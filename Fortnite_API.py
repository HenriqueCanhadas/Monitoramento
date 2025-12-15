"""
MONITOR FORTNITE - VERSÃO COMPLETA COM EMAIL OTIMIZADO PARA MOBILE
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

# ========================================
# CONFIGURAÇÕES
# ========================================

ITENS_MONITORAR = [
O Batman Que Ri,
Superman,
Hatsune Miku,
V,
Johnny Silverhand,
Iron Man,
Darth Vader,
Darth Vader Samurai,
Stormtrooper Samurai,
Yuji Itadori,
Megumi Fushiguro,
Satoru Gojo,
Nobara Kugisaki,
Goku Black,
Eren Jaeger,
Mikasa Ackermann,
Captain Levi,
Son Goku,
Vegeta,
Bulma
]

# Configuração de Email
EMAIL_REMETENTE = os.getenv('EMAIL_APP_P')
SENHA_APP = os.getenv('SENHA_APP_P')
DESTINATARIOS = [EMAIL_REMETENTE]

FORTNITE_SHOP_URL = "https://www.fortnite.com/item-shop?lang=pt-BR"

# ========================================
# FUNÇÕES AUXILIARES (mantidas iguais)
# ========================================

def obter_horario_brasilia():
    try:
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    except:
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def normalizar_texto(texto):
    import unicodedata
    texto = texto.lower().strip()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto

def encontrar_card_correto(driver, elemento_titulo, nome_item):
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

def buscar_itens_na_loja(driver, itens_procurados):
    resultados = []
    itens_normalizados = {normalizar_texto(item): item for item in itens_procurados}
    
    print("\n🔍 Analisando loja do Fortnite...")
    
    try:
        elementos_titulo = driver.find_elements(By.CSS_SELECTOR, '[data-testid="item-title"]')
        print(f"   📄 Encontrados {len(elementos_titulo)} itens na loja\n")
        
        itens_info = {}
        
        for idx, elemento_titulo in enumerate(elementos_titulo):
            try:
                nome_item = elemento_titulo.text.strip()
                nome_normalizado = normalizar_texto(nome_item)
                
                for item_norm, item_original in itens_normalizados.items():
                    if item_norm in nome_normalizado:
                        if item_original in itens_info:
                            continue
                        
                        print(f"   🎯 ENCONTRADO: '{item_original}' → '{nome_item}'")
                        
                        card_element = encontrar_card_correto(driver, elemento_titulo, nome_item)
                        preco = extrair_preco_do_card(driver, card_element, nome_item)
                        
                        if preco:
                            itens_info[item_original] = {
                                'encontrado': True,
                                'preco': preco,
                                'nome_completo': nome_item
                            }
                            print(f"   ✅ {item_original} = {preco} V-Bucks\n")
                        else:
                            itens_info[item_original] = {
                                'encontrado': True,
                                'preco': None,
                                'nome_completo': nome_item
                            }
                            print(f"   ⚠️ Sem preço\n")
                        
            except:
                continue
        
        for item_original in itens_procurados:
            if item_original in itens_info:
                info = itens_info[item_original]
                preco_formatado = f"{info['preco']} V-Bucks" if info['preco'] else "Preço não detectado"
                
                resultados.append({
                    'nome': item_original,
                    'encontrado': True,
                    'preco': preco_formatado,
                    'preco_num': info['preco'],
                    'nome_completo': info.get('nome_completo', '')
                })
            else:
                resultados.append({
                    'nome': item_original,
                    'encontrado': False,
                    'preco': None,
                    'preco_num': None,
                    'nome_completo': ''
                })
        
    except Exception as e:
        print(f"⚠️ Erro ao buscar itens: {str(e)}")
        import traceback
        traceback.print_exc()
        
        for item in itens_procurados:
            resultados.append({
                'nome': item,
                'encontrado': False,
                'preco': None,
                'preco_num': None,
                'nome_completo': ''
            })
    
    return resultados

# ========================================
# FUNÇÕES DE EMAIL - OTIMIZADO PARA MOBILE
# ========================================

def criar_html_email(resultados, agora):
    """Cria HTML ultra-otimizado para email mobile E desktop"""
    
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
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: repeating-linear-gradient(
                    45deg,
                    transparent,
                    transparent 10px,
                    rgba(255,255,255,0.05) 10px,
                    rgba(255,255,255,0.05) 20px
                );
            }}
            
            .header h1 {{
                color: white;
                font-size: 42px;
                margin: 0 0 10px 0;
                text-shadow: 3px 3px 0px #0066AA, 5px 5px 0px rgba(0,0,0,0.3);
                position: relative;
                z-index: 1;
                letter-spacing: 2px;
            }}
            
            .header p {{
                color: #E0F7FF;
                font-size: 16px;
                margin: 0;
                position: relative;
                z-index: 1;
                font-weight: 600;
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
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            
            .stat-box:hover {{
                transform: translateY(-5px);
            }}
            
            .stat-box.verde {{ 
                border-color: #00FF85; 
                background: linear-gradient(135deg, #0a3d2e 0%, #051f1a 100%);
            }}
            
            .stat-box.verde:hover {{
                box-shadow: 0 10px 30px rgba(0,255,133,0.3);
            }}
            
            .stat-box.vermelho {{ 
                border-color: #FF3366; 
                background: linear-gradient(135deg, #3d0a1e 0%, #1f0510 100%);
            }}
            
            .stat-box.vermelho:hover {{
                box-shadow: 0 10px 30px rgba(255,51,102,0.3);
            }}
            
            .stat-box.amarelo {{ 
                border-color: #FFD700; 
                background: linear-gradient(135deg, #3d2f0a 0%, #1f1705 100%);
            }}
            
            .stat-box.amarelo:hover {{
                box-shadow: 0 10px 30px rgba(255,215,0,0.3);
            }}
            
            .stat-icon {{ 
                font-size: 48px; 
                margin-bottom: 12px;
                filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
            }}
            
            .stat-number {{
                font-size: 56px;
                font-weight: bold;
                margin: 12px 0;
                line-height: 1;
                text-shadow: 3px 3px 0px rgba(0,0,0,0.3);
            }}
            
            .stat-number.verde {{ color: #00FF85; }}
            .stat-number.vermelho {{ color: #FF3366; }}
            .stat-number.amarelo {{ 
                color: #FFD700; 
                font-size: 42px; 
            }}
            
            .stat-label {{
                font-size: 13px;
                color: #B0C4DE;
                text-transform: uppercase;
                font-weight: bold;
                letter-spacing: 1.5px;
            }}
            
            .items {{
                padding: 30px 25px;
            }}
            
            .item {{
                background: linear-gradient(135deg, #1e3a5f 0%, #122841 100%);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 15px;
                border: 4px solid;
                transition: all 0.3s ease;
            }}
            
            .item:hover {{
                transform: translateX(5px);
            }}
            
            .item.verde {{ 
                border-color: #00FF85; 
                background: linear-gradient(135deg, #0f3d2e 0%, #0a2820 100%);
            }}
            
            .item.verde:hover {{
                box-shadow: 0 8px 25px rgba(0,255,133,0.2);
            }}
            
            .item.vermelho {{ 
                border-color: #FF3366;
                opacity: 0.7;
            }}
            
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
                flex-shrink: 0;
                margin-right: 15px;
                box-shadow: 0 6px 15px rgba(0,217,255,0.4);
                text-shadow: 2px 2px 0px rgba(0,0,0,0.3);
            }}
            
            .item-texto {{
                flex: 1;
                min-width: 0;
            }}
            
            .item-nome {{
                color: white;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 5px;
                word-wrap: break-word;
                line-height: 1.3;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }}
            
            .item-sub {{
                color: #B0C4DE;
                font-size: 14px;
                word-wrap: break-word;
                line-height: 1.4;
            }}
            
            .item-bottom {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 12px;
            }}
            
            .badge {{
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
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
                box-shadow: 0 4px 15px rgba(255,215,0,0.4);
                text-shadow: 2px 2px 0px rgba(0,0,0,0.3);
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
                letter-spacing: 2px;
                box-shadow: 0 8px 25px rgba(0,217,255,0.5);
                transition: all 0.3s ease;
                text-shadow: 2px 2px 0px rgba(0,0,0,0.3);
            }}
            
            .botao:hover {{
                background: linear-gradient(135deg, #00FFFF 0%, #00D9FF 100%);
                box-shadow: 0 10px 35px rgba(0,255,255,0.7);
                transform: translateY(-3px);
            }}
            
            .footer {{
                background: rgba(0,0,0,0.5);
                padding: 25px;
                text-align: center;
                color: #B0C4DE;
                font-size: 13px;
                border-top: 3px solid #00D9FF;
            }}
            
            .footer p {{ 
                margin: 6px 0; 
                line-height: 1.6;
            }}
            
            .footer strong {{ 
                color: #00D9FF; 
                font-weight: 700;
            }}
            
            /* ============================================ */
            /* RESPONSIVIDADE PARA MOBILE */
            /* ============================================ */
            @media only screen and (max-width: 600px) {{
                body {{
                    padding: 5px;
                }}
                
                .email-wrapper {{
                    border-radius: 12px;
                    border-width: 3px;
                    max-width: 100%;
                }}
                
                .header {{
                    padding: 20px 15px;
                }}
                
                .header h1 {{
                    font-size: 22px;
                }}
                
                .header p {{
                    font-size: 11px;
                }}
                
                .stats {{
                    grid-template-columns: 1fr;
                    gap: 10px;
                    padding: 15px 12px;
                }}
                
                .stat-box {{
                    padding: 15px 10px;
                }}
                
                .stat-icon {{
                    font-size: 28px;
                }}
                
                .stat-number {{
                    font-size: 32px;
                }}
                
                .stat-number.amarelo {{
                    font-size: 24px;
                }}
                
                .stat-label {{
                    font-size: 10px;
                }}
                
                .items {{
                    padding: 15px 12px;
                }}
                
                .item {{
                    padding: 12px;
                    margin-bottom: 10px;
                }}
                
                .item-numero {{
                    width: 36px;
                    height: 36px;
                    font-size: 18px;
                }}
                
                .item-nome {{
                    font-size: 14px;
                }}
                
                .item-sub {{
                    font-size: 10px;
                }}
                
                .badge {{
                    padding: 6px 12px;
                    font-size: 10px;
                }}
                
                .preco {{
                    padding: 6px 12px;
                    font-size: 12px;
                }}
                
                .botao-container {{
                    padding: 20px 15px;
                }}
                
                .botao {{
                    padding: 15px 35px;
                    font-size: 14px;
                    width: 100%;
                    max-width: 300px;
                }}
            }}
            
            /* ============================================ */
            /* RESPONSIVIDADE PARA DESKTOP/TABLET */
            /* ============================================ */
            @media only screen and (min-width: 601px) and (max-width: 900px) {{
                .email-wrapper {{
                    max-width: 700px;
                }}
                
                .header h1 {{
                    font-size: 36px;
                }}
                
                .stat-number {{
                    font-size: 48px;
                }}
                
                .stat-number.amarelo {{
                    font-size: 36px;
                }}
            }}
            
            /* ============================================ */
            /* AJUSTE PARA TELAS MUITO PEQUENAS */
            /* ============================================ */
            @media only screen and (max-width: 375px) {{
                .header h1 {{
                    font-size: 20px;
                }}
                
                .stat-number {{
                    font-size: 28px;
                }}
                
                .stat-number.amarelo {{
                    font-size: 20px;
                }}
                
                .item-nome {{
                    font-size: 13px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <!-- Header -->
            <div class="header">
                <h1>🎮 FORTNITE SHOP 🛒</h1>
                <p>📅 Atualizado em {agora}</p>
            </div>
            
            <!-- Stats -->
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
            
            <!-- Items -->
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
        
        display_name = nome_completo if nome_completo and nome_completo != nome else nome
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
            html += f"""
                        <span class="preco">💎 {preco_num:,}</span>
        """
        
        html += """
                    </div>
                </div>
        """
    
    html += f"""
            </div>
            
            <!-- Botão -->
            <div class="botao-container">
                <a href="{FORTNITE_SHOP_URL}" class="botao">
                    🛒 VISITAR LOJA
                </a>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <p><strong>Monitor Automático da Loja Fortnite</strong></p>
                <p>Desenvolvido com 💙 | © 2025</p>
                <p>Fique de olho nos seus itens favoritos! 🎯</p>
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
        msg['Subject'] = f'🎮 Fortnite Shop Alert - {encontrados} itens encontrados!'
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
        import traceback
        traceback.print_exc()
        return False

