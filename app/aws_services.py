import boto3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

s3_client = boto3.client('s3', region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
sqs_client = boto3.client('sqs', region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")

def download_from_s3(s3_key, download_path):
    s3_client.download_file(BUCKET_NAME, s3_key, download_path)

def upload_to_s3(file_path, s3_key):
    s3_client.upload_file(file_path, BUCKET_NAME, s3_key)

def delete_sqs_message(receipt_handle):
    sqs_client.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)

def generate_presigned_url(s3_key):
    # Gera um link de download seguro e temporário (válido por 1 hora)
    # Alterado para 24 horas (86400 segundos)
    return s3_client.generate_presigned_url('get_object',
                                            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                                            ExpiresIn=86400)


def send_error_email(to_email):
    # Envio seguro de email contornando bloqueios da AWS Academy
    remetente = os.getenv("EMAIL_OFICINA")
    senha = os.getenv("EMAIL_SENHA_APP")
    
    if not remetente or not senha:
        print("[SMTP] Credenciais de e-mail ausentes. Ignorando envio.")
        return

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = to_email
    msg['Subject'] = "❌ Falha no Processamento | CYBERFRAME AI"
    
    # Template HTML para o e-mail de erro
    html_body = f"""
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Courier New', Courier, monospace; background-color: #0a0a0a; color: #e0e0e0; margin: 0; padding: 20px; }}
            .container {{ background-color: #1a1a1a; border: 1px solid #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); max-width: 600px; margin: auto; padding: 30px; text-align: center; }}
            .logo svg {{ filter: drop-shadow(0 0 5px #00f3ff); }}
            h1 {{ color: #ff4d4d; text-shadow: 0 0 8px #ff4d4d; }}
            p {{ font-size: 16px; line-height: 1.6; }}
            .footer {{ font-size: 12px; color: #888; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <svg width="80" height="80" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="neonGradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#00f3ff" /><stop offset="100%" stop-color="#bf00ff" /></linearGradient>
                    </defs>
                    <path d="M50 10 L90 30 L90 70 L50 90 L10 70 L10 30 Z" fill="none" stroke="url(#neonGradient)" stroke-width="4"/>
                    <circle cx="50" cy="50" r="15" fill="none" stroke="#00f3ff" stroke-width="3"/>
                    <circle cx="50" cy="50" r="5" fill="#00f3ff"/>
                </svg>
            </div>
            <h1>Falha na Análise</h1>
            <p>Olá,</p>
            <p>Detectamos uma anomalia ao processar seu arquivo de vídeo. Isso pode ocorrer devido a um formato não suportado ou arquivo corrompido.</p>
            <p>Por favor, verifique a integridade do seu arquivo e tente fazer o upload novamente.</p>
            <div class="footer">
                <p>&copy; CYBERFRAME AI // Sistema de Extração Neural</p>
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        # Usando 'with' para garantir que a conexão seja fechada
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.sendmail(remetente, to_email, msg.as_string())
        print(f"📧 E-mail de erro enviado para {to_email}")
    except Exception as e:
        print(f"Erro ao enviar email SMTP: {e}")

def send_success_email(to_email, download_link):
    remetente = os.getenv("EMAIL_OFICINA")
    senha = os.getenv("EMAIL_SENHA_APP")

    if not remetente or not senha:
        print("[SMTP] Credenciais de e-mail ausentes. Ignorando envio.")
        return

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = to_email
    msg['Subject'] = "✅ Processamento Concluído | CYBERFRAME AI"

    # Template HTML para o e-mail de sucesso
    html_body = f"""
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Courier New', Courier, monospace; background-color: #0a0a0a; color: #e0e0e0; margin: 0; padding: 20px; }}
            .container {{ background-color: #1a1a1a; border: 1px solid #00f3ff; box-shadow: 0 0 15px rgba(0, 243, 255, 0.2); max-width: 600px; margin: auto; padding: 30px; text-align: center; }}
            .logo svg {{ filter: drop-shadow(0 0 5px #00f3ff); }}
            h1 {{ color: #00ff66; text-shadow: 0 0 8px #00ff66; }}
            p {{ font-size: 16px; line-height: 1.6; }}
            .button {{ display: inline-block; background-color: transparent; border: 1px solid #00f3ff; color: #00f3ff; padding: 12px 25px; text-decoration: none; font-size: 16px; margin-top: 20px; transition: all 0.3s ease; box-shadow: 0 0 10px rgba(0, 243, 255, 0.2); }}
            .button:hover {{ background-color: #00f3ff; color: #000; box-shadow: 0 0 20px rgba(0, 243, 255, 0.6); }}
            .footer {{ font-size: 12px; color: #888; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <svg width="80" height="80" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="neonGradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#00f3ff" /><stop offset="100%" stop-color="#bf00ff" /></linearGradient>
                    </defs>
                    <path d="M50 10 L90 30 L90 70 L50 90 L10 70 L10 30 Z" fill="none" stroke="url(#neonGradient)" stroke-width="4"/>
                    <circle cx="50" cy="50" r="15" fill="none" stroke="#00f3ff" stroke-width="3"/>
                    <circle cx="50" cy="50" r="5" fill="#00f3ff"/>
                </svg>
            </div>
            <h1>Análise Concluída</h1>
            <p>Olá,</p>
            <p>O processamento do seu arquivo de vídeo foi concluído com sucesso. Os frames extraídos estão prontos para download.</p>
            <a href="{download_link}" class="button">BAIXAR PACOTE DE FRAMES</a>
            <p style="font-size: 12px; color: #a0a0a0; margin-top: 15px;">Este link de acesso é seguro e expira em 24 horas.</p>
            <div class="footer">
                <p>&copy; CYBERFRAME AI // Sistema de Extração Neural</p>
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.sendmail(remetente, to_email, msg.as_string())
            print(f"📧 E-mail de sucesso enviado para {to_email}")
    except Exception as e:
        print(f"Erro ao enviar email SMTP de sucesso: {e}")