import streamlit as st
import psycopg2
import pandas as pd
from psycopg2 import extras
import time
from datetime import datetime, timedelta

# ==============================================================================
# 1. CONFIGURAÇÃO DE PÁGINA E METADADOS (PADRÃO PREMIUM)
# ==============================================================================
st.set_page_config(
    page_title="SGI Projetta - Renato Santos",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# URL de conexão oficial do seu banco de dados no Render
URL_RENDER = "postgresql://renato_admin:irFGr5xMmqjd18NyQCJOD1m9lapIC0Wr@dpg-d870b9ojo89c73d31dfg-a.oregon-postgres.render.com/integrador_docente_mobile"


# ==============================================================================
# 2. INFRAESTRUTURA DE CONEXÃO (BLINDAGEM DE BANCO)
# ==============================================================================
def conectar_banco():
    """
    Mantém a conexão persistente usando a URI do Render no session_state.
    """
    if "conn" not in st.session_state or st.session_state.conn is None or st.session_state.conn.closed != 0:
        try:
            st.session_state.conn = psycopg2.connect(URL_RENDER)
        except Exception as e:
            st.error(f"❌ Falha crítica na conexão Cloud Render: {e}")
            return None
    return st.session_state.conn


# ==============================================================================
# 3. IDENTIDADE VISUAL E CSS (ESTILO SAAS EXCLUSIVO - PROJETTA CARBON)
# ==============================================================================
st.markdown("""
    <style>
    /* Fundo Principal */
    .stApp {
        background: #0F172A;
    }

    /* --- AJUSTE FINO DE UX: CURSOR POINTER --- */
    div[data-baseweb="select"], 
    div[data-baseweb="select"] *, 
    div[role="button"], 
    div[role="button"] *,
    .stSelectbox div {
        cursor: pointer !important;
    }

    li[role="option"], 
    li[role="option"] * {
        cursor: pointer !important;
    }

    [data-testid="stTable"] div, 
    .stDataEditor div[role="gridcell"],
    .stDataEditor div[role="columnheader"] {
        cursor: pointer !important;
    }

    div[data-baseweb="select"]:hover {
        border-color: #3b82f6 !important;
        transition: all 0.2s ease-in-out;
    }

    /* 🎨 CONTAINER DO FORMULÁRIO DE LOGIN (CARBON THEME) */
    [data-testid="stForm"] {
        background-color: #1E293B !important;
        padding: 45px;
        border-radius: 25px;
        box-shadow: 0 20px 45px rgba(0,0,0,0.7);
        border: 2px solid #3b82f6 !important; /* Borda Iluminada Neon */
    }

    /* Estilização de Labels e Textos Internos do Form */
    [data-testid="stForm"] label p {
        color: #F8FAFC !important;
        font-weight: 700 !important;
        font-size: 16px;
    }

    /* Inputs Customizados */
    [data-testid="stForm"] input {
        color: #F8FAFC !important;
        background-color: #0F172A !important;
        border: 2px solid #475569 !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }

    [data-testid="stForm"] input:focus {
        border-color: #3b82f6 !important;
    }

    /* Títulos de Login */
    .login-title {
        color: #3b82f6;
        font-family: 'Urbanist', sans-serif;
        font-weight: 900;
        text-align: center;
        font-size: 36px;
        margin-bottom: 8px;
    }

    .login-subtitle {
        color: #94A3B8;
        text-align: center;
        font-size: 15px;
        margin-bottom: 25px;
        font-weight: 500;
    }

    .lgpd-text {
        color: #94A3B8;
        font-size: 13px;
        text-align: justify;
        margin-top: 15px;
        margin-bottom: 10px;
        line-height: 1.4;
    }

    /* Ajuste desenho do olho do password input */
    [data-testid="stForm"] input[type="password"] ~ button svg {
        width: 18px !important;
        height: 18px !important;
        fill: #94A3B8 !important;
    }

    /* BOTÃO DE LOGIN EXCLUSIVO */
    div.stFormSubmitButton button {
        width: 100% !important;
        border-radius: 12px !important;
        height: 3.8em !important;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 18px !important;
        border: none !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        opacity: 1 !important;
    }

    div.stFormSubmitButton button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.5) !important;
        background: linear-gradient(135deg, #1d4ed8 0%, #60a5fa 100%) !important;
        opacity: 1 !important;
    }

    /* TODOS OS OUTROS BOTÕES DO PAINEL */
    div[data-testid="stNotification"] ~ div button,
    .stButton > button:not([id*="login"]),
    .stDownloadButton > button {
        width: 100% !important;
        border-radius: 12px !important;
        height: 3.8em !important;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        opacity: 1 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
    }

    div[data-testid="stNotification"] ~ div button:hover,
    .stButton > button:not([id*="login"]):hover,
    .stDownloadButton > button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.5) !important;
        background: linear-gradient(135deg, #1d4ed8 0%, #60a5fa 100%) !important;
        opacity: 1 !important;
    }

    .stButton > button:active, .stDownloadButton > button:active,
    .stButton > button:focus, .stDownloadButton > button:focus {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
        color: white !important;
        opacity: 1 !important;
    }

    .main-title {
        color: #F8FAFC;
        font-weight: 800;
        font-size: 2.5rem;
        border-left: 8px solid #3b82f6;
        padding-left: 20px;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# 4. SISTEMA DE AUTENTICAÇÃO (CONTROLE DE ACESSO)
# ==============================================================================
def realizar_login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.write("<br><br>", unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("<div class='login-title'>📊 Integrador Docente</div>", unsafe_allow_html=True)
            st.markdown("<div class='login-subtitle'>Portal Oficial de Lançamento • Renato Santos</div>",
                        unsafe_allow_html=True)
            st.write("---")

            user = st.text_input("Usuário / Login")
            senha = st.text_input("Senha de Acesso", type="password")

            # 📄 TERMO DE CONSENTIMENTO LGPD RESTAURADO
            st.markdown("""
                <div class='lgpd-text'>
                    Ao acessar, você declara estar ciente e concordar com os <b>Termos de Uso</b> e 
                    <b>Política de Privacidade (LGPD)</b> do Integrador Docente SaaS, autorizando o processamento 
                    de notas pedagógicas e dados institucionais sincronizados para fins operacionais.
                </div>
            """, unsafe_allow_html=True)

            st.write("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Acessar Painel Integrador")

            if submit:
                conn = conectar_banco()
                if conn:
                    query = "SELECT nome_professor, username, ativo FROM usuarios_integrador WHERE username = %s AND senha = %s"
                    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
                    cursor.execute(query, (user, senha))
                    user_data = cursor.fetchone()
                    cursor.close()

                    if user_data:
                        if user_data['ativo']:
                            st.session_state.autenticado = True
                            st.session_state.user_nome = user_data['nome_professor'] if user_data['nome_professor'] else \
                            user_data['username']
                            st.session_state.username = user_data['username']
                            st.session_state.user_perfil = 'admin' if user_data['username'] in ['renato',
                                                                                                'admin'] else 'professor'
                            st.rerun()
                        else:
                            st.error("🚫 Sua conta está inativa. Entre em contato com o suporte.")
                    else:
                        st.error("❌ Usuário ou senha incorretos.")
        st.stop()
    return True


# ==============================================================================
# 5. FLUXO PRINCIPAL (APLICAÇÃO LOGADA)
# ==============================================================================
if realizar_login():
    st.markdown("""
        <style>
        h1, h2, h3, h4, label, p { color: #F1F5F9 !important; }
        </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR (NAVEGAÇÃO) ---
    st.sidebar.markdown(f"## 👤 {st.session_state.user_nome}")
    st.sidebar.write(f"Nível: **{st.session_state.user_perfil.capitalize()}**")
    st.sidebar.write("---")

    opcoes_menu = ["📊 Lançamento de Notas"]
    if st.session_state.user_perfil == 'admin':
        opcoes_menu.append("⚙️ Gestão Administrativa")

    escolha = st.sidebar.selectbox("O que deseja fazer?", opcoes_menu)

    st.sidebar.write("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🔴 Sair do Sistema"):
        st.session_state.autenticado = False
        st.rerun()

    conn = conectar_banco()

    if conn:
        MAPA_NOME_ESCOLAS = {
            1: "Escola 1 - Agripino",
            2: "Escola 2 - Nazareth",
            3: "Escola 3 - Pernambuco"
        }

        # ======================================================================
        # 6. MÓDULO: LANÇAMENTO DE NOTAS (ISOLADO POR PROFESSOR)
        # ======================================================================
        if escolha == "📊 Lançamento de Notas":
            try:
                st.markdown("<h1 class='main-title'>📊 Lançamento de Notas</h1>", unsafe_allow_html=True)

                if st.session_state.user_perfil == 'admin':
                    query_esc = "SELECT id, nome FROM escolas ORDER BY nome"
                else:
                    query_esc = f"""
                        SELECT DISTINCT e.id, e.nome 
                        FROM escolas e
                        JOIN escolas_professores ep ON e.id = ep.escola_id
                        JOIN usuarios_integrador u ON ep.professor_id = u.id
                        WHERE u.username = '{st.session_state.username}'
                        ORDER BY e.nome
                    """

                escolas_df = pd.read_sql(query_esc, conn)

                if escolas_df.empty and st.session_state.username in ['renato', 'admin'] or not escolas_df.empty:
                    if escolas_df.empty:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT DISTINCT escola_id FROM alunos WHERE escola_id IS NOT NULL ORDER BY escola_id;")
                        ids_banco = [l[0] for l in cursor.fetchall()]
                        cursor.close()
                        escolas_df = pd.DataFrame(
                            [{"id": i, "nome": MAPA_NOME_ESCOLAS.get(i, f"Escola Código {i}")} for i in ids_banco])

                if not escolas_df.empty:
                    escolas_df['nome_exibicao'] = escolas_df.apply(lambda r: MAPA_NOME_ESCOLAS.get(r['id'], r['nome']),
                                                                   axis=1)

                    c1, c2 = st.columns([2, 1])
                    with c1:
                        escola_exibida = st.selectbox("🏫 Escolha a Escola", escolas_df['nome_exibicao'])
                        id_escola = escolas_df.loc[escolas_df['nome_exibicao'] == school_id, 'id'].values[
                            0] if 'school_id' in locals() else \
                        escolas_df.loc[escolas_df['nome_exibicao'] == escola_exibida, 'id'].values[0]
                    with c2:
                        trimestre_selecionado = st.selectbox("📅 Trimestre Target", [1, 2, 3])

                    if st.session_state.user_perfil == 'admin':
                        query_turmas = f"SELECT DISTINCT turma FROM alunos WHERE escola_id = {id_escola} AND turma IS NOT NULL ORDER BY turma"
                    else:
                        query_turmas = f"""
                            SELECT DISTINCT turma FROM vinculo_professor_turma 
                            WHERE professor_username = '{st.session_state.username}' 
                            AND escola_id = {id_escola}
                            ORDER BY turma
                        """

                    turmas_df = pd.read_sql(query_turmas, conn)

                    if turmas_df.empty:
                        query_turmas = f"SELECT DISTINCT turma FROM alunos WHERE escola_id = {id_escola} AND turma IS NOT NULL ORDER BY turma"
                        turmas_df = pd.read_sql(query_turmas, conn)

                    if not turmas_df.empty:
                        turma_nome = st.selectbox("👥 Selecione a Turma", turmas_df['turma'])

                        query_dados = f"""
                            SELECT a.id, a.nome_completo as "Aluno", 
                                   COALESCE(n.av1, 0.0) as "AV1", 
                                   COALESCE(n.av2, 0.0) as "AV2", 
                                   COALESCE(n.av3, 0.0) as "AV3", 
                                   COALESCE(n.recuperacao, 0.0) as "RECUP",
                                   (COALESCE(n.av1, 0.0) + COALESCE(n.av2, 0.0) + COALESCE(n.av3, 0.0)) as "Somatório",
                                   COALESCE(n.faltas, 0) as "Faltas"
                            FROM alunos a
                            LEFT JOIN notas_bimestre n ON a.id = n.aluno_id AND n.trimestre = {trimestre_selecionado}
                            WHERE a.escola_id = {id_escola} AND a.turma = '{turma_nome}' AND a.status = 'Ativo'
                            ORDER BY a.nome_completo
                        """

                        df = pd.read_sql(query_dados, conn)
                        df = df[~df['Aluno'].str.contains("Aulas previstas|Matrícula", na=False)]

                        # --- MÉTRICAS DE PERFORMANCE DA TURMA TANQUE DE GUERRA ---
                        if not df.empty:
                            st.write("---")
                            total_a = len(df)
                            notas_l = df[df['AV1'] > 0].shape[0]
                            percentual = (notas_l / total_a) if total_a > 0 else 0

                            met1, met2, met3 = st.columns(3)
                            met1.metric("Total Alunos", total_a)
                            met2.metric("Notas Sincronizadas", notas_l, f"{notas_l - total_a} pendentes")
                            met3.metric("Média Geral", f"{df['Somatório'].mean():.1f} pts")

                            st.write(f"**Progresso do Lançamento: {percentual:.0%}**")
                            st.progress(percentual)
                            st.write("<br>", unsafe_allow_html=True)

                        # --- EDITOR DE DADOS (DATA EDITOR PREMIUM) ---
                        edited_df = st.data_editor(
                            df,
                            column_config={
                                "id": None,
                                "Aluno": st.column_config.TextColumn("Nome do Aluno", disabled=True, width="large"),
                                "AV1": st.column_config.NumberColumn("AV1", format="%.1f", min_value=0.0,
                                                                     max_value=10.0),
                                "AV2": st.column_config.NumberColumn("AV2", format="%.1f", min_value=0.0,
                                                                     max_value=10.0),
                                "AV3": st.column_config.NumberColumn("AV3", format="%.1f", min_value=0.0,
                                                                     max_value=10.0),
                                "RECUP": st.column_config.NumberColumn("🔄 REC", format="%.1f", min_value=0.0,
                                                                       max_value=10.0),
                                "Somatório": st.column_config.NumberColumn("Total", disabled=True, format="%.1f"),
                                "Faltas": st.column_config.NumberColumn("Faltas", step=1)
                            },
                            hide_index=True,
                            use_container_width=True,
                            key=f"ed_rnd_{id_escola}_{turma_nome}_{st.session_state.username}"
                        )

                        # --- LÓGICA DE SALVAMENTO DE ALTO IMPACTO (DELETE + INSERT) ---
                        st.write("---")
                        if st.button("💾 CONFIRMAR E SALVAR NO RENDER"):
                            cursor = conn.cursor()
                            try:
                                for _, row in edited_df.iterrows():
                                    somatorio = row['AV1'] + row['AV2'] + row['AV3']
                                    media_final = row['RECUP'] if row['RECUP'] > somatorio else somatorio

                                    # Limpa registros redundantes no banco do Render
                                    cursor.execute("""
                                        DELETE FROM notas_bimestre WHERE aluno_id = %s AND trimestre = %s;
                                    """, (int(row['id']), int(trimestre_selecionado)))

                                    # Insere de forma limpa na estrutura clonada
                                    cursor.execute("""
                                        INSERT INTO notas_bimestre (
                                            aluno_id, av1, av2, av3, recuperacao, 
                                            media_final, faltas, trimestre, professor_username, data_atualizacao
                                        )
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW());
                                    """, (
                                        int(row['id']), float(row['AV1']), float(row['AV2']), float(row['AV3']),
                                        float(row['RECUP']), float(media_final), int(row['Faltas']),
                                        int(trimestre_selecionado), str(st.session_state.username)
                                    ))
                                conn.commit()
                                st.success(f"✅ Sincronização da Turma {turma_nome} realizada no Render com sucesso!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar: {e}")
                                conn.rollback()
                            finally:
                                cursor.close()

                        # --- EXPORTAÇÃO E RELATÓRIOS ELEGANTES ---
                        st.write("---")
                        st.subheader("📄 Relatórios")
                        exp1, exp2 = st.columns(2)
                        with exp1:
                            csv_data = edited_df.to_csv(index=False).encode('utf-8')
                            st.download_button("📥 Baixar CSV", csv_data, f"SGI_{turma_nome}.csv", "text/csv")

                        with exp2:
                            linhas_alunos = ""
                            if not edited_df.empty:
                                for _, row in edited_df.iterrows():
                                    linhas_alunos += f"""
                                    <tr>
                                        <td>{row['Aluno']}</td>
                                        <td class="center">{row['AV1']:.1f}</td>
                                        <td class="center">{row['AV2']:.1f}</td>
                                        <td class="center">{row['AV3']:.1f}</td>
                                        <td class="center">{row['RECUP']:.1f}</td>
                                        <td class="center font-bold">{row['Somatório']:.1f}</td>
                                        <td class="center">{int(row['Faltas'])}</td>
                                    </tr>
                                    """
                            else:
                                linhas_alunos = "<tr><td colspan='7' class='center'>Nenhum aluno encontrado.</td></tr>"

                            html_cont = f"""<!DOCTYPE html>
                                    <html>
                                    <head>
                                        <meta charset="utf-8">
                                        <title>SGI - {escola_exibida}</title>
                                        <style>
                                            body {{ font-family: Arial, sans-serif; margin: 30px; color: #1E293B; }}
                                            h2 {{ color: #1E3A8A; border-bottom: 2px solid #3B82F6; padding-bottom: 8px; margin-bottom: 5px; }}
                                            h3 {{ color: #475569; margin-top: 5px; font-weight: 600; margin-bottom: 5px; }}
                                            h4 {{ color: #64748B; margin-top: 5px; font-weight: 500; margin-bottom: 25px; }}
                                            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                                            th, td {{ border: 1px solid #CBD5E1; padding: 10px; text-align: left; font-size: 14px; }}
                                            th {{ background-color: #F8FAFC; color: #334155; font-weight: bold; }}
                                            .center {{ text-align: center; }}
                                            .font-bold {{ font-weight: bold; }}
                                            p {{ color: #94A3B8; font-size: 12px; margin-top: 40px; border-top: 1px dashed #CBD5E1; padding-top: 10px; }}
                                        </style>
                                    </head>
                                    <body>
                                        <h2>🏫 {escola_exibida}</h2>
                                        <h3>👤 Professor(a): {st.session_state.user_nome}</h3>
                                        <h4>👥 Turma: {turma_nome} | Trimestre: {trimestre_selecionado}º</h4>
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>Nome do Aluno</th>
                                                    <th class="center">AV1</th>
                                                    <th class="center">AV2</th>
                                                    <th class="center">AV3</th>
                                                    <th class="center">REC</th>
                                                    <th class="center">Total</th>
                                                    <th class="center">Faltas</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {linhas_alunos}
                                            </tbody>
                                        </table>
                                        <p>Documento gerado digitalmente via Integrador Docente • Projetta.</p>
                                    </body>
                                    </html>"""

                            st.session_state['html_relatorio'] = html_cont
                            st.download_button(
                                label="🖨️ Relatório HTML",
                                data=st.session_state['html_relatorio'],
                                file_name=f"Relatorio_{turma_nome}.html",
                                mime="text/html",
                                key=f"btn_html_rnd_{turma_nome}"
                            )
                    else:
                        st.info(f"💡 Você ainda não possui turmas vinculadas na escola **{escola_exibida}**.")
                else:
                    st.warning("⚠️ Nenhuma instituição vinculada ao seu perfil de docente.")

            except Exception as e:
                st.error(f"Ocorreu um erro no módulo de notas: {e}")
                st.session_state.conn = None

        # ======================================================================
        # 7. MÓDULO: GESTÃO ADMINISTRATIVA (PAINEL GERAL NO RENDER)
        # ======================================================================
        elif escolha == "⚙️ Gestão Administrativa":
            st.markdown("<h1 class='main-title'>⚙️ Gestão Administrativa</h1>", unsafe_allow_html=True)

            abas = st.tabs(["🏫 Escolas", "👥 Alunos", "👤 Professores", "🔗 Vínculos", "💰 Financeiro", "🚀 Carga SEEDUC"])

            with abas[0]:
                st.subheader("Cadastro de Unidades")
                with st.form("form_esc"):
                    nome_n = st.text_input("Nome da Escola / Colégio")
                    if st.form_submit_button("Cadastrar Unidade"):
                        if nome_n:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO escolas (nome) VALUES (%s)", (nome_n,))
                            conn.commit()
                            st.success(f"Unidade '{nome_n}' inserida no Render.")
                        else:
                            st.warning("O nome não pode estar vazio.")

            with abas[1]:
                st.subheader("Manutenção de Alunos")
                with st.form("form_alu"):
                    escs_df = pd.read_sql("SELECT id, nome FROM escolas ORDER BY nome", conn)
                    if escs_df.empty:
                        escs_df = pd.DataFrame([{"id": k, "nome": v} for k, v in MAPA_NOME_ESCOLAS.items()])

                    s_esc = st.selectbox("Selecione a Escola", escs_df['nome'])
                    id_e = escs_df.loc[escs_df['nome'] == s_esc, 'id'].values[0]
                    n_a = st.text_input("Nome Completo do Aluno")
                    t_a = st.text_input("Turma (ex: 1001)")
                    if st.form_submit_button("Registrar Aluno"):
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO alunos (nome_completo, escola_id, turma, status) VALUES (%s,%s,%s,'Ativo')",
                            (n_a, int(id_e), t_a))
                        conn.commit()
                        st.success(f"Aluno {n_a} cadastrado com sucesso.")

            with abas[2]:
                st.subheader("👤 Central de Gerenciamento de Docentes")
                with st.expander("➕ Cadastrar Novo Professor", expanded=False):
                    with st.form("form_prof_unificado"):
                        u_log = st.text_input("Username (Login)")
                        p_log = st.text_input("Senha Inicial", type="password")
                        n_log = st.text_input("Nome Completo")
                        if st.form_submit_button("🚀 Criar Conta e Liberar Acesso"):
                            if u_log and p_log and n_log:
                                try:
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        "INSERT INTO usuarios_integrador (username, senha, nome_professor, ativo) VALUES (%s,%s,%s,TRUE)",
                                        (u_log.lower().strip(), p_log, n_log)
                                    )
                                    conn.commit()
                                    st.success(f"✅ Professor {n_log} cadastrado com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao cadastrar: {e}")
                            else:
                                st.warning("Preencha todos os campos.")

                st.write("---")
                st.subheader("👥 Professores Cadastrados")
                try:
                    query_prof = "SELECT id, username, nome_professor as nome, ativo, criado_em FROM usuarios_integrador ORDER BY criado_em DESC"
                    df_prof = pd.read_sql(query_prof, conn)

                    for index, row in df_prof.iterrows():
                        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
                        with c1:
                            st.info(f"🔑 {row['username']}")
                        with c2:
                            st.write(f"**{row['nome'] if row['nome'] else row['username']}**")
                        with c3:
                            st.write("🟢 Ativo" if row['ativo'] else "🔴 Bloqueado")
                        with c4:
                            label_btn = "Bloquear" if row['ativo'] else "Ativar"
                            if st.button(label_btn, key=f"gestao_{row['id']}"):
                                cursor = conn.cursor()
                                cursor.execute("UPDATE usuarios_integrador SET ativo = %s WHERE id = %s",
                                               (not row['ativo'], row['id']))
                                conn.commit()
                                st.rerun()
                except Exception as e:
                    st.error(f"Erro ao carregar lista: {e}")

            with abas[3]:
                st.subheader("Atribuição de Turmas e Vínculos")
                p_df = pd.read_sql(
                    "SELECT id, username, nome_professor as nome FROM usuarios_integrador WHERE ativo = TRUE", conn)
                e_df = pd.read_sql("SELECT id, nome FROM escolas ORDER BY nome", conn)
                if e_df.empty:
                    e_df = pd.DataFrame([{"id": k, "nome": v} for k, v in MAPA_NOME_ESCOLAS.items()])

                if not p_df.empty and not e_df.empty:
                    sel_p = st.selectbox("Escolha o Professor", p_df['username'],
                                         format_func=lambda x: p_df.loc[p_df['username'] == x, 'nome'].values[0] if
                                         p_df.loc[p_df['username'] == x, 'nome'].values[0] else x)
                    id_professor_selecionado = p_df.loc[p_df['username'] == sel_p, 'id'].values[0]

                    sel_e_n = st.selectbox("Unidade Escolar", e_df['nome'])
                    sel_e_id = e_df.loc[e_df['nome'] == sel_e_n, 'id'].values[0]
                    vinc_id = st.text_input("Vínculo SEEDUC (Matrícula ex: 1, 2, 3)")

                    # 🛡️ FIX DEFINTIVO: Mudado de 'school_id' para 'escola_id' para alinhar com o PostgreSQL do Render
                    t_disp = pd.read_sql(
                        f"SELECT DISTINCT turma FROM alunos WHERE escola_id = {sel_e_id} AND turma IS NOT NULL ORDER BY turma",
                        conn)
                    lista_turmas = t_disp['turma'].tolist() if not t_disp.empty else []

                    ts = st.multiselect("Selecione as Turmas deste Docente", lista_turmas)

                    if st.button("💾 Confirmar e Registrar Vínculos", key="btn_salvar_vinculo_adm"):
                        if vinc_id:
                            try:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    INSERT INTO escolas_professores (professor_id, escola_id)
                                    VALUES (%s, %s);
                                """, (int(id_professor_selecionado), int(sel_e_id)))

                                if ts:
                                    for t_item in ts:
                                        cursor.execute("""
                                            INSERT INTO vinculo_professor_turma (professor_username, escola_id, turma, vinculo_id)
                                            VALUES (%s, %s, %s, %s);
                                        """, (sel_p, int(sel_e_id), t_item, vinc_id))

                                conn.commit()
                                cursor.close()
                                st.success(f"🎉 Sucesso! Professor vinculado à escola '{sel_e_n}' com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao salvar relacionamento: {e}")
                                conn.rollback()
                        else:
                            st.error("❌ Informe o Vínculo (Matrícula) antes de salvar.")

            with abas[4]:
                st.subheader("💰 Gestão de Assinaturas e Recebimentos")

                try:
                    query_fin = "SELECT status_pagamento, valor_total, qtd_turmas FROM assinaturas"
                    df_fin = pd.read_sql(query_fin, conn)

                    if not df_fin.empty:
                        c_m1, c_m2, c_m3 = st.columns(3)
                        recebido = df_fin[df_fin['status_pagamento'] == 'pago']['valor_total'].sum()
                        pendente = df_fin[df_fin['status_pagamento'] == 'pendente']['valor_total'].sum()
                        c_m1.metric("Confirmado ✅", f"R$ {recebido:,.2f}")
                        c_m2.metric("Pendente ⏳", f"R$ {pendente:,.2f}")
                        c_m3.metric("Total Turmas", int(df_fin['qtd_turmas'].sum()))
                except:
                    st.warning("Tabela de assinaturas indisponível no momento.")

                st.write("---")
                with st.expander("➕ Registrar Nova Venda/Cobrança", expanded=False):
                    with st.form("form_nova_venda"):
                        profs_venda = pd.read_sql(
                            "SELECT username, nome_professor as nome FROM usuarios_integrador WHERE ativo = TRUE", conn)
                        if not profs_venda.empty:
                            sel_user = st.selectbox("Professor", profs_venda['username'],
                                                    format_func=lambda x:
                                                    profs_venda.loc[profs_venda['username'] == x, 'nome'].values[0] if
                                                    profs_venda.loc[profs_venda['username'] == x, 'nome'].values[
                                                        0] else x)
                            n_turmas = st.number_input("Quantidade de Turmas", min_value=1, step=1, value=1)

                            if st.form_submit_button("Gerar Cobrança"):
                                cursor = conn.cursor()
                                nome_prof_venda = profs_venda.loc[profs_venda['username'] == sel_user, 'nome'].values[0]
                                valor_venda = n_turmas * 10.0
                                cursor.execute("""
                                    INSERT INTO assinaturas (username_docente, nome_professor, qtd_turmas, valor_total, status_pagamento)
                                    VALUES (%s, %s, %s, %s, 'pendente')
                                """, (sel_user, nome_prof_venda, n_turmas, valor_venda))
                                conn.commit()
                                st.success("Cobrança gerada com sucesso!")
                                st.rerun()

                st.write("### 🚀 Pendências de Pagamento")
                try:
                    query_pendentes = "SELECT * FROM assinaturas WHERE status_pagamento = 'pendente' ORDER BY data_cadastro DESC"
                    df_p = pd.read_sql(query_pendentes, conn)

                    if df_p.empty:
                        st.info("Tudo em dia! Nenhum Pix pendente.")
                    else:
                        for _, row in df_p.iterrows():
                            col_a, col_b, col_c = st.columns([3, 1, 1])
                            col_a.write(f"**{row['nome_professor']}** ({row['qtd_turmas']} turmas)")
                            col_b.write(f"R$ {row['valor_total']:.2f}")
                            if col_c.button("Confirmar ✅", key=f"pay_{row['id']}"):
                                cursor = conn.cursor()
                                venc = (datetime.now() + timedelta(days=90)).date()
                                cursor.execute("""
                                    UPDATE assinaturas SET 
                                    status_pagamento = 'pago', 
                                    data_pagamento = %s, 
                                    data_vencimento = %s 
                                    WHERE id = %s
                                """, (datetime.now(), venc, row['id']))
                                conn.commit()
                                st.success("Pago!")
                                st.rerun()
                except:
                    pass

            with abas[5]:
                st.subheader("🚀 Integração Robótica SEEDUC")
                st.info("Este módulo dispara a extração automática diretamente do portal oficial para o Render.")
                with st.form("form_robo"):
                    st.text_input("Login/CPF SEEDUC")
                    st.text_input("Senha Portal", type="password")
                    st.selectbox("Escola Alvo para Carga",
                                 ["Escola 1 - Agripino", "Escola 2 - Nazareth", "Escola 3 - Pernambuco"])
                    if st.form_submit_button("🚀 INICIAR EXTRAÇÃO TANQUE DE GUERRA"):
                        st.warning("Comando de extração enviado para a fila do robô mobile.")
