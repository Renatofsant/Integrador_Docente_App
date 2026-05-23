import psycopg2
from psycopg2.extras import execute_values

# ⚙️ 1. Configuração do Banco de Origem (Docker Local)
DOCKER_CONFIG = {
    "host": "localhost",
    "port": 5438,
    "user": "postgres",
    "password": "admin123",
    "dbname": "seeduc_db"
}

# ⚙️ 2. Configuração do Banco de Destino (Render Nuvem)
# ⚠️ Substitua com a sua "External Database URL" do Render
URL_RENDER = "postgresql://renato_admin:irFGr5xMmqjd18NyQCJOD1m9lapIC0Wr@dpg-d870b9ojo89c73d31dfg-a.oregon-postgres.render.com/integrador_docente_mobile"


def migrar_sgi_para_render():
    conn_docker = None
    conn_render = None

    try:
        print("[MIGRAÇÃO] Iniciando conexão com os bancos de dados...")
        conn_docker = psycopg2.connect(**DOCKER_CONFIG)
        conn_render = psycopg2.connect(URL_RENDER)

        cursor_docker = conn_docker.cursor()
        cursor_render = conn_render.cursor()

        # --- PASSO 1: CRIAR AS TABELAS NO RENDER ---
        print("[RENDER] Criando estruturas das tabelas se não existirem...")

        cursor_render.execute("""
            CREATE TABLE IF NOT EXISTS escolas (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255),
                vinculo_login VARCHAR(100)
            );

            CREATE TABLE IF NOT EXISTS alunos (
                id SERIAL PRIMARY KEY,
                escola_id INT,
                nome_completo VARCHAR(255),
                matricula VARCHAR(100),
                turma VARCHAR(50),
                status VARCHAR(50)
            );

            CREATE TABLE IF NOT EXISTS notas_bimestre (
                id SERIAL PRIMARY KEY,
                aluno_id INT,
                bimestre INT,
                av1 NUMERIC(4,2),
                av2 NUMERIC(4,2),
                av3 NUMERIC(4,2),
                faltas INT,
                enviado_portal BOOLEAN,
                data_atualizacao TIMESTAMP,
                media_final NUMERIC(4,2),
                trimestre INT,
                recuperacao NUMERIC(4,2)
            );
        """)

        # Limpa dados anteriores no Render para evitar duplicações de teste
        cursor_render.execute("TRUNCATE TABLE notas_bimestre, alunos, escolas RESTART IDENTITY;")
        conn_render.commit()

        # --- PASSO 2: MIGRAR TABELA ESCOLAS ---
        print("[MIGRAÇÃO] Copiando dados da tabela 'escolas'...")
        cursor_docker.execute("SELECT id, nome, vinculo_login FROM escolas;")
        dados_escolas = cursor_docker.fetchall()
        if dados_escolas:
            execute_values(cursor_render, """
                INSERT INTO escolas (id, nome, vinculo_login) VALUES %s;
            """, dados_escolas)

        # --- PASSO 3: MIGRAR TABELA ALUNOS ---
        print("[MIGRAÇÃO] Copiando dados da tabela 'alunos'...")
        cursor_docker.execute("SELECT id, escola_id, nome_completo, matricula, turma, status FROM alunos;")
        dados_alunos = cursor_docker.fetchall()
        if dados_alunos:
            execute_values(cursor_render, """
                INSERT INTO alunos (id, escola_id, nome_completo, matricula, turma, status) VALUES %s;
            """, dados_alunos)

        # --- PASSO 4: MIGRAR TABELA NOTAS_BIMESTRE ---
        print("[MIGRAÇÃO] Copiando dados da tabela 'notas_bimestre'...")
        cursor_docker.execute("""
            SELECT id, aluno_id, bimestre, av1, av2, av3, faltas, enviado_portal, 
                   data_atualizacao, media_final, trimestre, recuperacao 
            FROM notas_bimestre;
        """)
        dados_notas = cursor_docker.fetchall()
        if dados_notas:
            execute_values(cursor_render, """
                INSERT INTO notas_bimestre (id, aluno_id, bimestre, av1, av2, av3, faltas, 
                                           enviado_portal, data_atualizacao, media_final, trimestre, recuperacao) 
                VALUES %s;
            """, dados_notas)

        # Confirma todas as gravações no Render
        conn_render.commit()
        print("\n🚀 [SUCESSO BALÍSTICO] Migração concluída com êxito!")
        print(
            f"Total copiado: {len(dados_escolas)} escolas, {len(dados_alunos)} alunos, {len(dados_notas)} registros de notas.")

    except Exception as e:
        print(f"\n❌ [ERRO CRÍTICO] Falha durante a migração: {e}")
        if conn_render:
            conn_render.rollback()

    finally:
        if conn_docker:
            conn_docker.close()
        if conn_render:
            conn_render.close()


if __name__ == "__main__":
    migrar_sgi_para_render()