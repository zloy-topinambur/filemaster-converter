from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, uuid, subprocess

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = "temp_storage"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ПУТЬ К LIBREOFFICE (Проверьте путь!)
LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"

@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.post("/convert-pages")
async def convert_pages(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pages'):
        return JSONResponse(status_code=400, content={"message": "Only .pages files supported"})

    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        subprocess.run([LIBREOFFICE_PATH, '--headless', '--convert-to', 'pdf', '--outdir', UPLOAD_DIR, input_path], check=True)
        pdf_name = f"{file_id}_{file.filename.rsplit('.', 1)[0]}.pdf"
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