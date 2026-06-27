import cv2
import os
import zipfile


def process_video(video_path, output_dir, zip_path):
    print(f"[PROCESSOR] Iniciando processamento do vídeo: {video_path}")

    if not os.path.exists(video_path):
        raise Exception(f"Arquivo de vídeo não encontrado: {video_path}")

    print(f"[PROCESSOR] Tamanho do vídeo: {os.path.getsize(video_path)} bytes")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    cam = cv2.VideoCapture(video_path)

    if not cam.isOpened():
        raise Exception(f"Não foi possível abrir o vídeo: {video_path}")

    fps = cam.get(cv2.CAP_PROP_FPS)
    total_frames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"[PROCESSOR] FPS: {fps}")
    print(f"[PROCESSOR] Total de frames: {total_frames}")

    frame_interval = int(fps) if fps > 0 else 1

    currentframe = 0
    frame_files = []

    while True:
        ret, frame = cam.read()

        if not ret:
            break

        if currentframe % frame_interval == 0:
            name = os.path.join(output_dir, f"frame_{currentframe}.jpg")

            sucesso = cv2.imwrite(name, frame)

            if not sucesso:
                raise Exception(f"Falha ao salvar frame {currentframe}")

            frame_files.append(name)

        currentframe += 1

    cam.release()

    print(f"[PROCESSOR] Frames extraídos: {len(frame_files)}")

    if len(frame_files) == 0:
        raise Exception("Nenhum frame foi extraído do vídeo.")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in frame_files:
            zipf.write(file, os.path.basename(file))

    print(f"[PROCESSOR] ZIP criado em: {zip_path}")

    return zip_path