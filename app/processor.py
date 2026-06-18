import cv2
import os
import zipfile

def process_video(video_path, output_dir, zip_path):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    cam = cv2.VideoCapture(video_path)
    currentframe = 0
    
    # Extrai 1 frame (foto) a cada segundo do vídeo
    fps = cam.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps) if fps > 0 else 1
    
    frame_files = []
    
    while True:
        ret, frame = cam.read()
        if ret:
            if currentframe % frame_interval == 0:
                name = os.path.join(output_dir, f'frame_{currentframe}.jpg')
                cv2.imwrite(name, frame)
                frame_files.append(name)
            currentframe += 1
        else:
            break
            
    cam.release()
    cv2.destroyAllWindows()
    
    # Compacta tudo em um ZIP
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in frame_files:
            zipf.write(file, os.path.basename(file))
            
    return zip_path