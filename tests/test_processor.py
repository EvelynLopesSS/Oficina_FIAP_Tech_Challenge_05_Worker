import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys

# Adiciona o diretório 'app' ao path para permitir a importação dos módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.processor import process_video

class TestVideoProcessor(unittest.TestCase):

    @patch('app.processor.os.path.getsize')
    @patch('app.processor.os.path.exists')
    @patch('app.processor.os.makedirs')
    @patch('app.processor.cv2.VideoCapture')
    @patch('app.processor.cv2.imwrite')
    @patch('app.processor.zipfile.ZipFile')
    def test_process_video_success(self, mock_zipfile, mock_imwrite, mock_videocapture, mock_makedirs, mock_exists, mock_getsize):
        """
        Testa o fluxo de sucesso do processamento de vídeo.
        """
        # Configuração dos mocks
        mock_exists.return_value = True
        mock_imwrite.return_value = True
        mock_getsize.return_value = 1024 # Simula um tamanho de arquivo

        # Mock do objeto VideoCapture
        mock_cam = MagicMock()
        mock_cam.isOpened.return_value = True
        mock_cam.get.side_effect = [30.0, 300] # FPS, Total de Frames
        # Simula a leitura de 31 frames para extrair 2 (frame 0 e 30)
        mock_cam.read.side_effect = [(True, 'frame_data')] * 31 + [(False, None)]
        mock_videocapture.return_value = mock_cam

        # Mock do ZipFile
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip

        # Execução da função
        video_path = '/tmp/test.mp4'
        output_dir = '/tmp/frames'
        zip_path = '/tmp/frames.zip'
        result_path = process_video(video_path, output_dir, zip_path)

        # Verificações
        self.assertEqual(result_path, zip_path)
        mock_videocapture.assert_called_once_with(video_path)
        mock_makedirs.assert_called_once_with(output_dir)
        
        # Verifica se o imwrite foi chamado para os frames corretos (0 e 30)
        self.assertEqual(mock_imwrite.call_count, 2)
        mock_imwrite.assert_any_call('/tmp/frames/frame_0.jpg', 'frame_data')
        mock_imwrite.assert_any_call('/tmp/frames/frame_30.jpg', 'frame_data')

        # Verifica se os arquivos foram adicionados ao zip
        mock_zip.write.assert_any_call('/tmp/frames/frame_0.jpg', 'frame_0.jpg')
        mock_zip.write.assert_any_call('/tmp/frames/frame_30.jpg', 'frame_30.jpg')
        self.assertEqual(mock_zip.write.call_count, 2)

        mock_cam.release.assert_called_once()

    @patch('app.processor.os.path.exists', return_value=False) # Simula que o arquivo não existe
    def test_process_video_file_not_found(self, mock_exists):
        """
        Testa o comportamento quando o arquivo de vídeo não é encontrado.
        """
        with self.assertRaisesRegex(Exception, "Arquivo de vídeo não encontrado"):
            process_video('/tmp/non_existent_video.mp4', '/tmp/frames', '/tmp/frames.zip')

    @patch('app.processor.os.path.exists', return_value=True) # Simula que o arquivo existe
    @patch('app.processor.os.path.getsize') # Mock para getsize
    @patch('app.processor.cv2.VideoCapture')
    def test_process_video_open_error(self, mock_videocapture, mock_getsize, mock_exists):
        """
        Testa o comportamento quando o OpenCV não consegue abrir o vídeo.
        """
        mock_getsize.return_value = 1024 # Precisa ser mockado mesmo que não usado diretamente no fluxo
        mock_cam = MagicMock()
        mock_cam.isOpened.return_value = False # Simula falha ao abrir
        mock_videocapture.return_value = mock_cam

        with self.assertRaisesRegex(Exception, "Não foi possível abrir o vídeo"):
            process_video('/tmp/bad_video.mp4', '/tmp/frames', '/tmp/frames.zip')

if __name__ == '__main__':
    unittest.main()