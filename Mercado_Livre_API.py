"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  MONITOR DE PREÇOS - MINIATURAS F1 1/43 McDONALD'S - MERCADO LIVRE          ║
║  Versão: 4.0 - Sistema Unificado com Auto-Login                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import time
import smtplib
from email.message import EmailMessage
import datetime
import os
import random
import re
import json
import logging
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin, urlparse

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import imaplib
import email as email_lib
from email.header import decode_header

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DE LOGGING (APENAS TERMINAL)
# ═══════════════════════════════════════════════════════════════════════════════

def configurar_logging():
    """Configura sistema de logging apenas para terminal"""
    
    logger = logging.getLogger("MLMonitor")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    # Formato com ícones
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname_icon)s %(message)s',
        datefmt='%H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Adicionar ícones
    class IconFilter(logging.Filter):
        ICONS = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️ ',
            'WARNING': '⚠️ ',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }
        
        def filter(self, record):
            record.levelname_icon = self.ICONS.get(record.levelname, '•')
            return True
    
    console_handler.addFilter(IconFilter())
    logger.addHandler(console_handler)
    
    return logger

logger = configurar_logging()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES GLOBAIS
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG = {
    # Credenciais (MOVA PARA VARIÁVEIS DE AMBIENTE EM PRODUÇÃO!)
    'email_ml': os.environ.get('EMAIL_APP_M'),
    'senha_app_ml': os.environ.get('SENHA_APP_M'),
    'email_destino': os.environ.get('EMAIL_APP_P'),
    'senha_app_destino': os.environ.get('SENHA_APP_P'),
    
    # URL específica para monitorar
    'url_base': 'https://lista.mercadolivre.com.br/mc-donalds-f1-1%2F43',
    
    # Debug
    'chrome_headless': False,  # True = invisível, False = visível
    'salvar_html_debug': True,  # Salvar HTML para análise
    'forcar_selenium': False,  # True = sempre usar Selenium (para testar)
    
    # Filtros de produtos
    'termos_obrigatorios': ["1/43", "1:43"],
    'termos_relevantes': ["f1", "formula 1", "mcdonald"],
    
    # Exclusões
    'exclusoes_titulo': ["hot wheels", "mclaren f1-mcl36"],
    'exclusoes_id': ["mlb-1929640090", "mlb22449590", "mlb5466709978"],
    
    # Parâmetros de busca
    'max_paginas': 5,
    'produtos_por_pagina': 50,
    'numero_itens_email': 5,
    
    # Categorização
    'padroes_preto': ["apxgp", "preto", "expensity", "cor apx", "modelo apxgp", "expensify"],
    'padroes_vermelho': ["vermelho", "automac", "app", "automaq", "maisto", "modelo vermelho"],
    'padroes_dupla': ["set 2un", "kit 2x", "kit c/2", "dupla", "2x miniatura", "kit com 2"],
    
    # Configurações de rede
    'timeout': 20,
    'delay_entre_paginas': (2, 4),
    'delay_entre_tentativas': 6,
    'max_tentativas': 4,
}

# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO DE AUTO-LOGIN (SELENIUM)
# ═══════════════════════════════════════════════════════════════════════════════

