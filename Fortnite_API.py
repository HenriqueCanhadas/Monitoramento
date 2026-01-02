"""
MONITOR FORTNITE - VERSÃO ULTRA MELHORADA
Estratégia: Lista todos os itens primeiro, depois faz matching inteligente
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import random
import smtplib
from email.message import EmailMessage
import os
import unicodedata
from difflib import SequenceMatcher

# ========================================
# CONFIGURAÇÕES
# ========================================
ITENS_MONITORAR = [
    "O Batman Que Ri",
    "Superman",
    "Hatsune Miku",
    "Johnny Silverhand",
    "Iron Man",
    "Darth Vader",
    "Darth Vader Samurai",
    "Stormtrooper Samurai",
    "Yuji Itadori",
    "Megumi Fushiguro",
    "Satoru Gojo",
    "Nobara Kugisaki",
    "Goku Black",
    "Eren Jaeger",
    "Mikasa Ackermann",
    "Captain Levi",
    "Son Goku",
    "Vegeta",
    "Bulma"
]

# Configuração de Email
EMAIL_REMETENTE = os.getenv('EMAIL_APP_P')
SENHA_APP = os.getenv('SENHA_APP_P')
DESTINATARIOS = [EMAIL_REMETENTE]

FORTNITE_SHOP_URL = "https://www.fortnite.com/item-shop?lang=pt-BR"

# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def obter_horario_brasilia():
    try:
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    except:
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def normalizar_texto(texto):
    """Remove acentos, lowercase e remove espaços extras"""
    texto = texto.lower().strip()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    texto = ' '.join(texto.split())
    return texto

def similaridade_strings(str1, str2):
    """
    Calcula similaridade entre duas strings usando SequenceMatcher
    Retorna valor entre 0 e 1 (1 = idêntico)
    """
    return SequenceMatcher(None, normalizar_texto(str1), normalizar_texto(str2)).ratio()

def palavras_em_comum(str1, str2):
    """Retorna conjunto de palavras em comum entre duas strings"""
    palavras1 = set(normalizar_texto(str1).split())
    palavras2 = set(normalizar_texto(str2).split())
    return palavras1 & palavras2

def e_match_valido(item_busca, item_loja):
    """
    Determina se um item da loja é um match válido para a busca
    Usa múltiplos critérios para evitar falsos positivos
    """
    # Normaliza ambos
    busca_norm = normalizar_texto(item_busca)
    loja_norm = normalizar_texto(item_loja)
    
    # Critério 1: Match exato ou substring
    if busca_norm == loja_norm or busca_norm in loja_norm:
        return True, 1.0, "match_exato"
    
    # Critério 2: Todas as palavras da busca estão na loja
    palavras_busca = set(busca_norm.split())
    palavras_loja = set(loja_norm.split())
    
    # Remove palavras muito comuns/genéricas
    palavras_genericas = {'pacote', 'pacotao', 'pack', 'bundle', 'set', 'edition', 'skin', 'outfit'}
    palavras_busca = palavras_busca - palavras_genericas
    palavras_loja = palavras_loja - palavras_genericas
    
    if palavras_busca and palavras_busca.issubset(palavras_loja):
        # Todas as palavras da busca estão na loja
        similaridade = len(palavras_busca) / len(palavras_loja) if palavras_loja else 0
        return True, similaridade, "subset_completo"
    
    # Critério 3: Pelo menos 2 palavras significativas em comum
    palavras_comuns = palavras_busca & palavras_loja
    palavras_significativas = [p for p in palavras_comuns if len(p) >= 4]
    
    if len(palavras_significativas) >= 2:
        similaridade = len(palavras_comuns) / len(palavras_busca) if palavras_busca else 0
        if similaridade >= 0.7:  # 70% das palavras batem
            return True, similaridade, "palavras_significativas"
    
    # Critério 4: Similaridade de string alta (para nomes compostos)
    sim_score = similaridade_strings(item_busca, item_loja)
    if sim_score >= 0.85:  # 85% de similaridade
        return True, sim_score, "similaridade_alta"
    
    return False, 0.0, "nao_match"

def encontrar_card_correto(driver, elemento_titulo, nome_item):
    """Sobe na hierarquia DOM até encontrar o card completo com preço"""
    current = elemento_titulo
    nivel = 0
    max_niveis = 10
    
    while nivel < max_niveis:
        try:
            parent = current.find_element(By.XPATH, "..")
            texto_nivel = driver.execute_script("return arguments[0].textContent;", parent)
            
            nome_normalizado = normalizar_texto(nome_item)
            texto_normalizado = normalizar_texto(texto_nivel)
            ocorrencias = texto_normalizado.count(nome_normalizado)
            
            if ocorrencias == 1:
                tem_preco = 'v-bucks' in texto_normalizado or 'vbucks' in texto_normalizado
                if tem_preco:
                    return parent
            
            current = parent
            nivel += 1
            
        except:
            break
    
    return current

def extrair_preco_do_card(driver, card_element, nome_item):
    """Extrai preço do card com múltiplos métodos"""
    
    # Método 1: data-testid específico
    try:
        preco_elements = card_element.find_elements(By.XPATH, ".//*[@data-testid='current-vbuck-price']")
        
        if preco_elements:
            preco_el = preco_elements[0]
            texto = driver.execute_script("return arguments[0].textContent;", preco_el)
            
            if texto and texto.strip():
                preco_limpo = re.sub(r'[^\d]', '', texto)
                if preco_limpo and preco_limpo.isdigit():
                    return int(preco_limpo)
            
            html = driver.execute_script("return arguments[0].innerHTML;", preco_el)
            texto_limpo = re.sub(r'<[^>]+>', '', html)
            preco_limpo = re.sub(r'[^\d]', '', texto_limpo)
            
            if preco_limpo and preco_limpo.isdigit():
                return int(preco_limpo)
                
    except:
        pass
    
    # Método 2: Busca por classe
    try:
        preco_el = card_element.find_element(By.CSS_SELECTOR, '[class*="price"], [class*="vbuck"], [class*="cost"]')
        texto = preco_el.text
        preco_limpo = re.sub(r'[^\d]', '', texto)
        if preco_limpo and preco_limpo.isdigit():
            preco_num = int(preco_limpo)
            if 100 <= preco_num <= 10000:
                return preco_num
    except:
        pass
    
    # Método 3: Regex no texto do card
    try:
        texto_card = driver.execute_script("return arguments[0].textContent;", card_element)
        matches = re.findall(r'(\d{1,2}\.\d{3}|\d{3,5})\s*(?:V-?Bucks?)?', texto_card, re.IGNORECASE)
        
        if matches:
            for match in matches:
                preco_str = match.replace('.', '')
                try:
                    preco_num = int(preco_str)
                    if 100 <= preco_num <= 10000:
                        return preco_num
                except:
                    continue
    except:
        pass
    
    return None

def inicializar_driver_antidetect():
    print("🔧 Configurando navegador anti-detecção...")
    
    options = uc.ChromeOptions()
    
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    options.add_argument('--headless=new')
    
    try:
        print("   🔍 Detectando versão do Chrome instalada...")
        driver = uc.Chrome(options=options)
        print("   ✅ Driver inicializado com sucesso!")
    except Exception as e:
        print(f"   ⚠️ Erro ao inicializar: {e}")
        print("   🔄 Tentando método alternativo...")
        driver = uc.Chrome(options=options, use_subprocess=True)
    
    try:
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": random.choice(user_agents)
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except:
        pass
    
    return driver

def aguardar_pagina_carregar(driver, timeout=30):
    print("⏳ Aguardando página carregar (pode demorar pelo Cloudflare)...")
    
    inicio = time.time()
    time.sleep(10)
    
    tentativas = 0
    max_tentativas = 6
    
    while tentativas < max_tentativas:
        try:
            if "cloudflare" in driver.page_source.lower() and "checking" in driver.page_source.lower():
                print(f"   ⏳ Cloudflare verificando... (tentativa {tentativas + 1}/{max_tentativas})")
                time.sleep(5)
                tentativas += 1
                continue
            
            if "fortnite" in driver.page_source.lower() or "item" in driver.page_source.lower():
                print("   ✅ Página carregada!")
                time.sleep(3)
                return True
            
            time.sleep(5)
            tentativas += 1
            
        except Exception as e:
            print(f"   ⚠️ Erro ao verificar: {e}")
            time.sleep(5)
            tentativas += 1
    
    tempo_total = time.time() - inicio
    print(f"   ⏰ Tempo total de carregamento: {tempo_total:.1f}s")
    return False

def fazer_scroll_completo(driver):
    """Faz scroll na página para carregar todos os itens"""
    print("   📜 Fazendo scroll para carregar todos os itens...")
    
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
            
            last_height = new_height
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        print("   ✅ Scroll completo\n")
    except Exception as e:
        print(f"   ⚠️ Erro no scroll: {e}\n")

# ========================================
# NOVA ESTRATÉGIA: LISTA TODOS OS ITENS PRIMEIRO
# ========================================

def listar_todos_itens_da_loja(driver):
    """
    PASSO 1: Lista TODOS os itens disponíveis na loja
    Retorna: lista de dicionários com {nome, elemento, card}
    """
    print("\n📋 PASSO 1: Listando TODOS os itens da loja...")
    
    fazer_scroll_completo(driver)
    
    itens_encontrados = []
    elementos_processados = set()
    
    try:
        # Usa apenas o seletor principal que sabemos que funciona
        elementos_titulo = driver.find_elements(By.CSS_SELECTOR, '[data-testid="item-title"]')
        
        print(f"   📄 Encontrados {len(elementos_titulo)} elementos de título\n")
        
        for elemento in elementos_titulo:
            try:
                nome = elemento.text.strip()
                
                if not nome or len(nome) < 2:
                    continue
                
                # Evita duplicatas
                nome_norm = normalizar_texto(nome)
                if nome_norm in elementos_processados:
                    continue
                
                elementos_processados.add(nome_norm)
                
                # Busca o card e preço
                card = encontrar_card_correto(driver, elemento, nome)
                preco = extrair_preco_do_card(driver, card, nome)
                
                itens_encontrados.append({
                    'nome': nome,
                    'nome_normalizado': nome_norm,
                    'elemento': elemento,
                    'card': card,
                    'preco': preco
                })
                
                preco_str = f"{preco} V-Bucks" if preco else "sem preço"
                print(f"   • {nome} ({preco_str})")
                
            except Exception as e:
                continue
        
        print(f"\n   ✅ Total de {len(itens_encontrados)} itens únicos na loja\n")
        
    except Exception as e:
        print(f"   ❌ Erro ao listar itens: {e}\n")
    
    return itens_encontrados

def buscar_itens_monitorados(itens_loja, itens_procurados):
    """
    PASSO 2: Busca os itens monitorados na lista da loja
    Usa matching inteligente para evitar falsos positivos
    """
    print("🔍 PASSO 2: Buscando itens monitorados na lista...\n")
    
    resultados = []
    
    for item_busca in itens_procurados:
        melhor_match = None
        melhor_score = 0
        melhor_tipo = None
        
        # Testa contra cada item da loja
        for item_loja in itens_loja:
            e_match, score, tipo = e_match_valido(item_busca, item_loja['nome'])
            
            if e_match and score > melhor_score:
                melhor_match = item_loja
                melhor_score = score
                melhor_tipo = tipo
        
        if melhor_match:
            print(f"   ✅ '{item_busca}' → '{melhor_match['nome']}'")
            print(f"      Score: {melhor_score:.0%} | Tipo: {melhor_tipo}")
            if melhor_match['preco']:
                print(f"      Preço: {melhor_match['preco']} V-Bucks")
            print()
            
            resultados.append({
                'nome': item_busca,
                'encontrado': True,
                'preco': f"{melhor_match['preco']} V-Bucks" if melhor_match['preco'] else "Preço não detectado",
                'preco_num': melhor_match['preco'],
                'nome_completo': melhor_match['nome'],
                'score': melhor_score,
                'tipo_match': melhor_tipo
            })
        else:
            print(f"   ❌ '{item_busca}' não encontrado")
            
            # Mostra itens similares (pode ajudar a debugar)
            similares = []
            for item_loja in itens_loja:
                sim = similaridade_strings(item_busca, item_loja['nome'])
                if sim >= 0.4:  # 40% de similaridade
                    similares.append((item_loja['nome'], sim))
            
            if similares:
                similares.sort(key=lambda x: x[1], reverse=True)
                print(f"      Itens similares encontrados:")
                for nome_sim, score_sim in similares[:3]:
                    print(f"         • {nome_sim} ({score_sim:.0%})")
            print()
            
            resultados.append({
                'nome': item_busca,
                'encontrado': False,
                'preco': None,
                'preco_num': None,
                'nome_completo': '',
                'score': 0.0,
                'tipo_match': None
            })
    
    return resultados

def salvar_lista_loja(itens_loja, arquivo='loja_fortnite_completa.txt'):
    """Salva lista completa da loja para referência"""
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("LISTA COMPLETA DA LOJA FORTNITE\n")
            f.write(f"Data: {obter_horario_brasilia()}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, item in enumerate(itens_loja, 1):
                preco_str = f"{item['preco']} V-Bucks" if item['preco'] else "Sem preço"
                f.write(f"{i}. {item['nome']} - {preco_str}\n")
        
        print(f"   💾 Lista completa salva em: {arquivo}\n")
    except Exception as e:
        print(f"   ⚠️ Erro ao salvar lista: {e}\n")

# ========================================
# EMAIL, DISPLAY E MAIN
# ========================================

def criar_html_email(resultados, agora):
    """Cria HTML do email - versão simplificada"""
    
    encontrados = sum(1 for r in resultados if r['encontrado'])
    nao_encontrados = len(resultados) - encontrados
    total_vbucks = sum(r.get('preco_num', 0) for r in resultados if r['encontrado'] and r.get('preco_num'))
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #0A1628 0%, #1A2F4F 50%, #0D1B2A 100%);
                padding: 10px;
                min-height: 100vh;
            }}
            
            .email-wrapper {{
                max-width: 800px;
                margin: 0 auto;
                background: linear-gradient(180deg, #1e3a5f 0%, #0f1f38 100%);
                border: 4px solid #00D9FF;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            }}
            
            .header {{
                background: linear-gradient(135deg, #00D9FF 0%, #0088CC 100%);
                padding: 35px 25px;
                text-align: center;
            }}
            
            .header h1 {{
                color: white;
                font-size: 42px;
                margin: 0 0 10px 0;
                text-shadow: 3px 3px 0px #0066AA;
            }}
            
            .header p {{
                color: #E0F7FF;
                font-size: 16px;
            }}
            
            .stats {{
                background: rgba(0, 0, 0, 0.3);
                padding: 30px 25px;
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
            }}
            
            .stat-box {{
                background: linear-gradient(135deg, #1a3a5f 0%, #0f2847 100%);
                border-radius: 15px;
                padding: 30px 20px;
                text-align: center;
                border: 4px solid;
            }}
            
            .stat-box.verde {{ border-color: #00FF85; }}
            .stat-box.vermelho {{ border-color: #FF3366; }}
            .stat-box.amarelo {{ border-color: #FFD700; }}
            
            .stat-icon {{ font-size: 48px; margin-bottom: 12px; }}
            
            .stat-number {{
                font-size: 56px;
                font-weight: bold;
                margin: 12px 0;
            }}
            
            .stat-number.verde {{ color: #00FF85; }}
            .stat-number.vermelho {{ color: #FF3366; }}
            .stat-number.amarelo {{ color: #FFD700; font-size: 42px; }}
            
            .stat-label {{
                font-size: 13px;
                color: #B0C4DE;
                text-transform: uppercase;
                font-weight: bold;
            }}
            
            .items {{ padding: 30px 25px; }}
            
            .item {{
                background: linear-gradient(135deg, #1e3a5f 0%, #122841 100%);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 15px;
                border: 4px solid;
            }}
            
            .item.verde {{ border-color: #00FF85; }}
            .item.vermelho {{ border-color: #FF3366; opacity: 0.7; }}
            
            .item-top {{
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }}
            
            .item-numero {{
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, #00D9FF, #0088CC);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 24px;
                margin-right: 15px;
            }}
            
            .item-texto {{ flex: 1; }}
            
            .item-nome {{
                color: white;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            
            .item-sub {{
                color: #B0C4DE;
                font-size: 14px;
            }}
            
            .item-bottom {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 12px;
            }}
            
            .badge {{
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            
            .badge.verde {{
                background: linear-gradient(135deg, #00FF85, #00CC6A);
                color: #003D1F;
            }}
            
            .badge.vermelho {{
                background: linear-gradient(135deg, #FF3366, #CC0033);
                color: white;
            }}
            
            .preco {{
                background: linear-gradient(135deg, #FFD700, #FFA500);
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 18px;
            }}
            
            .botao-container {{
                background: rgba(0, 0, 0, 0.3);
                padding: 40px 25px;
                text-align: center;
            }}
            
            .botao {{
                display: inline-block;
                background: linear-gradient(135deg, #00D9FF 0%, #0088CC 100%);
                color: white;
                text-decoration: none;
                padding: 22px 60px;
                border-radius: 35px;
                font-weight: bold;
                font-size: 20px;
                text-transform: uppercase;
                border: 4px solid #00FFFF;
            }}
            
            .footer {{
                background: rgba(0,0,0,0.5);
                padding: 25px;
                text-align: center;
                color: #B0C4DE;
                font-size: 13px;
                border-top: 3px solid #00D9FF;
            }}
            
            @media only screen and (max-width: 600px) {{
                body {{ padding: 5px; }}
                .header h1 {{ font-size: 22px; }}
                .stats {{ grid-template-columns: 1fr; gap: 10px; padding: 15px 12px; }}
                .stat-number {{ font-size: 32px; }}
                .item {{ padding: 12px; }}
                .item-nome {{ font-size: 14px; }}
                .botao {{ padding: 15px 35px; font-size: 14px; width: 100%; }}
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <h1>🎮 FORTNITE SHOP 🛒</h1>
                <p>📅 {agora}</p>
            </div>
            
            <div class="stats">
                <div class="stat-box verde">
                    <div class="stat-icon">✅</div>
                    <div class="stat-number verde">{encontrados}</div>
                    <div class="stat-label">Encontrados</div>
                </div>
                
                <div class="stat-box vermelho">
                    <div class="stat-icon">❌</div>
                    <div class="stat-number vermelho">{nao_encontrados}</div>
                    <div class="stat-label">Ausentes</div>
                </div>
                
                <div class="stat-box amarelo">
                    <div class="stat-icon">💰</div>
                    <div class="stat-number amarelo">{total_vbucks:,}</div>
                    <div class="stat-label">Total V-Bucks</div>
                </div>
            </div>
            
            <div class="items">
    """
    
    for i, item in enumerate(resultados, 1):
        nome = item['nome']
        encontrado = item['encontrado']
        nome_completo = item.get('nome_completo', '')
        preco_num = item.get('preco_num')
        
        cor = "verde" if encontrado else "vermelho"
        status_icon = "✓" if encontrado else "✗"
        status_text = "Na Loja" if encontrado else "Ausente"
        
        display_name = nome_completo if nome_completo else nome
        subtitle = f"Nome na loja: {nome_completo}" if nome_completo and nome_completo != nome else f"Buscando: {nome}"
        
        html += f"""
                <div class="item {cor}">
                    <div class="item-top">
                        <div class="item-numero">{i}</div>
                        <div class="item-texto">
                            <div class="item-nome">{display_name}</div>
                            <div class="item-sub">{subtitle}</div>
                        </div>
                    </div>
                    <div class="item-bottom">
                        <span class="badge {cor}">{status_icon} {status_text}</span>
        """
        
        if encontrado and preco_num:
            html += f'<span class="preco">💎 {preco_num:,}</span>'
        
        html += """
                    </div>
                </div>
        """
    
    html += f"""
            </div>
            
            <div class="botao-container">
                <a href="{FORTNITE_SHOP_URL}" class="botao">🛒 VISITAR LOJA</a>
            </div>
            
            <div class="footer">
                <p><strong>Monitor Automático da Loja Fortnite</strong></p>
                <p>© 2025 | Sistema de Matching Inteligente</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def enviar_email(resultados, agora):
    """Envia email com o relatório"""
    try:
        print("\n📧 Preparando email...")
        
        msg = EmailMessage()
        encontrados = sum(1 for r in resultados if r['encontrado'])
        msg['Subject'] = f'🎮 Fortnite Shop - {encontrados} itens encontrados!'
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = ', '.join(DESTINATARIOS)
        
        html_content = criar_html_email(resultados, agora)
        msg.add_alternative(html_content, subtype='html')
        
        print("   📤 Enviando email...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_REMETENTE, SENHA_APP)
            smtp.send_message(msg)
        
        print("   ✅ Email enviado com sucesso!")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao enviar email: {str(e)}")
        return False

def salvar_screenshot(driver, nome="fortnite_loja.png"):
    try:
        driver.save_screenshot(nome)
        print(f"   📸 Screenshot salvo: {nome}")
    except:
        pass

def imprimir_cabecalho(agora):
    print("\n" + "="*100)
    print("🎮 MONITOR FORTNITE - VERSÃO ULTRA (Lista Completa + Matching Inteligente)".center(100))
    print("="*100)
    print(f"⏰ Verificação iniciada em: {agora}")
    print(f"🔍 Itens monitorados: {len(ITENS_MONITORAR)}")
    print("="*100 + "\n")

def imprimir_resultados(resultados):
    print("\n" + "="*100)
    print("📊 RESULTADOS FINAIS".center(100))
    print("="*100 + "\n")
    
    for i, item in enumerate(resultados, 1):
        nome = item['nome']
        encontrado = item['encontrado']
        preco = item['preco']
        nome_completo = item.get('nome_completo', '')
        
        print(f"[{i}/{len(resultados)}] {nome}")
        
        if encontrado:
            print(f"      ✅ ENCONTRADO!")
            if nome_completo and nome_completo != nome:
                print(f"      Nome na loja: {nome_completo}")
            print(f"      Preço: 💰 {preco}")
        else:
            print(f"      ❌ Não encontrado")
        
        print("-"*100)

def imprimir_resumo(resultados):
    encontrados = sum(1 for r in resultados if r['encontrado'])
    nao_encontrados = len(resultados) - encontrados
    
    print("\n" + "="*100)
    print("📈 RESUMO".center(100))
    print("="*100)
    print(f"✅ Encontrados: {encontrados}")
    print(f"❌ Não encontrados: {nao_encontrados}")
    print(f"📋 Total: {len(resultados)}")
    print("="*100 + "\n")

def main():
    agora = obter_horario_brasilia()
    
    imprimir_cabecalho(agora)
    
    print("🌐 Iniciando navegador...")
    driver = inicializar_driver_antidetect()
    
    try:
        print(f"🔗 Acessando: {FORTNITE_SHOP_URL}")
        driver.get(FORTNITE_SHOP_URL)
        
        if not aguardar_pagina_carregar(driver):
            print("⚠️ Timeout - tentando mesmo assim...")
        
        salvar_screenshot(driver, "fortnite_loja.png")
        
        # NOVA ESTRATÉGIA EM 2 PASSOS:
        # 1. Lista TODOS os itens da loja
        itens_loja = listar_todos_itens_da_loja(driver)
        
        # Salva lista completa para referência
        salvar_lista_loja(itens_loja)
        
        # 2. Busca os itens monitorados na lista
        resultados = buscar_itens_monitorados(itens_loja, ITENS_MONITORAR)
        
        imprimir_resultados(resultados)
        imprimir_resumo(resultados)
        
        enviar_email(resultados, agora)
        
        print("✅ Monitoramento concluído!")
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        salvar_screenshot(driver, "fortnite_erro.png")
    
    finally:
        print("🔒 Fechando navegador...")
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
