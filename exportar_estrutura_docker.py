import psycopg2
import json

# ⚙️ Credenciais do seu PostgreSQL no Docker (Porta 5438 e senha fornecidas por você)
DB_CONFIG = {
    "host": "localhost",
    "port": 5438,
    "user": "postgres",
    "password": "admin123",
    "dbname": "seeduc_db"
}


def extrair_dados_para_analise():
    try:
        print("[DOCKER] A conectar ao banco local no Docker...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        relatorio = {
            "tabelas_encontradas": {},
            "amostra_dados": {}
        }

        # CORREÇÃO 1: Nomes das tabelas reais encontrados no seu DBeaver
        tabelas_alvo = ["alunos", "escolas", "notas_bimestre"]

        for tabela in tabelas_alvo:
            print(f"[DOCKER] A analisar estrutura da tabela: {tabela}...")

            # 1. Captura a estrutura das colunas (nomes e tipos de dados)
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{tabela}' AND table_schema = 'public';
            """)
            colunas = cursor.fetchall()
            relatorio["tabelas_encontradas"][tabela] = {col: tipo for col, tipo in colunas}

            # 2. Captura uma amostra segura (apenas as 3 primeiras linhas)
            try:
                cursor.execute(f"SELECT * FROM {tabela} LIMIT 3;")
                linhas = cursor.fetchall()
                nomes_colunas = [desc[0] for desc in cursor.description]

                amostras = []
                for linha in linhas:
                    # Converte valores que não são strings/números simples para texto para evitar erro de JSON
                    amostras.append({nomes_colunas[i]: str(linha[i]) for i in range(len(linha))})

                # CORREÇÃO 2: Salvando diretamente na lista sem a linha com erro de "samples"
                relatorio["amostra_dados"][tabela] = amostras

            except Exception as e_tab:
                print(f"[AVISO] Não foi possível ler dados da tabela {tabela}: {e_tab}")

        # Salva o relatório estruturado em um arquivo de texto
        with open("estrutura_sgi.txt", "w", encoding="utf-8") as f:
            json.dump(relatorio, f, indent=4, ensure_ascii=False)

        print("\n[SUCESSO] Arquivo 'estrutura_sgi.txt' gerado com sucesso!")
        print("Agora abra esse TXT, copie o conteúdo e cole aqui para eu analisar.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERRO] Falha ao conectar ou extrair do Docker: {e}")


if __name__ == "__main__":
    extrair_dados_para_analise()