from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re
from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib
from email.message import EmailMessage
import os
from supabase import create_client, Client

# ========================================
# CONFIGURAÇÕES VIA VARIÁVEIS DE AMBIENTE
# ========================================

# Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# Email
EMAIL_REMETENTE = os.environ.get('EMAIL_APP_P')
SENHA_APP = os.environ.get('SENHA_APP_P')

# Validar variáveis obrigatórias
required_vars = {
    'SUPABASE_URL': SUPABASE_URL,
    'SUPABASE_KEY': SUPABASE_KEY,
    'EMAIL_APP_P': EMAIL_REMETENTE,
    'SENHA_APP_P': SENHA_APP
}

# Inicializar Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Conexão com Supabase estabelecida")
except Exception as e:
    print(f"❌ Erro ao conectar com Supabase: {e}")
    exit(1)

# Destinatários (usa o mesmo email do remetente)
DESTINATARIOS = [EMAIL_REMETENTE]

# Produtos a monitorar (LISTA COMPLETA - 14 produtos)
PRODUTOS = [
    {
        "product_key": "kabum-1",
        "url": "https://www.kabum.com.br/produto/461173/cabo-em-espiral-para-teclado-hyperx-usb-c-para-usb-a-1-20m-azul-6j680aa",
        "preco_estimado": 75.00
    },
    {
        "product_key": "kabum-2",
        "url": "https://www.kabum.com.br/produto/95803/hd-interno-seagate-barracuda-4tb-sata-3-5-st4000dm004",
        "preco_estimado": 650.00
    },
    {
        "product_key": "kabum-3",
        "url": "https://www.kabum.com.br/produto/128256/hd-interno-seagate-barracuda-8tb-3-5-sata-st8000dm004",
        "preco_estimado": 950.00
    },
    {
        "product_key": "kabum-4",
        "url": "https://www.kabum.com.br/produto/451197/caixa-de-som-gamer-rise-mode-aura-sound-s5-rgb-bluetooth-3wx2-preto-rm-sp-05-rgb",
        "preco_estimado": 65.00
    },
    {
        "product_key": "kabum-5",
        "url": "https://www.kabum.com.br/produto/451195/caixa-de-som-gamer-rise-mode-aura-sound-s3-rgb-rainbow-3w-2-preto-rm-sp-03-rgb",
        "preco_estimado": 50.00
    },
    {
        "product_key": "kabum-6",
        "url": "https://www.kabum.com.br/produto/527400/console-playstation-5-slim-sony-ssd-1tb-com-controle-sem-fio-dualsense-branco-2-jogos-1000038899",
        "preco_estimado": 3300.00
    },
    {
        "product_key": "kabum-7",
        "url": "https://www.kabum.com.br/produto/875817/console-sony-playstation-5-slim-com-leitor-de-discos-ssd-1tb-controle-sem-fio-dualsense-2-jogos-1000038858",
        "preco_estimado": 3300.00
    },
    {
        "product_key": "kabum-8",
        "url": "https://www.kabum.com.br/produto/922661/console-sony-playstation-5-com-leitor-de-discos-ssd-1tb-controle-sem-fio-dualsense-2-jogos-1000050613",
        "preco_estimado": 3300.00
    },
    {
        "product_key": "kabum-15",
        "url": "https://www.kabum.com.br/produto/934759/console-sony-playstation-5-com-leitor-de-discos-ssd-1tb-controle-sem-fio-dualsense-2-jogos",
        "preco_estimado": 3300.00
    },
    {
        "product_key": "kabum-16",
        "url": "https://www.kabum.com.br/produto/922661/console-sony-playstation-5-com-leitor-de-discos-ssd-1tb-controle-sem-fio-dualsense-2-jogos-1000050613",
        "preco_estimado": 3300.00
    },
    {
        "product_key": "kabum-17",
        "url": "https://www.kabum.com.br/produto/636960/console-playstation-5-pro-sony-ssd-2tb-com-controle-sem-fio-dualsense-branco-1000046552",
        "preco_estimado": 5000.00
    },
    {
        "product_key": "kabum-9",
        "url": "https://www.kabum.com.br/produto/316365/cartao-de-memoria-sandisk-ultra-microsd-uhs-i-128gb-100mb-s-com-adaptador-sdsqunr-128g-gn3ma",
        "preco_estimado": 55.00
    },
    {
        "product_key": "kabum-10",
        "url": "https://www.kabum.com.br/produto/111807/cartao-de-memoria-kingston-microsd-de-128gb-canvas-select-plus-100mb-s-classe-10-com-adaptador-sd-sdcs2-128gb",
        "preco_estimado": 55.00
    },
    {
        "product_key": "kabum-11",
        "url": "https://www.kabum.com.br/produto/728163/cartao-de-memoria-sandisk-creator-series-microsd-128gb-classe-10-leitura-190-mb-s-e-gravacao-90-mb-s-sdsqxaa-128g-gn6ms",
        "preco_estimado": 130.00
    },
    {
        "product_key": "kabum-12",
        "url": "https://www.kabum.com.br/produto/728162/cartao-de-memoria-sandisk-creator-series-microsd-256gb-classe-10-leitura-190-mb-s-e-gravacao-130-mb-s-sdsqxav-256g-gn6ms",
        "preco_estimado": 200.00
    },
    {
        "product_key": "kabum-13",
        "url": "https://www.kabum.com.br/produto/111808/cartao-de-memoria-kingston-microsd-de-256gb-canvas-select-plus-100mb-s-classe-10-com-adaptador-sd-sdcs2-256gb",
        "preco_estimado": 120.00
    },
    {
        "product_key": "kabum-14",
        "url": "https://www.kabum.com.br/produto/728161/cartao-de-memoria-sandisk-creator-series-microsd-512gb-classe-10-leitura-190-mb-s-e-gravacao-130-mb-s-sdsqxav-512g-gn6ms",
        "preco_estimado": 330.00
    },
]

