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
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">

<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
</head>

<body style="
margin:0;
padding:30px;
background:#0F1117;
font-family:Arial,Helvetica,sans-serif;
">

<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr>
<td align="center">

<table width="620" cellpadding="0" cellspacing="0" border="0"
style="
background:#171B22;
border:2px solid #00F3FF;
border-radius:12px;
">

<tr>
<td align="center" style="padding:45px 30px 25px 30px;">

<div style="
font-size:38px;
font-weight:bold;
color:#00F3FF;
letter-spacing:3px;
">
⚡ CYBERFRAME AI
</div>

<div style="
margin-top:10px;
font-family:Consolas,monospace;
font-size:14px;
color:#9FA6B2;
">
v2.0 // Powered by FIAP X
</div>

</td>
</tr>

<tr>
<td style="padding:10px 45px;">

<h1 style="
margin:0;
text-align:center;
font-size:30px;
color:{title_color};
">
{title}
</h1>

<div style="
margin-top:35px;
font-size:17px;
line-height:1.8;
color:#FFFFFF;
text-align:center;
">
{content_html}
</div>

</td>
</tr>

<tr>
<td align="center" style="padding:35px;">

<hr style="
border:none;
border-top:1px solid #2B313C;
margin-bottom:25px;
">

<div style="
font-size:12px;
color:#7F8A99;
font-family:Consolas,monospace;
letter-spacing:1px;
">
CYBERFRAME AI • Neural Video Processing Platform
</div>

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
    title_color = "#FF5C5C"

    content_html = """

<p style="font-size:18px;color:#FFFFFF;">
Olá!
</p>

<p style="font-size:16px;color:#D7DEE8;">
Detectamos uma falha durante o processamento do seu vídeo.
</p>

<p style="font-size:16px;color:#D7DEE8;">
O arquivo pode estar corrompido ou em um formato incompatível.
</p>

<p style="font-size:16px;color:#D7DEE8;">
Faça um novo upload e tente novamente.
</p>

"""

    html_body = _build_html_template(title, title_color, content_html)
    _send_email(to_email, subject, html_body)

def send_success_email(to_email, download_link):

    subject = "✅ Processamento Concluído | CYBERFRAME AI"
    title = "Análise Concluída"
    title_color = "#00F3FF"

    content_html = f"""

<p style="font-size:18px;color:#FFFFFF;">
Olá!
</p>

<p style="font-size:16px;color:#D7DEE8;">
Seu vídeo foi processado com sucesso.
</p>

<p style="font-size:16px;color:#D7DEE8;">
Os frames extraídos já estão disponíveis para download.
</p>

<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="center" style="padding:35px 0;">

<a href="{download_link}"
style="
display:inline-block;
background:#00F3FF;
color:#0F1117;
padding:16px 36px;
text-decoration:none;
font-size:16px;
font-weight:bold;
border-radius:8px;
letter-spacing:1px;
">
⬇ BAIXAR PACOTE (.ZIP)
</a>

</td>
</tr>
</table>

<p style="font-size:13px;color:#9FA6B2;">
Este link permanecerá válido durante as próximas 24 horas.
</p>

"""

    html_body = _build_html_template(title, title_color, content_html)
    _send_email(to_email, subject, html_body)