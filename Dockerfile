# Используем легкий образ Python на базе Linux
FROM python:3.10-slim

# Устанавливаем системные зависимости и LibreOffice
# Также ставим шрифты, чтобы PDF выглядел красиво
RUN apt-get update && apt-get install -y \
    libreoffice \
    default-jre \
    fonts-opensymbol \
    fonts-liberation \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем папку для временных файлов (важно для прав доступа)
RUN mkdir -p temp_storage && chmod 777 temp_storage

# Открываем порт 8000
EXPOSE 8000

# Команда запуска
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]