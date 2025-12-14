"""
MONITOR FORTNITE - VERSÃO API OFICIAL
Usa a Fortnite-API.com para buscar itens da loja
"""

import requests
import smtplib
from email.message import EmailMessage
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from typing import List, Dict, Optional

# ========================================
# CONFIGURAÇÕES
# ========================================

# Email
EMAIL_REMETENTE = os.getenv('EMAIL_APP_P')
SENHA_APP = os.getenv('SENHA_APP_P')
DESTINATARIOS = [EMAIL_REMETENTE]

# Fortnite API (opcional - funciona sem key também)
FORTNITE_API_KEY = os.getenv('FORTNITE_API_KEY', '')

# Itens para monitorar
ITENS_MONITORAR = [
    "Vegeta",
    "Goku",
    "Desentupidor",
    "Skibidi Toilet",
    "Naruto",
    "Kratos",
    "Master Chief"
]

# URLs
FORTNITE_SHOP_URL = "https://www.fortnite.com/item-shop?lang=pt-BR"
FORTNITE_API_URL = "https://fortnite-api.com/v2/shop/br"

# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def obter_horario_brasilia():
    """Retorna o horário atual de Brasília formatado"""
    try:
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    except:
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparação"""
    import unicodedata
    texto = texto.lower().strip()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto

def buscar_loja_fortnite() -> Optional[Dict]:
    """Busca a loja atual do Fortnite via API"""
    
    print("🌐 Conectando à Fortnite API...")
    
    headers = {}
    if FORTNITE_API_KEY:
        headers['Authorization'] = FORTNITE_API_KEY
    
    try:
        response = requests.get(FORTNITE_API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 200:
            print(f"   ✅ API conectada com sucesso!")
            return data.get('data', {})
        else:
            print(f"   ❌ Erro na API: {data.get('error', 'Desconhecido')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erro ao conectar na API: {e}")
        return None

def extrair_itens_da_loja(loja_data: Dict) -> List[Dict]:
    """Extrai itens da resposta da API"""
    
    itens = []
    
    # A API retorna os itens em diferentes seções
    sections = [
        loja_data.get('featured', {}),
        loja_data.get('daily', {}),
        loja_data.get('specialFeatured', {}),
        loja_data.get('specialDaily', {}),
    ]
    
    for section in sections:
        entries = section.get('entries', [])
        
        for entry in entries:
            # Pega informações do bundle ou do item individual
            bundle = entry.get('bundle')
            items = entry.get('items', [])
            
            if bundle:
                # É um bundle/pacote
                nome = bundle.get('name', '')
                preco = entry.get('finalPrice', 0)
                
                if nome:
                    itens.append({
                        'nome': nome,
                        'preco': preco,
                        'tipo': 'bundle'
                    })
            
            # Itens individuais dentro do entry
            for item in items:
                nome = item.get('name', '')
                preco = entry.get('finalPrice', 0)
                
                if nome:
                    itens.append({
                        'nome': nome,
                        'preco': preco,
                        'tipo': 'item'
                    })
    
    return itens

def buscar_itens_monitorados(itens_loja: List[Dict], itens_procurados: List[str]) -> List[Dict]:
    """Busca os itens monitorados na loja"""
    
    print(f"\n🔍 Analisando {len(itens_loja)} itens da loja...")
    
    resultados = []
    itens_normalizados = {normalizar_texto(item): item for item in itens_procurados}
    itens_encontrados = {}
    
    # Busca cada item
    for item_loja in itens_loja:
        nome_loja = item_loja['nome']
        nome_normalizado = normalizar_texto(nome_loja)
        
        # Verifica se algum item monitorado está neste nome
        for item_norm, item_original in itens_normalizados.items():
            if item_norm in nome_normalizado:
                # Evita duplicatas
                if item_original not in itens_encontrados:
                    itens_encontrados[item_original] = {
                        'encontrado': True,
                        'preco': item_loja['preco'],
                        'nome_completo': nome_loja,
                        'tipo': item_loja['tipo']
                    }
                    print(f"   🎯 ENCONTRADO: '{item_original}' → '{nome_loja}' ({item_loja['preco']} V-Bucks)")
    
    # Monta resultados finais
    for item_original in itens_procurados:
        if item_original in itens_encontrados:
            info = itens_encontrados[item_original]
            resultados.append({
                'nome': item_original,
                'encontrado': True,
                'preco': f"{info['preco']} V-Bucks",
                'preco_num': info['preco'],
                'nome_completo': info['nome_completo']
            })
        else:
            resultados.append({
                'nome': item_original,
                'encontrado': False,
                'preco': None,
                'preco_num': None,
                'nome_completo': ''
            })
            print(f"   ❌ NÃO ENCONTRADO: '{item_original}'")
    
    return resultados

def criar_html_email(resultados, agora):
    """Cria HTML do email (mesma função anterior)"""
    
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
            
            .header h1 {{
                color: white;
                font-size: 42px;
                margin: 0 0 10px 0;
                text-shadow: 3px 3px 0px #0066AA;
                position: relative;
                z-index: 1;
            }}
            
            .header p {{
                color: #E0F7FF;
                font-size: 16px;
                margin: 0;
                position: relative;
                z-index: 1;
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
            
            .stat-box.verde {{ border-color: #00FF85; background: linear-gradient(135deg, #0a3d2e 0%, #051f1a 100%); }}
            .stat-box.vermelho {{ border-color: #FF3366; background: linear-gradient(135deg, #3d0a1e 0%, #1f0510 100%); }}
            .stat-box.amarelo {{ border-color: #FFD700; background: linear-gradient(135deg, #3d2f0a 0%, #1f1705 100%); }}
            
            .stat-icon {{ font-size: 48px; margin-bottom: 12px; }}
            .stat-number {{ font-size: 56px; font-weight: bold; margin: 12px 0; line-height: 1; }}
            .stat-number.verde {{ color: #00FF85; }}
            .stat-number.vermelho {{ color: #FF3366; }}
            .stat-number.amarelo {{ color: #FFD700; font-size: 42px; }}
            .stat-label {{ font-size: 13px; color: #B0C4DE; text-transform: uppercase; font-weight: bold; }}
            
            .items {{ padding: 30px 25px; }}
            
            .item {{
                background: linear-gradient(135deg, #1e3a5f 0%, #122841 100%);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 15px;
                border: 4px solid;
            }}
            
            .item.verde {{ border-color: #00FF85; background: linear-gradient(135deg, #0f3d2e 0%, #0a2820 100%); }}
            .item.vermelho {{ border-color: #FF3366; opacity: 0.7; }}
            
            .item-top {{ display: flex; align-items: center; margin-bottom: 15px; }}
            
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
            .item-nome {{ color: white; font-size: 20px; font-weight: bold; margin-bottom: 5px; }}
            .item-sub {{ color: #B0C4DE; font-size: 14px; }}
            
            .item-bottom {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; }}
            
            .badge {{
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            
            .badge.verde {{ background: linear-gradient(135deg, #00FF85, #00CC6A); color: #003D1F; }}
            .badge.vermelho {{ background: linear-gradient(135deg, #FF3366, #CC0033); color: white; }}
            
            .preco {{
                background: linear-gradient(135deg, #FFD700, #FFA500);
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 18px;
            }}
            
            .botao-container {{ background: rgba(0, 0, 0, 0.3); padding: 40px 25px; text-align: center; }}
            
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
            }}
            
            .footer p {{ margin: 6px 0; }}
            .footer strong {{ color: #00D9FF; }}
            
            /* Mobile */
            @media only screen and (max-width: 600px) {{
                .stats {{ grid-template-columns: 1fr; gap: 10px; padding: 15px; }}
                .stat-number {{ font-size: 32px; }}
                .stat-number.amarelo {{ font-size: 24px; }}
                .item-nome {{ font-size: 14px; }}
                .header h1 {{ font-size: 22px; }}
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="header">
                <h1>🎮 FORTNITE SHOP 🛒</h1>
                <p>📅 Atualizado em {agora}</p>
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
                <p><strong>Monitor Automático da Loja Fortnite (API Version)</strong></p>
                <p>Desenvolvido com 💙 | © 2025</p>
                <p>Powered by Fortnite-API.com 🚀</p>
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
        return False

def imprimir_cabecalho(agora):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*100)
    print("🎮 MONITOR DA LOJA FORTNITE - VERSÃO API".center(100))
    print("="*100)
    print(f"⏰ Verificação iniciada em: {agora}")
    print(f"🔍 Itens monitorados: {len(ITENS_MONITORAR)}")
    print("="*100 + "\n")

def imprimir_resultados(resultados):
    """Imprime resultados formatados"""
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
    """Imprime resumo final"""
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
    """Função principal do monitor"""
    agora = obter_horario_brasilia()
    
    imprimir_cabecalho(agora)
    
    # Busca loja via API
    loja_data = buscar_loja_fortnite()
    
    if not loja_data:
        print("❌ Não foi possível obter dados da loja. Abortando...")
        return
    
    # Extrai itens
    itens_loja = extrair_itens_da_loja(loja_data)
    print(f"   📦 Total de itens extraídos: {len(itens_loja)}")
    
    # Busca itens monitorados
    resultados = buscar_itens_monitorados(itens_loja, ITENS_MONITORAR)
    
    # Exibe resultados
    imprimir_resultados(resultados)
    imprimir_resumo(resultados)
    
    # Envia email
    enviar_email(resultados, agora)
    
    print("✅ Monitoramento concluído!")

if __name__ == "__main__":
    main()
