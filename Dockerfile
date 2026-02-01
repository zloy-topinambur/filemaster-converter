FROM python:3.10-slim

# Логи в консоль и фикс для папки home
ENV PYTHONUNBUFFERED=1
ENV HOME=/tmp

# Ставим LibreOffice (headless) и шрифты
RUN apt-get update && apt-get install -y \
    libreoffice \
    default-jre-headless \
    fonts-opensymbol \
    fonts-liberation \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем папку для загрузок
RUN mkdir -p temp_storage && chmod 777 temp_storage

EXPOSE 8000

# Запускаем 4 воркера для параллельной обработки
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