def salvar_screenshot(driver, nome="fortnite_loja.png"):
    try:
        driver.save_screenshot(nome)
        print(f"   📸 Screenshot salvo: {nome}")
    except:
        pass

# ========================================
# FUNÇÕES DE EXIBIÇÃO
# ========================================

def imprimir_cabecalho(agora):
    print("\n" + "="*100)
    print("🎮 MONITOR DA LOJA FORTNITE - VERSÃO COMPLETA".center(100))
    print("="*100)
    print(f"⏰ Verificação iniciada em: {agora}")
    print(f"🔍 Itens monitorados: {len(ITENS_MONITORAR)}")
    print("="*100 + "\n")

def imprimir_resultados(resultados):
    print("\n" + "="*100)
    print("📊 RESULTADOS DA BUSCA".center(100))
    print("="*100 + "\n")
    
    for i, item in enumerate(resultados, 1):
        nome = item['nome']
        encontrado = item['encontrado']
        preco = item['preco']
        nome_completo = item.get('nome_completo', '')
        
        print(f"[{i}/{len(resultados)}] {nome}")
        
        if encontrado:
            print(f"      Status: ✅ ENCONTRADO NA LOJA!")
            if nome_completo and nome_completo.lower() != nome.lower():
                print(f"      Nome na loja: {nome_completo}")
            print(f"      Preço: 💰 {preco}")
        else:
            print(f"      Status: ❌ Não está na loja hoje")
        
        print("-"*100)

