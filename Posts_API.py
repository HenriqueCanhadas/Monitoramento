from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os

# === CONFIGURAÇÕES VIA VARIÁVEIS DE AMBIENTE ===
EMAIL_REMETENTE = os.environ.get('EMAIL_APP_P')
SENHA_APP = os.environ.get('SENHA_APP_P')

DESTINATARIOS = [EMAIL_REMETENTE]  # Envia para o mesmo email

def enviar_email(assunto, corpo_texto, url=None, esperado=None, encontrado=None, erro=None):
    """Envia email de alerta"""
    msg = EmailMessage()
    msg['Subject'] = assunto
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = ', '.join(DESTINATARIOS)

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #c0392b;">🚨 Alerta de Verificação de Elemento</h2>
            <p><strong>Data/Hora:</strong> {agora}</p>
            <p>{corpo_texto}</p>
    """

    if url:
        html += f'<p><strong>🔗 URL:</strong> <a href="{url}">{url}</a></p>'
    if esperado is not None:
        html += f'<p><strong>✅ Texto Esperado:</strong> {esperado}</p>'
    if encontrado is not None:
        html += f'<p><strong>❌ Texto Encontrado:</strong> {encontrado}</p>'
    if erro:
        html += f'<p><strong>⚠️ Erro:</strong><br><code>{erro}</code></p>'

    html += """
            <hr>
            <p style="font-size: 0.9em; color: #888;">
                Este é um e-mail automático enviado pelo sistema de monitoramento.
            </p>
        </body>
    </html>
    """

    msg.set_content(corpo_texto)
    msg.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_REMETENTE, SENHA_APP)
            smtp.send_message(msg)
        print("📧 Email enviado com sucesso ✅")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        return False

# === SETUP DO DRIVER ===
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

print("\n" + "="*70)
print("🤖 Sistema de Monitoramento de Posts Iniciado")
print("="*70)
print(f"📧 Email configurado: {EMAIL_REMETENTE}")
print(f"🌐 Ambiente: {'CI/CD' if os.environ.get('CI') else 'Local'}")
print("="*70 + "\n")

# === FUNÇÃO DE VERIFICAÇÃO ===
def verificar_primeiro_resultado(busca_url, texto_esperado):
    """Verifica se o primeiro resultado corresponde ao texto esperado"""
    print("\n" + "="*60)
    print(f"🔍 Verificando: {texto_esperado}")
    print(f"🌐 URL: {busca_url}")
    
    try:
        driver.get(busca_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article .read-title a")))

        element = driver.find_element(By.CSS_SELECTOR, "article .read-title a")
        texto = element.text.strip()

        if texto == texto_esperado:
            print(f"✅ Primeiro resultado corresponde: '{texto}'")
        else:
            print(f"❌ Primeiro resultado diferente do esperado.")
            print(f"   ➤ Encontrado: '{texto}'")
            print(f"   ➤ Esperado : '{texto_esperado}'")
            enviado = enviar_email(
                assunto=f"[Alerta] Elemento não encontrado: {texto_esperado}",
                corpo_texto="O primeiro resultado foi encontrado, mas o texto não corresponde ao esperado.",
                url=busca_url,
                esperado=texto_esperado,
                encontrado=texto
            )
            if not enviado:
                print("⚠️ Falha ao enviar alerta por e-mail.")

    except Exception as e:
        print(f"❌ Erro durante a verificação: {e}")
        enviado = enviar_email(
            assunto=f"[Alerta] Elemento não encontrado: {texto_esperado}",
            corpo_texto="Ocorreu um erro ao tentar verificar o elemento na página.",
            url=busca_url,
            esperado=texto_esperado,
            erro=str(e)
        )
        if not enviado:
            print("⚠️ Falha ao enviar alerta por e-mail.")

    print("="*60)

# === VERIFICAÇÕES ===
try:
    verificar_primeiro_resultado(
        busca_url="https://packsparapobres.com/?s=sailorscholar",
        texto_esperado="#Sailorscholar – Christmas Frieren & Fern"
    )

    verificar_primeiro_resultado(
        busca_url="https://packsparapobres.com/?s=Natylikespizza",
        texto_esperado="Natylikespizza – Panty"
    )

    print("\n" + "="*70)
    print("✅ Monitoramento concluído com sucesso!")
    print("="*70 + "\n")

except KeyboardInterrupt:
    print("\n⚠️ Execução interrompida pelo usuário")
except Exception as e:
    print(f"\n❌ Erro crítico: {e}")
finally:
    driver.quit()
    print("🔒 Navegador fechado\n")
