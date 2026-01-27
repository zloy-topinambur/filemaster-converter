from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, uuid, subprocess

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 1. Определяем директорию, где лежит этот скрипт (для стабильной работы на Linux/Render)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Папка для загрузок
UPLOAD_DIR = os.path.join(BASE_DIR, "temp_storage")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ПУТЬ К LIBREOFFICE (Команда для Linux/Docker)
LIBREOFFICE_PATH = "soffice"

# --- МАРШРУТЫ ---

@app.get("/")
async def read_index():
    # Отдаем главную страницу
    file_path = os.path.join(BASE_DIR, 'index.html')
    if not os.path.exists(file_path):
        return JSONResponse(status_code=500, content={"message": "Error: index.html not found"})
    return FileResponse(file_path)

# !!! ВОТ СЮДА ДОБАВЛЯЕМ SITEMAP !!!
@app.get("/sitemap.xml")
async def sitemap():
    # Отдаем карту сайта для Google
    file_path = os.path.join(BASE_DIR, 'sitemap.xml')
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"message": "Sitemap not found"})
    return FileResponse(file_path, media_type="application/xml")

# ... где-то после функции sitemap ...

@app.get("/robots.txt")
async def robots():
    file_path = os.path.join(BASE_DIR, 'robots.txt')
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"message": "robots.txt not found"})
    # Важно: media_type должен быть text/plain
    return FileResponse(file_path, media_type="text/plain")

@app.post("/convert-pages")
async def convert_pages(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pages'):
        return JSONResponse(status_code=400, content={"message": "Only .pages files supported"})

    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Конвертация
        subprocess.run([
            LIBREOFFICE_PATH, 
            '--headless', 
            '--convert-to', 'pdf', 
            '--outdir', UPLOAD_DIR, 
            input_path
        ], check=True)
        
        pdf_name = f"{file_id}_{file.filename.rsplit('.', 1)[0]}.pdf"
        
        # Проверка результата
        final_pdf_path = os.path.join(UPLOAD_DIR, pdf_name)
        if not os.path.exists(final_pdf_path):
             raise Exception("PDF conversion failed")

        return {"status": "success", "url": f"/download/{pdf_name}", "name": file.filename.rsplit('.', 1)[0] + ".pdf"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    path = os.path.join(UPLOAD_DIR, file_name)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