class AutoLogin:
    """Gerencia login automático no Mercado Livre"""
    
    def __init__(self, email: str, senha_app: str):
        self.email = email
        self.senha_app = senha_app
        self.driver = None
    
    def esperar_natural(self, min_seg=1, max_seg=3):
        """Delay natural"""
        time.sleep(random.uniform(min_seg, max_seg))
    
    def configurar_driver(self):
        """Configura driver Chrome anti-detecção"""
        logger.info("Configurando Chrome...")
        
        options = Options()
        
        # Detectar ambiente CI/CD
        is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
        
        if is_ci:
            logger.info("🤖 Ambiente CI/CD detectado - configurando headless")
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-extensions')
            options.add_argument('--window-size=1920,1080')
        elif CONFIG.get('chrome_headless', False):
            options.add_argument('--headless=new')
            logger.info("Modo headless ativado")
        else:
            logger.info("Modo visível ativado - você verá o navegador")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            driver = webdriver.Chrome(options=options)
            
            # Tentar executar script anti-detecção (pode falhar no CI)
            try:
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                logger.info("✅ Script anti-detecção aplicado")
            except Exception as e:
                logger.warning(f"⚠️ Script anti-detecção falhou (normal no CI): {str(e)[:100]}")
            
            self.driver = driver
            logger.info("✅ Chrome configurado")
            
        except Exception as e:
            logger.error(f"Erro ao configurar Chrome: {e}")
            raise
    
    # Substitua o método fazer_login() na classe AutoLogin por este:

    def fazer_login(self, url: str) -> bool:
        """Executa processo completo de login"""
        
        try:
            logger.info("🔐 Iniciando processo de login...")
            
            is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
            
            # Acessar página
            logger.info("Acessando Mercado Livre...")
            self.driver.get(url)
            
            if not is_ci:
                self.driver.maximize_window()
            
            self.esperar_natural(2, 4)
            
            if is_ci:
                try:
                    os.makedirs('debug_temp', exist_ok=True)
                    self.driver.save_screenshot('debug_temp/login_step1.png')
                    logger.info("📸 Screenshot salvo: login_step1.png")
                except:
                    pass
                
            # Clicar em "Já tenho conta"
            logger.info("Clicando em 'Já tenho conta'...")
            try:
                ja_tenho_conta = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Já tenho conta')] | //span[contains(text(), 'Já tenho conta')]"))
                )
                ja_tenho_conta.click()
            except Exception as e:
                logger.warning(f"Botão 'Já tenho conta' não encontrado: {e}")
            
            self.esperar_natural(1, 2)
            
            if is_ci:
                try:
                    self.driver.save_screenshot('debug_temp/login_step2.png')
                    logger.info("📸 Screenshot salvo: login_step2.png")
                except:
                    pass
                
            # Inserir email
            logger.info("Inserindo email...")
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "user_id"))
            )
            email_field.clear()
            
            for char in self.email:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self.esperar_natural(1, 2)
            
            if is_ci:
                try:
                    self.driver.save_screenshot('debug_temp/login_step3.png')
                    logger.info("📸 Screenshot salvo: login_step3.png")
                except:
                    pass
                
            # Clicar em "Continuar"
            logger.info("Clicando em 'Continuar'...")
            continuar_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit'] | //button[contains(text(), 'Continuar')]"))
            )
            continuar_btn.click()
            self.esperar_natural(2, 4)
            
            if is_ci:
                try:
                    self.driver.save_screenshot('debug_temp/login_step4.png')
                    with open('debug_temp/login_step4.html', 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    logger.info("📸 Screenshot e HTML salvos: login_step4")
                except:
                    pass
                
            # ===== CORREÇÃO PRINCIPAL: Múltiplas estratégias para solicitar código =====
            logger.info("Solicitando código por email...")
            
            # Estratégia 1: Tentar múltiplos seletores
            seletores_botao = [
                "//button[contains(text(), 'Enviar código')]",
                "//button[contains(text(), 'código')]",
                "//button[contains(@class, 'andes-button')]",
                "//*[@id='code_validation']//button",
                "//button[@type='button']",
                "//span[contains(text(), 'Enviar')]//ancestor::button",
            ]
            
            botao_encontrado = False
            
            for idx, seletor in enumerate(seletores_botao, 1):
                try:
                    logger.info(f"🔍 Tentando seletor {idx}/{len(seletores_botao)}: {seletor}")
                    enviar_codigo = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, seletor))
                    )
                    enviar_codigo.click()
                    logger.info(f"✅ Código solicitado (seletor {idx})!")
                    botao_encontrado = True
                    break
                except:
                    continue
                
            # Estratégia 2: Tentar via JavaScript
            if not botao_encontrado:
                logger.warning("⚠️ Nenhum seletor funcionou, tentando JS...")
                try:
                    # Buscar todos os botões
                    botoes = self.driver.find_elements(By.TAG_NAME, "button")
                    logger.info(f"🔍 Encontrados {len(botoes)} botões na página")
                    
                    # Tentar clicar em botões que possam ser o de código
                    for i, botao in enumerate(botoes):
                        try:
                            texto = botao.text.lower()
                            if any(palavra in texto for palavra in ['código', 'enviar', 'email']):
                                logger.info(f"🎯 Tentando botão {i+1}: '{botao.text[:50]}'")
                                self.driver.execute_script("arguments[0].click();", botao)
                                logger.info("✅ Código solicitado via JS!")
                                botao_encontrado = True
                                break
                        except:
                            continue
                except Exception as e:
                    logger.error(f"Erro na estratégia JS: {e}")
            
            # Estratégia 3: Verificar se já está na tela de código
            if not botao_encontrado:
                logger.warning("⚠️ Botão não encontrado, verificando se já estamos na tela de código...")
                try:
                    # Procurar campos de dígitos
                    campos_digitos = self.driver.find_elements(By.CSS_SELECTOR, 'input[aria-label*="Dígito"]')
                    if campos_digitos:
                        logger.info("✅ Tela de código já está visível! Continuando...")
                        botao_encontrado = True
                    else:
                        logger.error("❌ Tela de código não encontrada")
                except:
                    pass
                
            if not botao_encontrado:
                logger.error("❌ Falha ao solicitar código por todas as estratégias")
                if is_ci:
                    try:
                        self.driver.save_screenshot('debug_temp/login_error.png')
                        with open('debug_temp/login_error.html', 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        logger.info("💾 Erro salvo: login_error.png e login_error.html")
                    except:
                        pass
                return False
            
            self.esperar_natural(2, 3)
            
            if is_ci:
                try:
                    self.driver.save_screenshot('debug_temp/login_step5.png')
                    logger.info("📸 Screenshot salvo: login_step5.png")
                except:
                    pass
                
            # Buscar código via IMAP
            logger.info("📧 Buscando código no email...")
            codigo = self.buscar_codigo_imap()
            
            if not codigo:
                logger.error("❌ Código não encontrado no email")
                return False
            
            logger.info(f"🎯 Código encontrado: {codigo}")
            
            # Inserir código
            if not self.inserir_codigo(codigo):
                return False
            
            logger.info("✅ Login concluído com sucesso!")
            self.esperar_natural(3, 5)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def buscar_codigo_imap(self) -> Optional[str]:
        """Busca código de verificação via IMAP"""
        
        try:
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            senha_limpa = self.senha_app.replace(" ", "")
            imap.login(self.email, senha_limpa)
            imap.select("INBOX")
            
            max_tentativas = 8
            
            for tentativa in range(1, max_tentativas + 1):
                logger.info(f"🔍 Tentativa {tentativa}/{max_tentativas}")
                
                _, messages = imap.search(None, 'ALL')
                
                if messages[0]:
                    email_ids = messages[0].split()
                    ultimos_emails = email_ids[-5:] if len(email_ids) >= 5 else email_ids
                    
                    for email_id in reversed(ultimos_emails):
                        try:
                            _, msg_data = imap.fetch(email_id, "(RFC822)")
                            email_body = msg_data[0][1]
                            email_message = email_lib.message_from_bytes(email_body)
                            
                            from_header = email_message.get("From", "")
                            
                            # Verificar se é do Mercado Livre
                            if not any(x in from_header.lower() for x in ['mercadolivre', 'mercado livre', 'noreply']):
                                continue
                            
                            # Extrair corpo
                            body = ""
                            if email_message.is_multipart():
                                for part in email_message.walk():
                                    if part.get_content_type() in ["text/plain", "text/html"]:
                                        try:
                                            payload = part.get_payload(decode=True)
                                            if payload:
                                                body += payload.decode('utf-8', errors='ignore')
                                        except:
                                            pass
                            else:
                                try:
                                    payload = email_message.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode('utf-8', errors='ignore')
                                except:
                                    pass
                            
                            # Procurar código de 6 dígitos
                            match = re.search(r'[Nn][ãa]o compartilhe.*?(\d{6})', body, re.DOTALL | re.IGNORECASE)
                            if match:
                                imap.close()
                                imap.logout()
                                return match.group(1)
                            
                            codigos = re.findall(r'\b(\d{6})\b', body)
                            if codigos:
                                imap.close()
                                imap.logout()
                                return codigos[-1]
                        
                        except:
                            continue
                
                if tentativa < max_tentativas:
                    time.sleep(8)
            
            imap.close()
            imap.logout()
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar código via IMAP: {e}")
            return None
    
    def inserir_codigo(self, codigo: str) -> bool:
        """Insere código de verificação"""
        
        try:
            logger.info("📝 Inserindo código...")
            
            for i, digito in enumerate(codigo):
                campo = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'input[aria-label="Dígito {i+1}"]'))
                )
                campo.clear()
                campo.send_keys(digito)
                time.sleep(random.uniform(0.2, 0.4))
            
            self.esperar_natural(1, 2)
            
            # Clicar em confirmar
            try:
                botao_confirmar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="submit-button"]'))
                )
                botao_confirmar.click()
            except:
                botao_confirmar = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
                )
                botao_confirmar.click()
            
            logger.info("✅ Código confirmado!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inserir código: {e}")
            return False
    
    def obter_cookies(self) -> dict:
        """Obtém cookies da sessão autenticada"""
        
        cookies = {}
        for cookie in self.driver.get_cookies():
            cookies[cookie['name']] = cookie['value']
        return cookies
    
    def fechar(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()

# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PARA GERENCIAR SCRAPING
# ═══════════════════════════════════════════════════════════════════════════════

class MercadoLivreScraper:
    """Gerencia scraping do Mercado Livre com auto-login"""
    
    def __init__(self):
        self.session = self._criar_sessao()
        self.cookies_inicializados = False
        self.auto_login = None
        self.tentativas_totais = 0
        self.paginas_sucesso = 0
        self.paginas_falha = 0
    
    def _criar_sessao(self) -> requests.Session:
        """Cria sessão HTTP com headers realistas"""
        
        session = requests.Session()
        
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'identity',  # FORÇAR SEM COMPRESSÃO
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        }
        
        session.headers.update(headers)
        logger.info("📡 Sessão HTTP criada (sem compressão)")
        return session
    
    def verificar_bloqueio(self, url: str) -> bool:
        """Verifica se URL indica bloqueio/verificação"""
        return "account-verification" in url or "security" in url
    
    def executar_login(self, url_bloqueio: str) -> bool:
        """Executa processo de login via Selenium"""
        
        logger.warning("🔐 Bloqueio detectado! Iniciando login automático...")
        
        self.auto_login = AutoLogin(
            CONFIG['email_ml'],
            CONFIG['senha_app_ml']
        )
        
        self.auto_login.configurar_driver()
        
        if self.auto_login.fazer_login(url_bloqueio):
            # Transferir cookies para a sessão requests
            cookies = self.auto_login.obter_cookies()
            
            for name, value in cookies.items():
                self.session.cookies.set(name, value)
            
            logger.info("✅ Cookies transferidos para sessão HTTP")
            # NÃO FECHAR O DRIVER - vamos continuar usando ele
            logger.info("🌐 Mantendo navegador aberto para continuar busca")
            return True
        else:
            self.auto_login.fechar()
            return False
    
    def buscar_pagina(self, url: str, pagina_num: int, tentativa: int = 1) -> Optional[BeautifulSoup]:
        """Busca uma página com retry e auto-login se necessário"""
        
        self.tentativas_totais += 1
        
        logger.info(f"Buscando página {pagina_num} (tentativa {tentativa}/{CONFIG['max_tentativas']})")
        
        # Se já temos Selenium aberto e autenticado, usar ele
        if self.auto_login and self.auto_login.driver:
            logger.info("🌐 Usando Selenium autenticado")
            try:
                self.auto_login.driver.get(url)
                self.auto_login.esperar_natural(2, 4)
                
                # Verificar se foi bloqueado novamente
                if self.verificar_bloqueio(self.auto_login.driver.current_url):
                    logger.error("❌ Bloqueio persistiu mesmo com Selenium autenticado")
                    self.paginas_falha += 1
                    return None
                
                # Capturar HTML
                html_content = self.auto_login.driver.page_source
                
                # Salvar para debug
                if CONFIG.get('salvar_html_debug', False):
                    os.makedirs('debug_temp', exist_ok=True)
                    filename = f'debug_temp/selenium_pagina_{pagina_num}_tent{tentativa}.html'
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"💾 HTML do Selenium salvo: {filename}")
                
                # Parse HTML
                try:
                    soup = BeautifulSoup(html_content, 'lxml')
                except:
                    soup = BeautifulSoup(html_content, 'html.parser')
                
                self.paginas_sucesso += 1
                logger.info(f"✅ Página {pagina_num} carregada via Selenium")
                return soup
                
            except Exception as e:
                logger.error(f"Erro ao usar Selenium: {e}")
                if tentativa < CONFIG['max_tentativas']:
                    return self.buscar_pagina(url, pagina_num, tentativa + 1)
                self.paginas_falha += 1
                return None
        
        # MODO DEBUG: Forçar uso do Selenium
        if CONFIG.get('forcar_selenium', False) and tentativa == 1:
            logger.warning("🔧 MODO DEBUG: Forçando uso do Selenium...")
            url_teste = CONFIG['url_base'] if pagina_num == 1 else url
            
            # Simular bloqueio para acionar login
            if not self.auto_login:
                logger.info("🌐 Abrindo navegador Chrome...")
                self.auto_login = AutoLogin(CONFIG['email_ml'], CONFIG['senha_app_ml'])
                self.auto_login.configurar_driver()
                
                logger.info(f"📍 Navegando para: {url_teste}")
                self.auto_login.driver.get(url_teste)
                
                logger.info("⏸️  Aguardando 30 segundos para você analisar a página...")
                logger.info("💡 Verifique se há bloqueio ou se a página carregou corretamente")
                time.sleep(30)
                
                # Capturar HTML do Selenium
                html_selenium = self.auto_login.driver.page_source
                
                # Salvar para debug
                if CONFIG.get('salvar_html_debug', False):
                    os.makedirs('debug_temp', exist_ok=True)
                    filename = f'debug_temp/selenium_pagina_{pagina_num}.html'
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(html_selenium)
                    logger.info(f"💾 HTML do Selenium salvo em: {filename}")
                
                # Transferir cookies
                cookies = self.auto_login.obter_cookies()
                for name, value in cookies.items():
                    self.session.cookies.set(name, value)
                
                logger.info("✅ Cookies transferidos do Selenium")
        
        try:
            if tentativa > 1:
                delay = tentativa * CONFIG['delay_entre_tentativas']
                logger.info(f"⏳ Aguardando {delay}s...")
                time.sleep(delay)
            
            inicio = time.time()
            response = self.session.get(url, timeout=CONFIG['timeout'], allow_redirects=True)
            duracao = time.time() - inicio
            
            logger.info(f"Status: {response.status_code} | Tempo: {duracao:.2f}s")
            
            # DESCOMPRIMIR CONTEÚDO SE NECESSÁRIO
            content_encoding = response.headers.get('content-encoding', '').lower()
            if content_encoding or not response.text.strip().startswith('<'):
                logger.info(f"🔄 Tentando descomprimir conteúdo (encoding: {content_encoding})...")
                
                import gzip
                import zlib
                
                # Tentar múltiplos métodos de descompressão
                decompressed = False
                
                # Método 1: gzip
                try:
                    decompressed_content = gzip.decompress(response.content)
                    response._content = decompressed_content
                    response.encoding = 'utf-8'
                    logger.info(f"✅ Descomprimido com GZIP: {len(decompressed_content)} bytes")
                    decompressed = True
                except:
                    pass
                
                # Método 2: deflate
                if not decompressed:
                    try:
                        decompressed_content = zlib.decompress(response.content)
                        response._content = decompressed_content
                        response.encoding = 'utf-8'
                        logger.info(f"✅ Descomprimido com DEFLATE: {len(decompressed_content)} bytes")
                        decompressed = True
                    except:
                        pass
                
                # Método 3: deflate raw
                if not decompressed:
                    try:
                        decompressed_content = zlib.decompress(response.content, -zlib.MAX_WBITS)
                        response._content = decompressed_content
                        response.encoding = 'utf-8'
                        logger.info(f"✅ Descomprimido com DEFLATE-RAW: {len(decompressed_content)} bytes")
                        decompressed = True
                    except:
                        pass
                
                if not decompressed:
                    logger.warning("⚠️ Não foi possível descomprimir o conteúdo")
            
            # VERIFICAR BLOQUEIO
            if self.verificar_bloqueio(response.url):
                logger.warning("🚫 BLOQUEIO DETECTADO!")
                logger.info(f"URL de bloqueio: {response.url}")
                
                # Executar login apenas na primeira tentativa de bloqueio
                if tentativa == 1:
                    if self.executar_login(response.url):
                        logger.info("✅ Login concluído! Continuando com Selenium...")
                        # Tentar novamente, mas agora vai usar Selenium
                        return self.buscar_pagina(url, pagina_num, tentativa + 1)
                    else:
                        logger.error("❌ Falha no login automático")
                        self.paginas_falha += 1
                        return None
                else:
                    logger.error("❌ Bloqueio persistiu após login")
                    self.paginas_falha += 1
                    return None
            
            # Verificar status codes
            if response.status_code == 403:
                logger.error("🚫 HTTP 403: Acesso negado")
                if tentativa < CONFIG['max_tentativas']:
                    return self.buscar_pagina(url, pagina_num, tentativa + 1)
                self.paginas_falha += 1
                return None
            
            if response.status_code == 429:
                logger.error("🚫 HTTP 429: Rate limit excedido")
                time.sleep(10)
                if tentativa < CONFIG['max_tentativas']:
                    return self.buscar_pagina(url, pagina_num, tentativa + 1)
                self.paginas_falha += 1
                return None
            
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code}")
                if tentativa < CONFIG['max_tentativas']:
                    return self.buscar_pagina(url, pagina_num, tentativa + 1)
                self.paginas_falha += 1
                return None
            
            # Parse HTML
            try:
                soup = BeautifulSoup(response.text, 'lxml')
            except:
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # DEBUG: Salvar HTML para análise
            if CONFIG.get('salvar_html_debug', False):
                try:
                    os.makedirs('debug_temp', exist_ok=True)
                    filename = f'debug_temp/pagina_{pagina_num}_tent{tentativa}.html'
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.info(f"🔍 HTML salvo em: {filename}")
                    
                    # Mostrar preview do HTML
                    preview = response.text[:500]
                    logger.info(f"📄 Preview HTML: {preview}...")
                    
                    # Verificar se parece ser uma página válida
                    if '<html' not in response.text.lower():
                        logger.warning("⚠️ Resposta não parece ser HTML válido!")
                    
                    # Contar elementos importantes
                    num_divs = response.text.count('<div')
                    num_links = response.text.count('<a ')
                    logger.info(f"📊 Elementos no HTML: {num_divs} divs, {num_links} links")
                    
                except Exception as e:
                    logger.warning(f"Erro ao salvar debug: {e}")
            
            self.paginas_sucesso += 1
            logger.info(f"✅ Página {pagina_num} carregada com sucesso")
            
            return soup
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout na requisição")
            if tentativa < CONFIG['max_tentativas']:
                return self.buscar_pagina(url, pagina_num, tentativa + 1)
            self.paginas_falha += 1
            return None
            
        except Exception as e:
            logger.error(f"Erro: {e}")
            if tentativa < CONFIG['max_tentativas']:
                return self.buscar_pagina(url, pagina_num, tentativa + 1)
            self.paginas_falha += 1
            return None
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do scraper"""
        return {
            'tentativas_totais': self.tentativas_totais,
            'paginas_sucesso': self.paginas_sucesso,
            'paginas_falha': self.paginas_falha,
            'taxa_sucesso': f"{(self.paginas_sucesso / max(self.tentativas_totais, 1) * 100):.1f}%"
        }
    
    def fechar(self):
        """Fecha recursos do scraper"""
        if self.auto_login:
            logger.info("🔒 Fechando navegador Selenium...")
            self.auto_login.fechar()
            self.auto_login = None

# ═══════════════════════════════════════════════════════════════════════════════
# EXTRAÇÃO DE PRODUTOS
# ═══════════════════════════════════════════════════════════════════════════════

class ProdutoExtractor:
    """Extrai e processa produtos do HTML"""
    
    @staticmethod
    def extrair_produtos(soup: BeautifulSoup, pagina_num: int) -> List[Dict]:
        """Extrai produtos usando múltiplas estratégias"""
        
        logger.info(f"Extraindo produtos da página {pagina_num}")
        
        estrategias = [
            ("li.ui-search-layout__item", "Layout padrão"),
            ("div.ui-search-result__wrapper", "Wrapper"),
            ("div.ui-search-result", "Result div"),
            ("ol.ui-search-layout li", "Lista direta"),
            ("article", "Articles"),
            ("div[class*='ui-search']", "Divs com ui-search"),
        ]
        
        items = []
        
        for seletor, descricao in estrategias:
            items = soup.select(seletor)
            logger.info(f"🔍 Testando '{descricao}' ({seletor}): {len(items)} elementos")
            if items:
                logger.info(f"✅ Estratégia '{descricao}': {len(items)} produtos")
                break
        
        if not items:
            logger.error("❌ Nenhum produto encontrado com nenhuma estratégia")
            
            # DEBUG: Análise adicional
            logger.info("🔍 Analisando estrutura da página...")
            
            # Verificar título da página
            title = soup.find('title')
            if title:
                logger.info(f"📄 Título da página: {title.get_text()[:100]}")
            
            # Procurar por mensagens de erro
            error_msgs = soup.find_all(string=re.compile(r'nenhum|sem resultado|não encontrado', re.I))
            if error_msgs:
                logger.warning(f"⚠️ Mensagens encontradas: {[msg[:50] for msg in error_msgs[:3]]}")
            
            # Contar todas as tags principais
            all_divs = soup.find_all('div')
            all_links = soup.find_all('a')
            logger.info(f"📊 Total na página: {len(all_divs)} divs, {len(all_links)} links")
            
            # Verificar se há produtos em formato diferente
            possible_products = soup.find_all('a', href=re.compile(r'/MLB-'))
            logger.info(f"🔗 Links com /MLB- encontrados: {len(possible_products)}")
            
            if possible_products:
                logger.info("💡 Produtos detectados em formato alternativo, tentando extração...")
                items = possible_products[:50]  # Limitar a 50
            else:
                return []
        
        produtos = []
        offset = (pagina_num - 1) * CONFIG['produtos_por_pagina']
        
        for idx, item in enumerate(items, start=1):
            try:
                produto = ProdutoExtractor._extrair_produto(item, offset + idx)
                if produto:
                    produtos.append(produto)
            except:
                continue
        
        logger.info(f"📦 {len(produtos)} produtos extraídos")
        return produtos
    
    @staticmethod
    def _extrair_produto(elemento, posicao: int) -> Optional[Dict]:
        """Extrai dados de um único produto"""
        
        # Encontrar link
        link_elem = elemento.find('a', class_='ui-search-link') or elemento.find('a', href=True)
        if not link_elem:
            return None
        
        # Extrair título
        titulo = link_elem.get('title', '').strip() or link_elem.get_text(strip=True)
        link = link_elem.get('href', '')
        
        if not titulo or not link:
            return None
        
        if not link.startswith('http'):
            link = urljoin('https://www.mercadolivre.com.br', link)
        
        # Extrair ID
        item_id = ''
        if match := re.search(r'MLB-?\d+', link):
            item_id = match.group(0).replace('-', '')
        
        # Filtros
        titulo_lower = titulo.lower()
        
        if any(exc in titulo_lower for exc in CONFIG['exclusoes_titulo']):
            return None
        
        if any(exc.lower() in item_id.lower() for exc in CONFIG['exclusoes_id']):
            return None
        
        if not any(term in titulo_lower for term in CONFIG['termos_obrigatorios']):
            return None
        
        # Extrair preço
        preco_str = ProdutoExtractor._extrair_preco(elemento)
        if not preco_str:
            return None
        
        preco_numerico = ProdutoExtractor._converter_preco(preco_str)
        categoria = ProdutoExtractor._categorizar(titulo)
        
        return {
            'Título': titulo,
            'Preço': preco_str,
            'Preço_Numerico': preco_numerico,
            'Link': link,
            'Posição': posicao,
            'Categoria': categoria,
            'ID': item_id,
        }
    
    @staticmethod
    def _extrair_preco(elemento) -> Optional[str]:
        """Extrai preço do elemento"""
        
        fraction = elemento.find('span', class_='andes-money-amount__fraction')
        if fraction:
            fraction_text = fraction.get_text(strip=True)
            cents = elemento.find('span', class_='andes-money-amount__cents')
            cents_text = cents.get_text(strip=True) if cents else "00"
            return f"R$ {fraction_text},{cents_text}"
        
        texto = elemento.get_text()
        if match := re.search(r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', texto):
            return f"R$ {match.group(1)}"
        
        return None
    
    @staticmethod
    def _converter_preco(preco_str: str) -> float:
        """Converte string de preço para float"""
        try:
            return float(preco_str.replace("R$", "").replace(".", "").replace(",", ".").strip())
        except:
            return float('inf')
    
    @staticmethod
    def _categorizar(titulo: str) -> str:
        """Categoriza produto pelo título"""
        titulo_lower = titulo.lower()
        
        if "mc donalds" not in titulo_lower and "mcdonald" not in titulo_lower:
            return 'Desconhecido'
        
        is_dupla = any(p in titulo_lower for p in CONFIG['padroes_dupla'])
        is_vermelha = any(p in titulo_lower for p in CONFIG['padroes_vermelho'])
        is_preta = any(p in titulo_lower for p in CONFIG['padroes_preto'])
        
        if is_dupla:
            return '2un'
        elif is_vermelha and is_preta:
            return 'Vermelha' if "vermelho" in titulo_lower else 'Preta'
        elif is_vermelha:
            return 'Vermelha'
        elif is_preta:
            return 'Preta'
        else:
            return 'Desconhecido'

# ═══════════════════════════════════════════════════════════════════════════════
# BUSCA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def buscar_produtos(scraper: MercadoLivreScraper) -> List[Dict]:
    """Busca produtos no Mercado Livre"""
    
    logger.info("="*80)
    logger.info("INICIANDO BUSCA DE PRODUTOS")
    logger.info("="*80)
    
    todos_produtos = []
    
    for pagina in range(1, CONFIG['max_paginas'] + 1):
        logger.info("")
        logger.info(f"━━━ PÁGINA {pagina}/{CONFIG['max_paginas']} ━━━")
        
        if pagina == 1:
            url = CONFIG['url_base']
        else:
            offset = (pagina - 1) * CONFIG['produtos_por_pagina'] + 1
            url = f"{CONFIG['url_base']}_Desde_{offset}"
        
        soup = scraper.buscar_pagina(url, pagina)
        
        if not soup:
            logger.error(f"Falha ao carregar página {pagina}")
            break
        
        produtos_pagina = ProdutoExtractor.extrair_produtos(soup, pagina)
        
        if not produtos_pagina:
            if pagina == 1:
                logger.error("Primeira página sem resultados - Abortando")
                break
            else:
                logger.info("Fim dos resultados")
                break
        
        todos_produtos.extend(produtos_pagina)
        logger.info(f"📊 Total acumulado: {len(todos_produtos)} produtos")
        
        if pagina < CONFIG['max_paginas']:
            delay = random.uniform(*CONFIG['delay_entre_paginas'])
            time.sleep(delay)
    
    return todos_produtos

# ═══════════════════════════════════════════════════════════════════════════════
# RELATÓRIOS
# ═══════════════════════════════════════════════════════════════════════════════

def exibir_relatorio_console(produtos: List[Dict]):
    """Exibe relatório no console"""
    
    print("\n" + "="*100)
    print("📊 RELATÓRIO DE PRODUTOS")
    print("="*100)
    
    categorias = defaultdict(list)
    for p in produtos:
        categorias[p['Categoria']].append(p)
    
    for cat, itens in sorted(categorias.items()):
        print(f"\n{'─'*100}")
        print(f"📦 {cat} - {len(itens)} produtos")
        print(f"{'─'*100}")
        
        itens_ord = sorted(itens, key=lambda x: x['Preço_Numerico'])[:10]
        
        for i, p in enumerate(itens_ord, 1):
            print(f"\n{i}. {p['Título'][:75]}")
            print(f"   💰 {p['Preço']}")
            print(f"   🔗 {p['Link']}")

def enviar_email(produtos: List[Dict]) -> bool:
    """Envia relatório por email"""
    
    logger.info("Preparando envio de e-mail...")
    
    email = CONFIG['email_destino']
    senha = CONFIG['senha_app_destino']
    
    # HTML do email
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><style>
    body{{font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px}}
    .container{{max-width:1200px;margin:0 auto;background:white;padding:30px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}}
    h1{{color:#333;border-bottom:3px solid #FFD700;padding-bottom:10px}}
    h2{{color:#555;margin-top:30px;border-left:4px solid #4CAF50;padding-left:10px}}
    table{{width:100%;border-collapse:collapse;margin-top:15px}}
    th,td{{padding:12px;text-align:left;border-bottom:1px solid #ddd}}
    th{{background:#f8f8f8;font-weight:600;color:#333}}
    tr:hover{{background:#f9f9f9}}
    .btn{{display:inline-block;padding:8px 16px;background:#4CAF50;color:white;text-decoration:none;border-radius:5px;font-size:12px}}
    .btn:hover{{background:#45a049}}
    .preco{{color:#e91e63;font-weight:bold}}
    .footer{{margin-top:30px;padding-top:20px;border-top:2px solid #eee;color:#666;font-size:14px}}
    </style></head>
    <body>
    <div class="container">
    <h1>🏎️ Miniaturas F1 1/43 McDonald's</h1>
    <p><strong>Total de produtos:</strong> {len(produtos)}</p>
    <p><strong>Data da busca:</strong> {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
    """
    
    categorias = defaultdict(list)
    for p in produtos:
        if p['Preço_Numerico'] < float('inf'):
            categorias[p['Categoria']].append(p)
    
    for cat, itens in sorted(categorias.items()):
        itens_ord = sorted(itens, key=lambda x: x['Preço_Numerico'])[:CONFIG['numero_itens_email']]
        
        html += f"""
        <h2>📦 {cat} - Top {len(itens_ord)} Melhores Preços</h2>
        <table>
        <tr>
            <th style="width:50px">Pos.</th>
            <th>Produto</th>
            <th style="width:100px">Preço</th>
            <th style="width:80px">Link</th>
        </tr>
        """
        
        for p in itens_ord:
            titulo = p['Título'][:80] + ('...' if len(p['Título']) > 80 else '')
            html += f"""
            <tr>
                <td style="text-align:center">{p['Posição']}</td>
                <td>{titulo}</td>
                <td class="preco">{p['Preço']}</td>
                <td style="text-align:center"><a href="{p['Link']}" class="btn" target="_blank">Ver</a></td>
            </tr>
            """
        
        html += "</table>"
    
    html += """
    <div class="footer">
    <strong>🤖 Monitor Automático de Preços</strong><br>
    Mercado Livre Brasil<br>
    Sistema integrado com auto-login
    </div>
    </div></body></html>
    """
    
    msg = EmailMessage()
    msg['Subject'] = f'📦 F1 McDonald\'s 1/43 - {len(produtos)} produtos encontrados'
    msg['From'] = email
    msg['To'] = email
    msg.set_content("Visualize este email em HTML para ver o relatório completo.")
    msg.add_alternative(html, subtype='html')
    
    try:
        logger.info("Conectando ao SMTP do Gmail...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email, senha)
            smtp.send_message(msg)
        logger.info("✅ E-mail enviado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {e}")
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Função principal"""
    
    print("\n" + "╔" + "═"*98 + "╗")
    print("║" + "  🏎️  MONITOR DE PREÇOS F1 1/43 McDONALD'S".center(100) + "║")
    print("║" + "  Mercado Livre Brasil - v4.0 (Auto-Login)".center(100) + "║")
    print("╚" + "═"*98 + "╝\n")
    
    # Detectar ambiente CI
    is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
    if is_ci:
        logger.info("🤖 Executando em ambiente CI/CD (GitHub Actions)")
        # Criar diretório de debug
        os.makedirs('debug_temp', exist_ok=True)
    
    logger.info("Iniciando Monitor de Preços v4.0")
    
    inicio_execucao = time.time()
    
    try:
        # Criar scraper
        scraper = MercadoLivreScraper()
        
        # Buscar produtos
        produtos = buscar_produtos(scraper)
        
        # Remover duplicatas
        produtos_unicos = {}
        for p in produtos:
            if p['ID'] not in produtos_unicos:
                produtos_unicos[p['ID']] = p
        
        produtos = list(produtos_unicos.values())
        
        # Estatísticas do scraper
        stats = scraper.get_stats()
        logger.info("")
        logger.info("="*80)
        logger.info("ESTATÍSTICAS DE SCRAPING")
        logger.info("="*80)
        logger.info(f"Tentativas totais: {stats['tentativas_totais']}")
        logger.info(f"Páginas com sucesso: {stats['paginas_sucesso']}")
        logger.info(f"Páginas com falha: {stats['paginas_falha']}")
        logger.info(f"Taxa de sucesso: {stats['taxa_sucesso']}")
        
        logger.info("")
        logger.info("="*80)
        logger.info("RESULTADO FINAL")
        logger.info("="*80)
        logger.info(f"Total de produtos únicos: {len(produtos)}")
        
        if len(produtos) == 0:
            logger.warning("NENHUM PRODUTO ENCONTRADO")
            print("\n" + "="*100)
            print("⚠️  NENHUM PRODUTO ENCONTRADO")
            print("="*100)
            print("\n💡 Possíveis causas:")
            print("   1. Mercado Livre bloqueando requisições")
            print("   2. Nenhum produto disponível no momento")
            print("   3. Filtros muito restritivos")
            return
        
        # Estatísticas por categoria
        categorias_stats = defaultdict(int)
        precos_por_categoria = defaultdict(list)
        
        for p in produtos:
            categorias_stats[p['Categoria']] += 1
            if p['Preço_Numerico'] < float('inf'):
                precos_por_categoria[p['Categoria']].append(p['Preço_Numerico'])
        
        logger.info("")
        logger.info("DISTRIBUIÇÃO POR CATEGORIA:")
        for cat in sorted(categorias_stats.keys()):
            qtd = categorias_stats[cat]
            precos = precos_por_categoria[cat]
            if precos:
                media = sum(precos) / len(precos)
                minimo = min(precos)
                logger.info(f"  {cat}: {qtd} produtos | Média: R$ {media:.2f} | Mínimo: R$ {minimo:.2f}")
            else:
                logger.info(f"  {cat}: {qtd} produtos")
        
        # Salvar resultados completos para CI
        if is_ci and len(produtos) > 0:
            results_file = 'debug_temp/resultados.json'
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_produtos': len(produtos),
                    'categorias': {cat: qtd for cat, qtd in categorias_stats.items()},
                    'produtos': produtos[:10],  # Apenas top 10
                    'stats': stats,
                    'timestamp': datetime.datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Resultados salvos em: {results_file}")
        
        # Exibir relatório
        exibir_relatorio_console(produtos)
        
        # Top produtos mais baratos
        produtos_validos = [p for p in produtos if p['Preço_Numerico'] < float('inf')]
        if produtos_validos:
            top_baratos = sorted(produtos_validos, key=lambda x: x['Preço_Numerico'])[:5]
            
            print("\n" + "="*100)
            print("🏆 TOP 5 PRODUTOS MAIS BARATOS")
            print("="*100)
            
            for i, p in enumerate(top_baratos, 1):
                print(f"\n{i}º - {p['Título'][:70]}")
                print(f"    💰 {p['Preço']} | 🏷️  {p['Categoria']}")
                print(f"    🔗 {p['Link']}")
        
        # Enviar email
        print("\n" + "="*100)
        print("📧 ENVIANDO RELATÓRIO POR E-MAIL")
        print("="*100)
        
        email_enviado = enviar_email(produtos)
        
        # Tempo de execução
        duracao = time.time() - inicio_execucao
        
        # Sumário final
        print("\n" + "╔" + "═"*98 + "╗")
        print("║" + " "*100 + "║")
        
        if email_enviado:
            print("║" + "  ✅ PROCESSO CONCLUÍDO COM SUCESSO!".center(100) + "║")
        else:
            print("║" + "  ⚠️  PROCESSO CONCLUÍDO (erro no e-mail)".center(100) + "║")
        
        print("║" + " "*100 + "║")
        print("║" + f"  📊 {len(produtos)} produtos processados".center(100) + "║")
        print("║" + f"  📧 E-mail: {'Enviado' if email_enviado else 'Falhou'}".center(100) + "║")
        print("║" + f"  ⏱️  Tempo: {duracao:.1f}s".center(100) + "║")
        print("║" + " "*100 + "║")
        print("╚" + "═"*98 + "╝\n")
        
        logger.info(f"Execução concluída em {duracao:.1f} segundos")
        logger.info(f"Produtos processados: {len(produtos)}")
        logger.info(f"E-mail enviado: {'Sim' if email_enviado else 'Não'}")
        
        # Fechar recursos
        scraper.fechar()
        
    except KeyboardInterrupt:
        logger.warning("Execução interrompida pelo usuário")
        print("\n\n⚠️  Execução interrompida pelo usuário")
        print("👋 Até logo!\n")
        
    except Exception as e:
        logger.critical(f"ERRO CRÍTICO: {e}")
        print("\n" + "="*100)
        print("❌ ERRO CRÍTICO")
        print("="*100)
        print(f"\n{e}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
