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
    msg['Subject'] = "FIAP X - Erro no Processamento do Vídeo"
    corpo = "Olá,\n\nOcorreu um erro ao processar o seu vídeo (arquivo corrompido ou formato inválido). Por favor, tente enviar novamente!\n\nEquipe FIAP X"
    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remetente, senha)
        servidor.sendmail(remetente, to_email, msg.as_string())
        servidor.quit()
        print(f"📧 E-mail de erro enviado para {to_email}")
    except Exception as e:
        print(f"Erro ao enviar email SMTP: {e}")