# ========================================
# FUNÇÕES AUXILIARES
# ========================================

def obter_horario_brasilia():
    """Retorna o horário atual de Brasília formatado para exibição"""
    try:
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
    except:
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def obter_horario_brasilia_iso():
    """Retorna o horário atual de Brasília em formato compatível com PostgreSQL (sem timezone)"""
    try:
        return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S.%f")
    except:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def converter_utc_para_brasilia(data_utc_str):
    """Converte data UTC do banco para horário de Brasília formatado"""
    try:
        data_utc = datetime.fromisoformat(data_utc_str.replace('Z', '+00:00'))
        data_brasilia = data_utc.astimezone(ZoneInfo("America/Sao_Paulo"))
        return data_brasilia.strftime("%d/%m/%Y %H:%M:%S")
    except:
        return data_utc_str

def formatar_nome_produto(url):
    """Extrai e formata o nome do produto da URL"""
    nome = url.split('/')[-1]
    partes = nome.split('-')
    
    if partes and partes[0].isdigit():
        partes.pop(0)
    
    nome_formatado = ' '.join(partes).replace('-', ' ').title()
    
    if len(nome_formatado) > 80:
        nome_formatado = nome_formatado[:77] + "..."
    
    return nome_formatado

def extrair_preco(texto):
    """Extrai o valor do preço do texto"""
    match = re.search(r'R\$\s*[\d.,]+', texto)
    return match.group(0) if match else None

def extrair_valor_numerico(preco_texto):
    """Converte texto de preço em valor numérico"""
    if not preco_texto:
        return None
    
    match = re.search(r'[\d.,]+', preco_texto)
    if match:
        valor = match.group(0).replace('.', '').replace(',', '.')
        try:
            return float(valor)
        except:
            return None
    return None

def calcular_diferenca_preco(preco_atual, preco_estimado):
    """Calcula a diferença percentual entre preços"""
    if preco_atual is None or preco_estimado is None:
        return None
    
    diferenca = ((preco_atual - preco_estimado) / preco_estimado) * 100
    return diferenca

