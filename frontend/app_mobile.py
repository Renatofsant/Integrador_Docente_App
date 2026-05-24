import flet as ft
import requests

# URL raiz do seu backend FastAPI hospedado no Render
API_URL = "https://integrador-docente-app.onrender.com"

# URL pública direta do seu robô PNG para carregamento universal no celular
URL_ROBO = "https://assets.zyrosite.com/A85219vlv1fpqWDW/6-QW0AIgV87xDYSCXR.png"


def main(page: ft.Page):
    page.title = "Integrador Docente Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = ft.Padding(top=50, left=20, right=20, bottom=20)

    # Alinhamento nativo e seguro para dispositivos móveis
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    # Dicionário de estado interno controlado
    estado = {
        "session_id": None,
        "usuario_sgi": "",
        "escola_id": 1  # Fixado em 1 (Escola Agripino) para os testes da Turma 1003
    }

    # --- COMPONENTES DE INTERFACE ---
    txt_user_sgi = ft.TextField(label="Usuário SGI (Login SEEDUC)", width=320, border_color="#3b82f6",
                                value="renato_admin")
    lbl_status = ft.Text(value="Pronto para iniciar o integrador.", color="gray400", size=14,
                         text_align=ft.TextAlign.CENTER)

    # Parâmetros da Pauta (Tela 2)
    txt_turma = ft.TextField(label="Número da Turma", value="1003", width=320, border_color="#3b82f6")
    txt_trimestre = ft.Dropdown(
        label="Trimestre",
        width=320,
        options=[ft.dropdown.Option("1"), ft.dropdown.Option("2"), ft.dropdown.Option("3")],
        value="1"
    )
    txt_previstas = ft.TextField(label="Aulas Previstas", value="20", width=150, border_color="#3b82f6")
    txt_dadas = ft.TextField(label="Aulas Dadas", value="20", width=150, border_color="#3b82f6")
    chk_confirmar = ft.Checkbox(label="Autorizar Gravação Automática", value=True)

    # Instanciando os componentes de imagem com a URL do seu robô real
    img_robo_login = ft.Image(src=URL_ROBO, width=70, height=70, fit="contain")
    img_robo_lancar = ft.Image(src=URL_ROBO, width=70, height=70, fit="contain")

    # --- LÓGICA DE EVENTOS ---

    def disparar_abertura_portal(e):
        """Passo 1: Comanda o FastAPI a abrir o navegador visível e joga o usuário para o site"""
        if not txt_user_sgi.value:
            lbl_status.value = "⚠️ Por favor, insira o seu usuário SGI."
            lbl_status.color = "red400"
            page.update()
            return

        lbl_status.value = "🚀 Acordando o robô e abrindo o portal..."
        lbl_status.color = "blue400"
        page.update()

        try:
            res = requests.post(f"{API_URL}/conectar", json={
                "usuario_sgi": txt_user_sgi.value.strip(),
                "escola_id": estado["escola_id"]
            })

            if res.status_code == 200:
                dados = res.json()
                estado["session_id"] = dados["session_id"]
                estado["usuario_sgi"] = txt_user_sgi.value.strip()

                lbl_status.value = "✅ Navegador aberto! Faça o login no celular e clique no botão '2. Lançar' no topo."
                lbl_status.color = "green400"

                # Abre o portal de forma nativa no navegador do celular como tela de apoio
                page.launch_url("https://docenteonline.educacao.rj.gov.br/")
            else:
                lbl_status.value = f"❌ Erro no motor: {res.json().get('detail')}"
                lbl_status.color = "red400"
        except Exception as err:
            lbl_status.value = "❌ Falha de conexão. O backend no Render está ativo?"
            lbl_status.color = "red400"
        page.update()

    def iniciar_injecao_notas(e):
        """Passo 2: O usuário já está na pauta, o celular ordena o disparo baseado no Render"""
        if not estado["session_id"]:
            lbl_status.value = "⚠️ Primeiramente, execute a conexão na Tela de 'Autenticação'."
            lbl_status.color = "red400"
            page.update()
            return

        if not txt_turma.value:
            lbl_status.value = "⚠️ Informe a turma alvo (Ex: 1003)."
            lbl_status.color = "red400"
            page.update()
            return

        lbl_status.value = f"📡 Puxando notas da 1003 no Render e injetando..."
        lbl_status.color = "purple400"
        page.update()

        try:
            res = requests.post(f"{API_URL}/lancar", json={
                "session_id": estado["session_id"],
                "turma": txt_turma.value.strip(),
                "trimestre": int(txt_trimestre.value),
                "aulas_previstas": int(txt_previstas.value),
                "aulas_dadas": int(txt_dadas.value),
                "confirmar_checkbox": chk_confirmar.value
            })

            if res.status_code == 200:
                lbl_status.value = "🚀 Robô em Ação! Acompanhe o preenchimento automático das notas."
                lbl_status.color = "green400"
            else:
                lbl_status.value = f"❌ Erro no lançamento: {res.json().get('detail')}"
                lbl_status.color = "red400"
        except Exception as err:
            lbl_status.value = f"❌ Falha ao enviar comando: {err}"
            lbl_status.color = "red400"
        page.update()

    # --- RENDERIZADORES DE INTERFACE ---

    # Conteúdo da Tela 1: Autenticação Inicial
    aba_login = ft.Column([
        ft.Container(height=10),
        # Linha do cabeçalho com o seu robô oficial centralizado e alinhado perfeitamente
        ft.Row([
            img_robo_login,
            ft.Text("Integrador Docente", size=22, weight=ft.FontWeight.BOLD, color="#3b82f6")
        ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        ft.Text("Módulo Lançador Mobile", size=14, color="gray400"),
        ft.Container(height=20),
        txt_user_sgi,
        ft.Container(height=15),
        ft.ElevatedButton(
            "CONECTAR E ABRIR PORTAL",
            on_click=disparar_abertura_portal,
            width=320,
            height=55,
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: "white"},
                bgcolor={ft.ControlState.DEFAULT: "#3b82f6"},
                shape=ft.RoundedRectangleBorder(radius=8)
            )
        ),
        ft.Container(height=20),
        ft.Container(
            content=lbl_status,
            padding=15,
            border=ft.Border.all(1, "#3b82f6"),
            border_radius=8,
            width=320,
            bgcolor="#1e1e2e"
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # Conteúdo da Tela 2: Configuração e Lançamento
    aba_lancamento = ft.Column([
        ft.Container(height=10),
        # Cabeçalho da pauta também estilizado com o seu robô
        ft.Row([
            img_robo_lancar,
            ft.Text("INJEÇÃO EM LOTE", size=22, weight=ft.FontWeight.BOLD, color="#10b981")
        ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        ft.Text("Configure os parâmetros da pauta aberta:", size=13, color="gray400"),
        ft.Container(height=15),
        txt_turma,
        txt_trimestre,
        ft.Row([txt_previstas, txt_dadas], alignment=ft.MainAxisAlignment.CENTER, width=320),
        ft.Container(content=chk_confirmar, width=320, padding=5),
        ft.Container(height=15),
        ft.ElevatedButton(
            "INICIAR AUTOMAÇÃO DE NOTAS",
            on_click=iniciar_injecao_notas,
            bgcolor="#8b5cf6",
            color="white",
            width=320,
            height=55,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # Componente dinâmico principal que gerencia o que está na tela
    conteudo_dinamico = ft.Container(content=aba_login, expand=True)

    # Funções de alternância de tela disparadas pelos botões superiores
    def mostrar_tela_login(e):
        btn_nav_login.bgcolor = "#3b82f6"
        btn_nav_lancar.bgcolor = "#2d2d3d"
        conteudo_dinamico.content = aba_login
        page.update()

    def mostrar_tela_lancar(e):
        btn_nav_login.bgcolor = "#2d2d3d"
        btn_nav_lancar.bgcolor = "#10b981"
        conteudo_dinamico.content = aba_lancamento
        page.update()

    # Botões de Navegação customizados
    btn_nav_login = ft.ElevatedButton("1. Conexão", on_click=mostrar_tela_login, bgcolor="#3b82f6", color="white", width=150, height=40)
    btn_nav_lancar = ft.ElevatedButton("2. Lançar", on_click=mostrar_tela_lancar, bgcolor="#2d2d3d", color="white", width=150, height=40)

    # Layout de topo contendo os botões de controle
    menu_superior = ft.Row([btn_nav_login, btn_nav_lancar], alignment=ft.MainAxisAlignment.CENTER, width=320)

    # Adiciona a estrutura limpa direto na página sem Columns ou Tabs instáveis
    page.add(
        menu_superior,
        ft.Divider(height=15, color="transparent"),
        conteudo_dinamico
    )
    page.update()


if __name__ == "__main__":
    # Como o src agora é um link HTTP real da internet, removemos o assets_dir para evitar conflitos de cache local
    ft.app(target=main)
