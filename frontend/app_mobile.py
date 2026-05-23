import flet as ft
import requests

# URL raiz do seu backend FastAPI (mude para o link do Render quando subir o app.py para lá)
API_URL = "http://192.168.0.107:8000"


def main(page: ft.Page):
    page.title = "PROJETTA - SGI Mobile Integrador"
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

    # Parâmetros da Pauta (Aba 2)
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
            # Envia a requisição para a rota correta do app.py
            res = requests.post(f"{API_URL}/abrir_portal", json={
                "usuario_sgi": txt_user_sgi.value.strip(),
                "escola_id": estado["escola_id"]
            })

            if res.status_code == 200:
                dados = res.json()
                estado["session_id"] = dados["session_id"]
                estado["usuario_sgi"] = txt_user_sgi.value.strip()

                lbl_status.value = "✅ Navegador aberto! Faça o login no PC ou celular e mude para a aba 'Lançamento'."
                lbl_status.color = "green400"

                # Abre o portal de forma nativa no navegador do celular como tela de apoio
                page.launch_url("https://docenteonline.educacao.rj.gov.br/")
            else:
                lbl_status.value = f"❌ Erro no motor: {res.json().get('detail')}"
                lbl_status.color = "red400"
        except Exception as err:
            lbl_status.value = "❌ Falha de conexão. O app.py está rodando?"
            lbl_status.color = "red400"
        page.update()

    def iniciar_injecao_notas(e):
        """Passo 2: O usuário já está na pauta, o celular ordena o disparo baseado no Render"""
        if not estado["session_id"]:
            lbl_status.value = "⚠️ Primeiramente, execute a conexão na Aba 'Autenticação'."
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

    # --- RENDERIZADORES DE INTERFACE (ESTRUTURA TANQUE DE GUERRA) ---

    # Conteúdo da Aba 1: Autenticação Inicial
    aba_login = ft.Column([
        ft.Container(height=10),
        ft.Text("⚡ PROJETTA SGI", size=26, weight=ft.FontWeight.BOLD, color="#3b82f6"),
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
            border=ft.border.all(1, "#3b82f6"),
            border_radius=8,
            width=320,
            bgcolor="#1e1e2e"
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # Conteúdo da Aba 2: Configuração e Injeção
    aba_lancamento = ft.Column([
        ft.Container(height=10),
        ft.Text("🚀 INJEÇÃO EM LOTE", size=22, weight=ft.FontWeight.BOLD, color="#10b981"),
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

    # Organização das Abas Nativas (Blindadas contra quebras no Celular)
    tabs_sistema = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="1. Autenticação", icon=ft.icons.LOCK_OPEN, content=aba_login),
            ft.Tab(text="2. Lançamento", icon=ft.icons.AUTO_STORIES, content=aba_lancamento),
        ],
        expand=1
    )

    # Adiciona o contêiner mestre na tela
    page.add(tabs_sistema)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