def formatar_preco_brasileiro(valor):
    """Formata valor numérico para padrão brasileiro"""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def obter_menor_preco_historico(product_key):
    """Busca o menor preço histórico do banco de dados"""
    try:
        response = supabase.table("Menores Preços Kabum") \
            .select("preco_atual") \
            .eq("product_key", product_key) \
            .execute()
        
        if response.data and len(response.data) > 0:
            preco = response.data[0].get('preco_atual')
            return preco if preco is not None else None
        return None
    except Exception as e:
        print(f"⚠️ Erro ao buscar menor preço para {product_key}: {str(e)}")
        return None

# ========================================
# FUNÇÕES DE SCRAPING
# ========================================

def verificar_status_produto(driver):
    """Verifica o status do produto na página"""
    base_xpath = '//*[@id="main-content"]/div[1]/div[1]/div[1]/div[3]'
    
    for div_num in [1, 2, 3]:
        try:
            xpath = f'{base_xpath}/div[{div_num}]'
            elemento = driver.find_element(By.XPATH, xpath)
            texto = elemento.text.strip()
            
            if 'Ops! Produto esgotado' in texto or 'esgotado' in texto.lower():
                return ("esgotado", "Ops! Produto esgotado")
            
            try:
                h4_element = elemento.find_element(By.TAG_NAME, 'h4')
                preco_texto = h4_element.text.strip()
                preco = extrair_preco(preco_texto)
                if preco:
                    return ("disponivel", preco)
            except:
                pass
            
            preco = extrair_preco(texto)
            if preco:
                return ("disponivel", preco)
                
        except:
            continue
    
    return ("erro", "Erro ao verificar")

