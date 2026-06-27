import json
import pytest
from unittest.mock import patch, MagicMock
from app.worker import process_message

# Mensagem SQS fake para os testes
FAKE_MESSAGE = {
    'ReceiptHandle': 'fake-receipt-handle',
    'Body': json.dumps({
        'video_id': 1,
        's3_video_key': 'uploads/fake_video.mp4',
        'user_email': 'teste@fiap.com'
    })
}

@patch("app.worker.update_video_status")
@patch("app.worker.download_from_s3")
@patch("app.worker.process_video")
@patch("app.worker.upload_to_s3")
@patch("app.worker.delete_sqs_message")
@patch("os.path.exists")
@patch("os.remove")
@patch("shutil.rmtree")
def test_process_message_success(mock_rmtree, mock_remove, mock_exists, mock_delete_sqs, 
                                 mock_upload_s3, mock_process, mock_download_s3, mock_update_db):
    """Testa o fluxo de SUCESSO do Worker (Caminho Feliz)"""
    mock_exists.return_value = True  # Finge que os arquivos existem para deletar no finally
    
    process_message(FAKE_MESSAGE)
    
    # Verifica se os status do banco foram atualizados corretamente
    assert mock_update_db.call_count == 2
    mock_update_db.assert_any_call(1, 'PROCESSANDO')
    mock_update_db.assert_any_call(1, 'CONCLUIDO', 'outputs/frames_1.zip')
    
    # Verifica chamadas da AWS e Processamento
    mock_download_s3.assert_called_once()
    mock_process.assert_called_once()
    mock_upload_s3.assert_called_once()
    mock_delete_sqs.assert_called_once_with('fake-receipt-handle')

@patch("app.worker.update_video_status")
@patch("app.worker.download_from_s3")
@patch("app.worker.process_video")
@patch("app.worker.send_error_email")
@patch("app.worker.delete_sqs_message")
@patch("os.path.exists")
def test_process_message_error(mock_exists, mock_delete_sqs, mock_send_email, mock_process, 
                               mock_download_s3, mock_update_db):
    """Testa o fluxo de ERRO do Worker (Ex: Arquivo corrompido)"""
    mock_exists.return_value = False
    
    # Força a função de processamento a dar um erro (Ex: erro do OpenCV)
    mock_process.side_effect = Exception("Vídeo corrompido")
    
    process_message(FAKE_MESSAGE)
    
    # Verifica se os status do banco foram atualizados corretamente
    assert mock_update_db.call_count == 2
    mock_update_db.assert_any_call(1, 'PROCESSANDO')
    mock_update_db.assert_any_call(1, 'ERRO') # Garante que caiu no Except
    
    # Garante que mandou o e-mail de erro
    mock_send_email.assert_called_once_with('teste@fiap.com')
    
    # A mensagem DEVE ser deletada da fila mesmo com erro, para não ficar travando o SQS
    mock_delete_sqs.assert_called_once_with('fake-receipt-handle')