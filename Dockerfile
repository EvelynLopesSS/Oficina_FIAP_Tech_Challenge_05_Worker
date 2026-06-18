FROM python:3.11-slim

# Instala dependências do sistema necessárias para processamento de vídeo
RUN apt-get update && apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Inicia o robô em background
CMD ["python", "app/worker.py"]