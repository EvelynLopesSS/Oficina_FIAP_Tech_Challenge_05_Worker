import boto3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .logo_data import LOGO_BASE64

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


def _send_email(to_email, subject, html_body):
    """Função centralizada para enviar e-mails."""
    remetente = os.getenv("EMAIL_OFICINA")
    senha = os.getenv("EMAIL_SENHA_APP")

    if not remetente or not senha:
        print("[SMTP] Credenciais de e-mail ausentes. Ignorando envio.")
        return

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.sendmail(remetente, to_email, msg.as_string())
        print(f"📧 E-mail '{subject}' enviado para {to_email}")
    except Exception as e:
        print(f"❌ Erro ao enviar email SMTP: {e}")

def _build_html_template(title, title_color, content_html):
    """Constrói o template HTML base do e-mail com estilos inline."""
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: Arial, sans-serif;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%">
        <tr>
            <td style="padding: 20px 0;">
                <table align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; border: 1px solid #dddddd;">
                    <tr>
                        <td align="center" style="padding: 40px 0 30px 0;">
                            <img src="data:image/png;base64,{LOGO_BASE64}" alt="CyberFrame AI Logo" width="100" style="display: block;" />
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <h1 style="color: {title_color}; text-align: center;">{title}</h1>
                            {content_html}
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="padding: 20px 30px; background-color: #eeeeee; color: #777777; font-size: 12px;">
                            &copy; CYBERFRAME AI // Sistema de Extração Neural
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

def send_error_email(to_email):
    subject = "❌ Falha no Processamento | CYBERFRAME AI"
    title = "Falha na Análise"
    title_color = "#D9534F"  # Vermelho
    content_html = """
        <p style="font-size: 16px; line-height: 1.5; color: #333333; text-align: center;">Olá,</p>
        <p style="font-size: 16px; line-height: 1.5; color: #333333; text-align: center;">
            Detectamos uma anomalia ao processar seu arquivo de vídeo. Isso pode ocorrer devido a um formato não suportado ou arquivo corrompido.
        </p>
        <p style="font-size: 16px; line-height: 1.5; color: #333333; text-align: center;">
            Por favor, verifique a integridade do seu arquivo e tente fazer o upload novamente.
        </p>
    """
    html_body = _build_html_template(title, title_color, content_html)
    _send_email(to_email, subject, html_body)

def send_success_email(to_email, download_link):
    subject = "✅ Processamento Concluído | CYBERFRAME AI"
    title = "Análise Concluída"
    title_color = "#5CB85C"  # Verde
    content_html = f"""
        <p style="font-size: 16px; line-height: 1.5; color: #333333; text-align: center;">Olá,</p>
        <p style="font-size: 16px; line-height: 1.5; color: #333333; text-align: center;">
            O processamento do seu arquivo de vídeo foi concluído com sucesso. Os frames extraídos estão prontos para download.
        </p>
        <table border="0" cellpadding="0" cellspacing="0" width="100%">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <a href="{download_link}" target="_blank" style="display: inline-block; background-color: #007BFF; color: #ffffff; padding: 12px 25px; text-decoration: none; font-size: 16px; border-radius: 5px;">
                        BAIXAR PACOTE DE FRAMES
                    </a>
                </td>
            </tr>
        </table>
        <p style="font-size: 12px; color: #777777; text-align: center;">
            Este link de acesso é seguro e expira em 24 horas.
        </p>
    """
    html_body = _build_html_template(title, title_color, content_html)
    _send_email(to_email, subject, html_body)