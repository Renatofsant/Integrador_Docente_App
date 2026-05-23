from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import base64

# Nova URL raiz que faz o redirecionamento correto para o Portal unificado da SIT
URL_PORTAL = "https://docenteonline.educacao.rj.gov.br/"


class MotorSEEDUC:
    def __init__(self, usuario, escola_id):
        self.usuario = usuario
        self.escola_id = escola_id
        self.driver = None

    def iniciar_navegador(self):
        """Inicia o Chrome preparado para o teste visual local no novo portal"""
        opt = Options()
        # --- MODO VISUAL PARA TESTE LOCAL ---
        # Garantimos que as linhas headless estão comentadas para o Chrome abrir no seu ecrã
        opt.add_argument("--start-maximized")
        opt.add_argument("--no-sandbox")
        opt.add_argument("--disable-dev-shm-usage")
        opt.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opt)
        self.driver.get(URL_PORTAL)

        # Tempo para o redirecionamento da SIT carregar completamente
        time.sleep(4)

    def capturar_captcha_base64(self):
        """Localiza o Captcha na nova página da SIT com espera e envia em Base64"""
        print("[ROBÔ] A aguardar o carregamento do Captcha...")
        for _ in range(5):
            try:
                elemento_captcha = self.driver.find_element(By.ID, "captcha_image")
                captcha_bytes = elemento_captcha.screenshot_as_png
                return base64.b64encode(captcha_bytes).decode('utf-8')
            except Exception:
                time.sleep(1)

        # Fallback se o ID falhar
        try:
            elemento_captcha = self.driver.find_element(By.CSS_SELECTOR, "img[src*='captcha']")
            captcha_bytes = elemento_captcha.screenshot_as_png
            return base64.b64encode(captcha_bytes).decode('utf-8')
        except Exception as e_alt:
            print(f"Erro crítico: Captcha não mapeado: {e_alt}")
            return None

    def injetar_login_e_captcha(self, login_seeduc, senha_seeduc, texto_captcha):
        """Injeta as credenciais nos novos campos da tela de autenticação unificada"""
        try:
            campo_user = self.driver.find_element(By.NAME, "username")
            campo_pass = self.driver.find_element(By.NAME, "password")
            campo_cap = self.driver.find_element(By.NAME, "captcha")
            btn_entrar = self.driver.find_element(By.NAME, "login")

            campo_user.clear()
            campo_user.send_keys(login_seeduc)
            campo_pass.clear()
            campo_pass.send_keys(senha_seeduc)
            campo_cap.clear()
            campo_cap.send_keys(texto_captcha)

            btn_entrar.click()
            time.sleep(4)

            # Validação inteligente de sucesso baseada na mudança de endereço
            if "autenticacao.educacao.rj.gov.br" not in self.driver.current_url:
                return {"status": "sucesso", "msg": "Logado com sucesso!"}
            else:
                return {"status": "erro", "msg": "Falha na autenticação. Verifique os dados ou o Captcha digitado."}

        except Exception as e:
            return {"status": "erro", "msg": f"Erro ao localizar campos na nova interface: {str(e)}"}

    def preencher_cabecalho_pauta(self, turma_alvo, aulas_previstas, aulas_dadas, confirmar_checkbox):
        """Executa cliques para navegar, selecionar a turma e preencher dados de aula"""
        try:
            # 1. Clicar no menu lateral "Lançamento de Notas"
            menu_notas = self.driver.find_element(By.LINK_TEXT, "Lançamento de Notas")
            menu_notas.click()
            time.sleep(2.5)

            # 2. Selecionar a Turma passada pelo telemóvel no dropdown
            campo_turma = self.driver.find_element(By.XPATH, f"//option[contains(text(), '{turma_alvo}')]")
            campo_turma.click()
            time.sleep(2.5)

            # 3. Digitar a quantidade de aulas previstas e dadas mapeados pelo nome parcial do elemento
            campo_previstas = self.driver.find_element(By.CSS_SELECTOR, "input[name*='AulasPrevistas']")
            campo_dadas = self.driver.find_element(By.CSS_SELECTOR, "input[name*='AulasDadas']")

            campo_previstas.clear()
            campo_previstas.send_keys(str(aulas_previstas))
            campo_dadas.clear()
            campo_dadas.send_keys(str(aulas_dadas))

            # 4. Se o professor autorizou no telemóvel, marca o Checkbox/Botão Gravar do portal
            if confirmar_checkbox:
                btn_gravar_cabecalho = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Gravar') or contains(@value, 'Gravar')]"
                )
                btn_gravar_cabecalho.click()
                time.sleep(2)

            print(f"[OK] Cabeçalho da pauta preenchido para a turma {turma_alvo}.")

        except Exception as e:
            print(f"Erro ao preencher parâmetros da pauta no portal: {e}")
            raise e

    def lancar_notas_turma(self, lista_alunos):
        """
        Executa a injeção em lote das notas recebidas diretamente do Render
        na pauta do portal via Selenium.
        """
        try:
            print(f"[ROBÔ] Iniciando o lançamento de {len(lista_alunos)} alunos extraídos do Render...")

            # 1. Executa o script JS original para varrer e capturar quem está matriculado na tela
            script_extracao = "let r=[]; document.querySelectorAll('tr').forEach(tr=>{let d=tr.querySelectorAll('td'); if(d.length>=2){let n=d[0].innerText.trim(); let s=d[1]?d[1].innerText.trim():''; if(n.length>5 && !n.includes('Aulas')) r.push({n:n, s:(s==='Matriculado'||s==='')?'Ativo':'Inativo'});}}); return r;"
            alunos_portal = self.driver.execute_script(script_extracao)

            if not alunos_portal:
                print("[ROBÔ] [AVISO] Nenhum aluno lido na pauta do portal.")
                return {"status": "aviso", "msg": "Nenhum aluno lido na pauta do portal."}

            # 2. Indexa a lista do Render em um dicionário para busca instantânea em memória O(1)
            dados_render_dict = {aluno["nome"].strip().upper(): aluno for aluno in lista_alunos}

            # 3. Varre os alunos identificados na página do portal
            for aluno_tela in alunos_portal:
                nome_tela = aluno_tela['n'].strip().upper()
                status_tela = aluno_tela['s']

                # Se o aluno exibido em tela constar nas notas ativas do Render e estiver Ativo
                if nome_tela in dados_render_dict and status_tela == "Ativo":
                    info_aluno = dados_render_dict[nome_tela]

                    nota_real = info_aluno["nota"]
                    faltas_reais = info_aluno["faltas"]

                    print(f"[ROBÔ] Digitando -> {nome_tela} | Nota: {nota_real} | Faltas: {faltas_reais}")

                    # 4. Isola a linha do aluno usando o XPath estruturado
                    xpath_linha = f"//tr[td[contains(text(), '{aluno_tela['n']}')]]"
                    linha = self.driver.find_element(By.開X, xpath_linha if hasattr(By, '開X') else By.XPATH,
                                                     xpath_linha)

                    campo_n = linha.find_element(By.CSS_SELECTOR, "input[name*='.NotaProva']")
                    campo_f = Finder_f = linha.find_element(By.CSS_SELECTOR, "input[name*='.Faltas']")

                    # Rolagem via JS para garantir foco visual perfeito no elemento centrado
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo_n)
                    time.sleep(0.1)

                    # Preenche o campo de nota trocando o ponto decimal por vírgula
                    campo_n.click()
                    campo_n.clear()
                    campo_n.send_keys(str(round(nota_real, 1)).replace('.', ','))

                    # 5. Lógica condicional de recuperação se a média final for inferior a 5.0
                    if nota_real < 5.0:
                        self.driver.execute_script("""
                            let linha = arguments[0];
                            let cb = linha.querySelector("input[type='checkbox'][name*='.PossuiRecuperacao']");
                            if (cb && !cb.checked) { cb.click(); }
                        """, linha)
                        time.sleep(1.2)

                        campo_rec = linha.find_element(By.CSS_SELECTOR, "input.inputnotarecuperacao")
                        self.driver.execute_script("arguments[0].value = arguments[1];", campo_rec,
                                                   str(round(nota_real, 1)).replace('.', ','))

                    # Preenche as faltas mapeadas
                    campo_f.click()
                    campo_f.clear()
                    campo_f.send_keys(str(int(faltas_reais)))
                    time.sleep(0.1)

            print("[ROBÔ] Injeção de dados executada com sucesso em todas as correspondências.")
            return {"status": "sucesso", "msg": "Notas injetadas com sucesso!"}

        except Exception as e:
            print(f"[ROBÔ] [ERRO CRÍTICO NO LANÇAMENTO]: {str(e)}")
            return {"status": "erro", "msg": f"Erro no lançamento: {str(e)}"}

    def fechar(self):
        if self.driver:
            self.driver.quit()