from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from motor_seeduc import MotorSEEDUC
import uuid
import psycopg2

app = FastAPI(title="API Integrador Docente SEEDUC")

# URL do seu banco no Render (Oregon)
URL_RENDER = "postgresql://renato_admin:irFGr5xMmqjd18NyQCJOD1m9lapIC0Wr@dpg-d870b9ojo89c73d31dfg-a.oregon-postgres.render.com/integrador_docente_mobile"

# Dicionário em memória para manter as sessões dos robôs ativas enquanto o professor interage
sessoes_ativas = {}


# --- MODELOS DE DADOS (JSON) ---
class ConectarRequest(BaseModel):
    usuario_sgi: str
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
    """Passo 1: Inicia o Chrome na nuvem e captura o Captcha para o celular"""
    try:
        session_id = str(uuid.uuid4())
        robo = MotorSEEDUC(usuario=req.usuario_sgi, escola_id=req.escola_id)
        robo.iniciar_navegador()

        captcha_b64 = robo.capturar_captcha_base64()

        if not captcha_b64:
            # Impedimos o robô de matar o Chrome se o Captcha falhar localmente
            # robo.fechar()
            print("[AVISO] Captcha não capturado instantaneamente, mas mantendo o Chrome aberto.")
            # Para não travar a transição de telas no teste, enviamos uma string vazia temporária
            captcha_b64 = ""

        sessoes_ativas[session_id] = robo
        return {"session_id": session_id, "captcha_image": captcha_b64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
def eateries_login(req: LoginRequest):
    """Passo 2: Recebe o captcha resolvido e navega até a tela de Lançamento de Notas"""
    if req.session_id not in sessoes_ativas:
        raise HTTPException(status_code=400, detail="Sessão expirada ou inválida.")

    robo = sessoes_ativas[req.session_id]

    # Tenta logar e ir para a tela de notas
    resultado = robo.injetar_login_e_captcha(req.login_seeduc, req.senha_seeduc, req.captcha_texto)

    if resultado["status"] == "erro":
        # Se falhou o captcha, fecha essa sessão para não travar memória
        robo.fechar()
        del sessoes_ativas[req.session_id]
        raise HTTPException(status_code=400, detail=resultado["msg"])

    return {"status": "sucesso", "msg": "Logado e aguardando parâmetros da pauta."}


@app.post("/lancar")
def iniciar_lancamento(req: LancamentoRequest, background_tasks: BackgroundTasks):
    """Passo 3: Recebe a turma, as aulas dadas/previstas e inicia o robô em segundo plano"""
    if req.session_id not in sessoes_ativas:
        raise HTTPException(status_code=400, detail="Sessão inválida.")

    # Busca as notas do Render IMEDIATAMENTE antes de iniciar a task em background
    try:
        print(f"[BACKEND] Conectando ao Render para buscar notas da Turma {req.turma}...")
        conn = psycopg2.connect(URL_RENDER)
        cursor = conn.cursor()

        # Query exata baseada na estrutura real do seu banco migrado!
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

        if not linhas:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum aluno ativo com notas encontrado para a Turma {req.turma} no {req.trimestre}º Trimestre."
            )

        # Converte para uma lista limpa de dicionários
        lista_alunos = [
            {"nome": l[0], "nota": float(l[1]), "faltas": int(l[2])}
            for l in linhas
        ]

        print(f"[BACKEND] Sucesso! {len(lista_alunos)} alunos localizados no Render para a injeção.")

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o banco no Render: {str(e)}")

    robo = sessoes_ativas[req.session_id]

    # Dispara a automação em segundo plano passando a lista de dados coletada
    background_tasks.add_task(
        executar_fluxo_completo,
        robo, req.session_id, req.turma, req.aulas_previstas, req.aulas_dadas, req.confirmar_checkbox, lista_alunos
    )

    return {"status": "processando",
            "msg": f"O robô iniciou o lançamento de {len(lista_alunos)} alunos. Acompanhe a janela do Chrome."}


# CORREÇÃO AQUI: Mudado de 'ejecutar' para 'executar' para casar com a chamada acima
def executar_fluxo_completo(robo, session_id, turma, previstas, dadas, checkbox, lista_alunos):
    """Executa a sequência interna do Selenium no portal da SEEDUC com os dados reais do Render"""
    try:
        # 1. Seleciona a turma, preenche as aulas dadas/previstas e clica no checkbox dentro do portal
        robo.preencher_cabecalho_pauta(turma, previstas, dadas, checkbox)

        # 2. Executa o bloco de loop injetando as notas extraídas diretamente do Render
        robo.lancar_notas_turma(lista_alunos)
    except Exception as e:
        print(f"[ERRO NO FLUXO DO ROBÔ]: {e}")
    finally:
        # Após concluir tudo, encerra o navegador e limpa a memória do servidor
        robo.fechar()
        if session_id in sessoes_ativas:
            del sessoes_ativas[session_id]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)