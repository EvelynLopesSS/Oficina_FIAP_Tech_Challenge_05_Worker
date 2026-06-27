import os
import json
import time
import shutil
from app.aws_services import sqs_client, QUEUE_URL, download_from_s3, upload_to_s3, delete_sqs_message, send_error_email, generate_presigned_url, send_success_email
from app.database import update_video_status
from app.processor import process_video

def poll_queue():
    print("🤖 Worker iniciado. Aguardando vídeos na fila SQS...")
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10 # Long polling (Economiza requisições)
            )
            
            if 'Messages' in response:
                for message in response['Messages']:
                    process_message(message)
        except Exception as e:
            print(f"Erro na conexão com SQS: {e}")
            time.sleep(5)

def process_message(message):
    receipt_handle = message['ReceiptHandle']
    body = json.loads(message['Body'])
    
    video_id = body['video_id']
    s3_video_key = body['s3_video_key']
    user_email = body['user_email']
    
    print(f"📥 Iniciando processamento do vídeo ID {video_id}")
    update_video_status(video_id, 'PROCESSANDO')
    
    # Prepara pastas temporárias no container
    local_video_path = f"/tmp/{os.path.basename(s3_video_key)}"
    local_output_dir = f"/tmp/frames_{video_id}"
    local_zip_path = f"/tmp/frames_{video_id}.zip"
    s3_zip_key = f"outputs/frames_{video_id}.zip"
    
    try:
        download_from_s3(s3_video_key, local_video_path)
        process_video(local_video_path, local_output_dir, local_zip_path)
        upload_to_s3(local_zip_path, s3_zip_key)
        
        # Atualiza o status e envia e-mail de sucesso com link para download
        update_video_status(video_id, 'CONCLUIDO', s3_zip_key)
        download_link = generate_presigned_url(s3_zip_key)
        send_success_email(user_email, download_link)
        print(f"✅ Vídeo ID {video_id} processado com sucesso!")

        
    except Exception as e:
        print(f"❌ Erro ao processar vídeo ID {video_id}: {e}")
        update_video_status(video_id, 'ERRO')
        send_error_email(user_email)
        
    finally:
        # Limpa o container para não lotar o disco
        if os.path.exists(local_video_path): os.remove(local_video_path)
        if os.path.exists(local_zip_path): os.remove(local_zip_path)
        if os.path.exists(local_output_dir): shutil.rmtree(local_output_dir)
        
        # Deleta a mensagem da fila para não processar duas vezes
        delete_sqs_message(receipt_handle)

if __name__ == '__main__':
    poll_queue()