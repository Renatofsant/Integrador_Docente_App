from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field # Usando o módulo v2 nativo e seguro
from motor_seeduc import MotorSEEDUC
import uuid
import psycopg2

app = FastAPI(title="API Integrador Docente SEEDUC")

# URL do seu banco no Render (Oregon)
URL_RENDER = "postgresql://renato_admin:irFGr5xMmqjd18NyQCJOD1m9lapIC0Wr@dpg-d870b9ojo89c73d31dfg-a.oregon-postgres.render.com/integrador_docente_mobile"

# Dicionário em memória para manter as sessões dos robôs ativas
sessoes_ativas = {}

# --- MODELOS DE DADOS ATUALIZADOS (SINTAXE PYDANTIC V2) ---
class ConectarRequest(BaseModel):
    usuario_sgi: str = Field(..., min_length=1)
    escola_id: int

class LoginRequest(BaseModel):
    session_id: str
    login_seeduc: str
    senha_seeduc: str
    captcha_texto: str

class LancamentoRequest(BaseModel):
    session_id: str
    turma: str
    trimestre: int
    aulas_previstas: int
    aulas_dadas: int
    confirmar_checkbox: bool

# --- ROTAS DA API ---

@app.post("/conectar")
def conectar_portal(req: ConectarRequest):
    try:
        session_id = str(uuid.uuid4())
        robo = MotorSEEDUC(usuario=str(req.usuario_sgi), school_id=int(req.escola_id))
        robo.iniciar_navegador()

        captcha_b64 = robo.capturar_captcha_base64()
        if not captcha_b64:
            captcha_b64 = ""

        sessoes_ativas[session_id] = robo
        return {"session_id": session_id, "captcha_image": captcha_b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def eateries_login(req: LoginRequest):
    if req.session_id not in sessoes_ativas:
        raise HTTPException(status_code=400, detail="Sessão expirada ou inválida.")

    robo = sessoes_ativas[req.session_id]
    resultado = robo.injetar_login_e_captcha(req.login_seeduc, req.senha_seeduc, req.captcha_texto)

    if resultado["status"] == "erro":
        robo.fechar()
        del sessoes_ativas[req.session_id]
        raise HTTPException(status_code=400, detail=resultado["msg"])

    return {"status": "sucesso", "msg": "Logado e aguardando parâmetros da pauta."}

@app.post("/lancar")
def iniciar_lancamento(req: LancamentoRequest, background_tasks: BackgroundTasks):
    if req.session_id not in sessoes_ativas:
        raise HTTPException(status_code=400, detail="Sessão inválida.")

    try:
        conn = psycopg2.connect(URL_RENDER)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.nome_completo, n.media_final, n.faltas
            FROM alunos a
            JOIN notas_bimestre n ON a.id = n.aluno_id
            WHERE a.turma = %s 
              AND a.status = 'Ativo' 
              AND n.trimestre = %s
            ORDER BY a.nome_completo;
        """, (req.turma, req.trimestre))

        linhas = cursor.fetchall()
        cursor.close()
        conn.close()

        if not list(linhas):
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum aluno ativo encontrado para a Turma {req.turma} no {req.trimestre}º Trimestre."
            )

        lista_alunos = [
            {"nome": str(l[0]), "nota": float(l[1]), "faltas": int(l[2])}
            for l in linhas
        ]

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco no Render: {str(e)}")

    robo = sessoes_ativas[req.session_id]

    background_tasks.add_task(
        executar_fluxo_completo,
        robo, req.session_id, req.turma, req.aulas_previstas, req.aulas_dadas, req.confirmar_checkbox, lista_alunos
    )

    return {"status": "processando", "msg": f"O robô iniciou o lançamento de {len(lista_alunos)} alunos."}

def executar_fluxo_completo(robo, session_id, turma, previstas, dadas, checkbox, lista_alunos):
    try:
        robo.preencher_cabecalho_pauta(turma, previstas, dadas, checkbox)
        robo.lancar_notas_turma(lista_alunos)
    except Exception as e:
        print(f"[ERRO NO FLUXO DO ROBÔ]: {e}")
    finally:
        robo.fechar()
        if session_id in sessoes_ativas:
            del sessoes_ativas[session_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
