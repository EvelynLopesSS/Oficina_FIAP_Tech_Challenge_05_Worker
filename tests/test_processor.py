import pytest
from unittest.mock import patch, MagicMock
from app.processor import process_video

@patch("os.path.exists")
def test_process_video_file_not_found(mock_exists):
    """Garante que o processador levanta erro se o vídeo não existir"""
    mock_exists.return_value = False
    
    with pytest.raises(Exception) as excinfo:
        process_video("video_inexistente.mp4", "/tmp/out", "/tmp/out.zip")
        
    assert "Arquivo de vídeo não encontrado" in str(excinfo.value)

@patch("os.path.exists")
@patch("os.path.getsize")
@patch("os.makedirs")
@patch("cv2.VideoCapture")
@patch("cv2.imwrite")
@patch("zipfile.ZipFile")
def test_process_video_success(mock_zip, mock_imwrite, mock_videocapture, mock_makedirs, mock_getsize, mock_exists):
    """Testa o caminho feliz mockando o OpenCV e o ZIP"""
    # 1. Configura os Mocks
    mock_exists.return_value = True
    mock_getsize.return_value = 1024  # 1 KB fake
    
    # Mock do OpenCV (Simula um vídeo com 1 frame)
    mock_cam = MagicMock()
    mock_cam.isOpened.return_value = True
    mock_cam.get.return_value = 30.0  # 30 FPS
    
    # Simula o read() retornando True na primeira vez e False na segunda (fim do vídeo)
    mock_cam.read.side_effect = [(True, "frame_data"), (False, None)]
    mock_videocapture.return_value = mock_cam
    
    mock_imwrite.return_value = True  # Simula salvamento com sucesso da imagem
    
    # 2. Executa a função
    resultado = process_video("video_valido.mp4", "/tmp/out", "/tmp/out.zip")
    
    # 3. Validações
    assert resultado == "/tmp/out.zip"
    mock_videocapture.assert_called_once_with("video_valido.mp4")
    mock_imwrite.assert_called_once()  # Garante que salvou 1 frame
    mock_zip.assert_called_once()      # Garante que criou o ZIP