def inicializar_driver():
    """Inicializa o Chrome em modo headless"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    return webdriver.Chrome(options=chrome_options)

# ========================================
# FUNÇÕES DE PERSISTÊNCIA
# ========================================

def salvar_no_supabase(produtos_info):
    """Salva dados no Supabase - Tabela de Monitoramento (histórico completo)"""
    try:
        for produto in produtos_info:
            if produto["tipo"] == "disponivel":
                preco_atual = extrair_valor_numerico(produto["status"])
            elif produto["tipo"] == "esgotado":
                preco_atual = 0.00
            else:
                preco_atual = None
            
            data_coleta_iso = obter_horario_brasilia_iso()
            
            data = {
                "product_key": produto["product_key"],
                "nome": produto["nome"],
                "url": produto["url"],
                "preco_atual": preco_atual,
                "status": produto["tipo"],
                "data_coleta": data_coleta_iso
            }
            
            supabase.table("Monitoramento Kabum").insert(data).execute()
        
        print("✅ Dados salvos no Supabase (Monitoramento Kabum) com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar no Supabase: {str(e)}")
        return False

def atualizar_menores_precos(produtos_info):
    """
    Atualiza a tabela Menores Preços Kabum apenas com os menores preços históricos.
    """
    try:
        for produto in produtos_info:
            if produto["tipo"] == "disponivel":
                preco_atual = extrair_valor_numerico(produto["status"])
            else:
                preco_atual = None
            
            if preco_atual is None or preco_atual == 0.00:
                continue
            
            product_key = produto["product_key"]
            
            response = supabase.table("Menores Preços Kabum") \
                .select("*") \
                .eq("product_key", product_key) \
                .execute()
            
            data_coleta_iso = obter_horario_brasilia_iso()
            
            dados_produto = {
                "product_key": product_key,
                "nome": produto["nome"],
                "url": produto["url"],
                "preco_atual": preco_atual,
                "status": "disponivel",
                "data_coleta": data_coleta_iso
            }
            
            if len(response.data) == 0:
                supabase.table("Menores Preços Kabum").insert(dados_produto).execute()
                print(f"   ➕ {product_key}: Adicionado com preço {formatar_preco_brasileiro(preco_atual)}")
                
            else:
                registro_existente = response.data[0]
                preco_existente = registro_existente.get("preco_atual")
                
                if preco_existente is None or preco_atual < preco_existente:
                    supabase.table("Menores Preços Kabum") \
                        .update(dados_produto) \
                        .eq("product_key", product_key) \
                        .execute()
                    
                    if preco_existente is None:
                        print(f"   🔄 {product_key}: Atualizado (era None) → {formatar_preco_brasileiro(preco_atual)}")
                    else:
                        economia = preco_existente - preco_atual
                        economia_percent = (economia / preco_existente) * 100
                        print(f"   📉 {product_key}: MENOR PREÇO! {formatar_preco_brasileiro(preco_existente)} → {formatar_preco_brasileiro(preco_atual)} (economiza {formatar_preco_brasileiro(economia)} | -{economia_percent:.1f}%)")
                else:
                    print(f"   ⏸️ {product_key}: Mantido {formatar_preco_brasileiro(preco_existente)} (atual: {formatar_preco_brasileiro(preco_atual)})")
        
        print("\n✅ Tabela 'Menores Preços Kabum' atualizada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar 'Menores Preços Kabum': {str(e)}")
        return False

# ========================================
# FUNÇÕES DE EMAIL
# ========================================

def criar_html_email(produtos_info, disponiveis, esgotados, erros, agora):
    """Cria HTML do email com relatório completo"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
            }}
            .summary {{
                padding: 30px;
                background-color: #f8f9fa;
                border-bottom: 3px solid #e9ecef;
            }}
            .summary-table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 20px;
            }}
            .summary-table td {{
                width: 33.33%;
                vertical-align: top;
            }}
            .summary-item {{
                text-align: center;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                transition: transform 0.2s ease;
            }}
            .summary-item:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.12);
            }}
            .summary-item.disponivel-card {{
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border: 2px solid #28a745;
            }}
            .summary-item.esgotado-card {{
                background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                border: 2px solid #dc3545;
            }}
            .summary-item.erro-card {{
                background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%);
                border: 2px solid #ffc107;
            }}
            .summary-item .icon {{
                font-size: 32px;
                margin-bottom: 10px;
            }}
            .summary-item .number {{
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 8px;
                line-height: 1;
            }}
            .disponivel {{ color: #28a745; }}
            .esgotado {{ color: #dc3545; }}
            .erro {{ color: #ffc107; }}
            .summary-item .label {{
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1.2px;
            }}
            .table-container {{
                padding: 30px;
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            }}
            thead {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            th {{
                padding: 15px 10px;
                text-align: center;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                white-space: nowrap;
            }}
            th:nth-child(2) {{
                text-align: left;
            }}
            tbody tr {{
                border-bottom: 1px solid #e9ecef;
                transition: background-color 0.3s ease;
            }}
            tbody tr:hover {{ background-color: #f8f9fa; }}
            tbody tr:last-child {{ border-bottom: none; }}
            td {{
                padding: 15px 10px;
                font-size: 14px;
                text-align: center;
            }}
            td:nth-child(2) {{
                text-align: left;
            }}
            .produto-nome {{
                font-weight: 500;
                color: #2c3e50;
                max-width: 350px;
            }}
            .status {{
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                text-align: center;
                white-space: nowrap;
            }}
            .status.disponivel {{
                background-color: #d4edda;
                color: #155724;
            }}
            .status.esgotado {{
                background-color: #f8d7da;
                color: #721c24;
            }}
            .status.erro {{
                background-color: #fff3cd;
                color: #856404;
            }}
            .preco {{
                font-size: 18px;
                font-weight: bold;
                color: #28a745;
                white-space: nowrap;
            }}
            .preco-menor {{
                font-size: 16px;
                font-weight: bold;
                color: #007bff;
                white-space: nowrap;
            }}
            .preco-estimado {{
                font-size: 14px;
                font-weight: 500;
                color: #6c757d;
                white-space: nowrap;
            }}
            .diferenca {{
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                white-space: nowrap;
            }}
            .diferenca.positiva {{
                background-color: #d4edda;
                color: #155724;
            }}
            .diferenca.negativa {{
                background-color: #f8d7da;
                color: #721c24;
            }}
            .diferenca.neutro {{
                background-color: #e2e3e5;
                color: #383d41;
            }}
            .link {{
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                background-color: #f8f9fa;
                border: 1px solid #667eea;
                color: #667eea;
                text-decoration: none;
                font-size: 12px;
                font-weight: 600;
                transition: all 0.3s ease;
                white-space: nowrap;
            }}
            .link:hover {{
                background-color: #667eea;
                color: white;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
                font-size: 12px;
                border-top: 3px solid #e9ecef;
            }}
            .index {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                width: 42px;
                height: 42px;
                border-radius: 50%;
                display: inline-block;
                text-align: center;
                line-height: 42px;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
            }}
            .index-cell {{
                text-align: center;
                vertical-align: middle;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Relatório de Verificação - KaBuM!</h1>
                <p>📅 Verificação realizada em {agora}</p>
            </div>
            
            <div class="summary">
                <table class="summary-table" role="presentation" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        <td>
                            <div class="summary-item disponivel-card">
                                <div class="icon">✅</div>
                                <div class="number disponivel">{disponiveis}</div>
                                <div class="label">Disponíveis</div>
                            </div>
                        </td>
                        <td>
                            <div class="summary-item esgotado-card">
                                <div class="icon">❌</div>
                                <div class="number esgotado">{esgotados}</div>
                                <div class="label">Esgotados</div>
                            </div>
                        </td>
                        <td>
                            <div class="summary-item erro-card">
                                <div class="icon">⚠</div>
                                <div class="number erro">{erros}</div>
                                <div class="label">Erros</div>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ÍNDICE</th>
                            <th>PRODUTO</th>
                            <th>STATUS</th>
                            <th>PREÇO ATUAL</th>
                            <th>MENOR PREÇO</th>
                            <th>PREÇO ESTIMADO</th>
                            <th>DIFERENÇA</th>
                            <th>AÇÃO</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for i, produto in enumerate(produtos_info, 1):
        nome = produto['nome']
        tipo = produto['tipo']
        status = produto['status']
        url = produto['url']
        preco_estimado = produto.get('preco_estimado', 0)
        menor_preco = produto.get('menor_preco', None)
        
        preco_estimado_display = formatar_preco_brasileiro(preco_estimado)
        
        # Formata menor preço
        if menor_preco is not None and menor_preco > 0:
            menor_preco_display = f'<span class="preco-menor">{formatar_preco_brasileiro(menor_preco)}</span>'
        else:
            menor_preco_display = '<span style="color: #6c757d;">—</span>'
        
        status_class = tipo
        if tipo == "disponivel":
            status_display = "✓ Disponível"
            preco_display = f'<span class="preco">{status}</span>'
            
            preco_atual_num = extrair_valor_numerico(status)
            diferenca = calcular_diferenca_preco(preco_atual_num, preco_estimado)
            
            if diferenca is not None:
                if diferenca > 0:
                    diferenca_class = "negativa"
                    diferenca_display = f'<span class="diferenca {diferenca_class}">📈 +{diferenca:.1f}%</span>'
                elif diferenca < 0:
                    diferenca_class = "positiva"
                    diferenca_display = f'<span class="diferenca {diferenca_class}">📉 {diferenca:.1f}%</span>'
                else:
                    diferenca_class = "neutro"
                    diferenca_display = f'<span class="diferenca {diferenca_class}">0%</span>'
            else:
                diferenca_display = '<span style="color: #6c757d;">—</span>'
                
        elif tipo == "esgotado":
            status_display = "✗ Esgotado"
            preco_display = '<span style="color: #dc3545;">—</span>'
            diferenca_display = '<span style="color: #6c757d;">—</span>'
        else:
            status_display = "⚠ Erro"
            preco_display = '<span style="color: #ffc107;">—</span>'
            diferenca_display = '<span style="color: #6c757d;">—</span>'
        
        html += f"""
                        <tr>
                            <td class="index-cell"><span class="index">{i}</span></td>
                            <td class="produto-nome">{nome}</td>
                            <td><span class="status {status_class}">{status_display}</span></td>
                            <td>{preco_display}</td>
                            <td>{menor_preco_display}</td>
                            <td><span class="preco-estimado">{preco_estimado_display}</span></td>
                            <td>{diferenca_display}</td>
                            <td><a href="{url}" class="link" target="_blank">🛒 Ver</a></td>
                        </tr>
        """
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p>Este é um relatório automático gerado pelo Monitor de Preços KaBuM!</p>
                <p>© 2025 - Sistema de Monitoramento de Produtos</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def enviar_email(produtos_info, disponiveis, esgotados, erros, agora):
    """Envia email com o relatório"""
    try:
        msg = EmailMessage()
        msg['Subject'] = f'📊 Relatório KaBuM! - {agora}'
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = ', '.join(DESTINATARIOS)
        
        html_content = criar_html_email(produtos_info, disponiveis, esgotados, erros, agora)
        msg.add_alternative(html_content, subtype='html')
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_REMETENTE, SENHA_APP)
            smtp.send_message(msg)
        
        print("✅ Email enviado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar email: {str(e)}")
        return False

# ========================================
# FUNÇÕES DE INTERFACE
# ========================================

def imprimir_cabecalho(agora):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*120)
    print("🔍 MONITOR DE PREÇOS KABUM".center(120))
    print("="*120)
    print(f"⏰ 📅 Verificação iniciada em: {agora}")
    print(f"📧 Email: {EMAIL_REMETENTE}")
    print(f"🌐 Ambiente: {'CI/CD' if os.environ.get('CI') else 'Local'}")
    print("="*120 + "\n")

def imprimir_resultado(index, total, produto, status, preco_estimado, menor_preco, url):
    """Imprime resultado de cada produto"""
    print(f"[{index}/{total}] {produto}")
    print(f"      Status: {status}")
    print(f"      Preço Estimado: {formatar_preco_brasileiro(preco_estimado)}")
    
    # Exibe menor preço histórico
    if menor_preco is not None and menor_preco > 0:
        print(f"      Menor Preço Histórico: 🏆 {formatar_preco_brasileiro(menor_preco)}")
    else:
        print(f"      Menor Preço Histórico: Não disponível")
    
    if "💰 R$" in status:
        preco_atual_texto = status.replace("💰 ", "")
        preco_atual_num = extrair_valor_numerico(preco_atual_texto)
        if preco_atual_num:
            diferenca = calcular_diferenca_preco(preco_atual_num, preco_estimado)
            if diferenca is not None:
                if diferenca > 0:
                    print(f"      Diferença: 📈 +{diferenca:.1f}% (mais caro)")
                elif diferenca < 0:
                    print(f"      Diferença: 📉 {diferenca:.1f}% (mais barato) 🎉")
                else:
                    print(f"      Diferença: 0% (igual)")
    
    print(f"      Link: {url}")
    print("-"*120)

def imprimir_rodape(disponiveis, esgotados, erros):
    """Imprime resumo final"""
    print("\n" + "="*120)
    print("📊 RESUMO DA VERIFICAÇÃO".center(120))
    print("="*120)
    print(f"✅ Produtos disponíveis: {disponiveis}")
    print(f"❌ Produtos esgotados: {esgotados}")
    print(f"⚠️ Erros ao verificar: {erros}")
    print("="*120 + "\n")

# ========================================
# FUNÇÃO PRINCIPAL
# ========================================

def main():
    """Função principal do monitor"""
    agora = obter_horario_brasilia()
    print("Horário de Brasília:", agora)
    
    # Inicializa variáveis
    produtos_disponiveis = 0
    produtos_esgotados = 0
    erros = 0
    total_urls = len(PRODUTOS)
    produtos_info = []
    
    # Inicializa driver
    driver = inicializar_driver()
    
    # Imprime cabeçalho
    imprimir_cabecalho(agora)
    
    try:
        # Processa cada produto
        for index, item in enumerate(PRODUTOS, 1):
            url = item['url']
            preco_estimado = item['preco_estimado']
            product_key = item.get('product_key', f"kabum-{index}")
            
            try:
                # Acessa página
                driver.get(url)
                time.sleep(3)
                
                # Verifica status
                tipo, status = verificar_status_produto(driver)
                
                # Busca menor preço histórico
                menor_preco_historico = obter_menor_preco_historico(product_key)
                
                # Contabiliza
                if tipo == "disponivel":
                    produtos_disponiveis += 1
                    status_display = f"💰 {status}"
                elif tipo == "esgotado":
                    produtos_esgotados += 1
                    status_display = "❌ Ops! Produto esgotado"
                else:
                    erros += 1
                    status_display = "⚠️ Não foi possível verificar"
                
                # Formata nome
                nome_produto = formatar_nome_produto(url)
                
                # Armazena informações
                produtos_info.append({
                    'product_key': product_key,
                    'nome': nome_produto,
                    'tipo': tipo,
                    'status': status,
                    'url': url,
                    'preco_estimado': preco_estimado,
                    'menor_preco': menor_preco_historico
                })
                
                # Imprime resultado
                imprimir_resultado(index, total_urls, nome_produto, status_display, preco_estimado, menor_preco_historico, url)
                
            except Exception as e:
                nome_produto = formatar_nome_produto(url)
                status_display = "⚠️ Erro ao processar"
                
                # Busca menor preço mesmo em caso de erro
                menor_preco_historico = obter_menor_preco_historico(product_key)
                
                imprimir_resultado(index, total_urls, nome_produto, status_display, preco_estimado, menor_preco_historico, url)
                erros += 1
                
                produtos_info.append({
                    'product_key': product_key,
                    'nome': nome_produto,
                    'tipo': 'erro',
                    'status': 'Erro ao verificar',
                    'url': url,
                    'preco_estimado': preco_estimado,
                    'menor_preco': menor_preco_historico
                })
    
    finally:
        # Fecha driver
        driver.quit()
    
    # Imprime resumo
    imprimir_rodape(produtos_disponiveis, produtos_esgotados, erros)
    
    # Salva no Supabase (histórico completo)
    print("💾 Salvando dados no Supabase (Monitoramento Kabum)...")
    salvar_no_supabase(produtos_info)
    
    # Atualiza menores preços
    print("\n💰 Atualizando menores preços históricos...")
    atualizar_menores_precos(produtos_info)
    
    # Envia email
    print("\n📧 Enviando relatório por email...")
    enviar_email(produtos_info, produtos_disponiveis, produtos_esgotados, erros, agora)
    
    print("\n✅ Monitoramento concluído com sucesso!")

# ========================================
# FUNÇÃO PARA CONSULTAR DADOS (EXEMPLO)
# ========================================

def consultar_ultimas_verificacoes(limit=10):
    """Exemplo: Consulta últimas verificações e exibe em horário de Brasília"""
    try:
        response = supabase.table("Monitoramento Kabum") \
            .select("*") \
            .order("data_coleta", desc=True) \
            .limit(limit) \
            .execute()
        
        print(f"\n📋 Últimas {limit} verificações:")
        print("="*120)
        
        for item in response.data:
            # Converte data UTC para Brasília
            data_brasilia = converter_utc_para_brasilia(item['data_coleta'])
            
            print(f"Produto: {item['nome']}")
            print(f"Preço: {formatar_preco_brasileiro(item['preco_atual']) if item['preco_atual'] else 'N/A'}")
            print(f"Status: {item['status']}")
            print(f"Data (Brasília): {data_brasilia}")
            print("-"*120)
        
        return response.data
    except Exception as e:
        print(f"❌ Erro ao consultar: {str(e)}")
        return None

# ========================================
# EXECUÇÃO
# ========================================

if __name__ == "__main__":
    main()