def imprimir_resumo(resultados):
    encontrados = sum(1 for r in resultados if r['encontrado'])
    nao_encontrados = len(resultados) - encontrados
    
    print("\n" + "="*100)
    print("📈 RESUMO".center(100))
    print("="*100)
    print(f"✅ Itens encontrados: {encontrados}")
    print(f"❌ Itens não encontrados: {nao_encontrados}")
    print(f"📋 Total verificado: {len(resultados)}")
    print("="*100 + "\n")

# ========================================
# FUNÇÃO PRINCIPAL
# ========================================

def main():
    agora = obter_horario_brasilia()
    
    imprimir_cabecalho(agora)
    
    print("🌐 Iniciando navegador com proteção anti-detecção...")
    driver = inicializar_driver_antidetect()
    
    try:
        print(f"🔗 Acessando: {FORTNITE_SHOP_URL}")
        driver.get(FORTNITE_SHOP_URL)
        
        if not aguardar_pagina_carregar(driver):
            print("⚠️ Timeout ao aguardar página - tentando buscar mesmo assim...")
        
        salvar_screenshot(driver, "fortnite_loja.png")
        
        resultados = buscar_itens_na_loja(driver, ITENS_MONITORAR)
        
        imprimir_resultados(resultados)
        imprimir_resumo(resultados)
        
        enviar_email(resultados, agora)
        
        print("✅ Monitoramento concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante a execução: {str(e)}")
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
