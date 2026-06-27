import unittest
from unittest.mock import patch, MagicMock
import os
import json
import sys

# Adiciona o diretório 'app' ao path para permitir a importação dos módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

# Mock dos módulos antes de importar o worker para resolver o ModuleNotFoundError
MOCK_MODULES = {
    'aws_services': MagicMock(),
    'database': MagicMock(),
    'processor': MagicMock(),
}

@patch.dict('sys.modules', MOCK_MODULES)
class TestWorker(unittest.TestCase):

    def _create_mock_message(self):
        """Cria uma mensagem SQS mockada."""
        message_body = {
            "video_id": "123-abc",
            "s3_video_key": "uploads/video.mp4",
            "user_email": "test@example.com"
        }
        return {
            'ReceiptHandle': 'test_receipt_handle',
            'Body': json.dumps(message_body)
        }

    def setUp(self):
        """Importa o módulo do worker aqui, depois que os mocks foram aplicados."""
        from worker import process_message
        self.process_message = process_message

    @patch('app.worker.delete_sqs_message')
    @patch('app.worker.shutil.rmtree')
    @patch('app.worker.os.remove')
    @patch('app.worker.os.path.exists', return_value=True)
    @patch('app.worker.send_success_email')
    @patch('app.worker.generate_presigned_url', return_value="http://presigned.url/download")
    @patch('app.worker.update_video_status')
    @patch('app.worker.upload_to_s3')
    @patch('app.worker.process_video')
    @patch('app.worker.download_from_s3')
    def test_process_message_success(self, mock_download, mock_process, mock_upload, mock_update, mock_generate_url, mock_send_email, mock_exists, mock_os_remove, mock_rmtree, mock_delete_sqs):
        """Testa o fluxo de sucesso do processamento da mensagem."""
        mock_message = self._create_mock_message()
        
        self.process_message(mock_message)

        # Verifica se as funções foram chamadas na ordem correta
        mock_download.assert_called_once()
        mock_process.assert_called_once()
        mock_upload.assert_called_once()
        
        # Verifica as atualizações de status
        mock_update.assert_any_call('123-abc', 'PROCESSANDO')
        mock_update.assert_any_call('123-abc', 'CONCLUIDO', 'outputs/frames_123-abc.zip')

        # Verifica a geração de URL e envio de e-mail
        mock_generate_url.assert_called_once_with('outputs/frames_123-abc.zip')
        mock_send_email.assert_called_once_with('test@example.com', "http://presigned.url/download")

        # Verifica a limpeza e deleção da mensagem
        self.assertEqual(mock_os_remove.call_count, 2)
        mock_rmtree.assert_called_once()
        mock_delete_sqs.assert_called_once_with('test_receipt_handle')

    @patch('app.worker.delete_sqs_message')
    @patch('app.worker.shutil.rmtree')
    @patch('app.worker.os.remove')
    @patch('app.worker.os.path.exists', return_value=True)
    @patch('app.worker.send_error_email')
    @patch('app.worker.update_video_status')
    @patch('app.worker.process_video', side_effect=Exception("Processing failed"))
    @patch('app.worker.download_from_s3')
    def test_process_message_failure(self, mock_download, mock_process, mock_update, mock_send_error_email, mock_exists, mock_os_remove, mock_rmtree, mock_delete_sqs):
        """Testa o fluxo de falha durante o processamento."""
        mock_message = self._create_mock_message()

        self.process_message(mock_message)

        # Verifica as chamadas iniciais
        mock_download.assert_called_once()
        mock_process.assert_called_once()

        # Verifica as atualizações de status para erro
        mock_update.assert_any_call('123-abc', 'PROCESSANDO')
        mock_update.assert_any_call('123-abc', 'ERRO')

        # Verifica o envio do e-mail de erro
        mock_send_error_email.assert_called_once_with('test@example.com')

        # Verifica se a limpeza e deleção da mensagem ainda ocorrem no bloco finally
        self.assertEqual(mock_os_remove.call_count, 2)
        mock_rmtree.assert_called_once()
        mock_delete_sqs.assert_called_once_with('test_receipt_handle')

if __name__ == '__main__':
    unittest.main()