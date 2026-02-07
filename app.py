from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, uuid, subprocess

app = FastAPI()

# --- КОНФИГУРАЦИЯ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "temp_storage")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

templates = Jinja2Templates(directory=BASE_DIR)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

LIBREOFFICE_PATH = "soffice"

# --- URL MAPPING ---
URL_MAP = {
    "pages-viewer": "pages_view",
    "pages-to-pdf": "pages_conv",
    "open-dat-file": "dat",
    "winmail-dat-opener": "winmail",
    "view-bin-file": "bin"
}
ID_TO_URL = {v: k for k, v in URL_MAP.items()}

# --- SEO CONTENT DATABASE ---
CONTENT = {
    "en": {
        "nav": {"pages_view": "View .Pages", "pages_conv": "Convert Pages", "dat": "Open .DAT", "winmail": "Fix Winmail", "bin": "View .BIN"},
        "pages_view": {
            "title": "Open .Pages Online on Windows, Android & iPhone (Free)",
            "desc": "Need to open a .pages file on Android or Windows? Use our fast online viewer to read Apple Pages documents on any mobile device for free.",
            "h1": "View .Pages Files Online",
            "text": "<h2>How to open Pages on Android?</h2><p>Apple Pages files don't open on Android or Windows by default. Our web-based tool allows you to view documents instantly without installing any apps. Perfect for mobile users!</p>"
        },
        "pages_conv": {
            "title": "Convert Pages to PDF Online - Mobile Friendly",
            "desc": "Convert Apple .pages to PDF on Android, iOS or Windows. High-quality conversion with layout preservation. No app download needed.",
            "h1": "Convert Pages to PDF",
            "text": "<h2>Universal PDF Conversion</h2><p>Turn your Mac documents into universal PDFs. Ideal for students and professionals using Android tablets or Windows PCs.</p>"
        },
        "dat": { "title": "Open .DAT File Online - Android & PC", "desc": "Identify and view .dat file content on your mobile. Analyze binary data and extract text or images from unknown DAT files.", "h1": "DAT File Opener Online", "text": "<h2>What's inside that DAT?</h2><p>DAT files can be tricky on mobile. Upload it to see if it's a hidden video, text, or a system file.</p>" },
        "winmail": { "title": "Winmail.dat Opener for Android & Windows", "desc": "Received an email with winmail.dat? Extract attachments on your Android phone or PC easily.", "h1": "Winmail.dat Extractor", "text": "<h2>Fix Outlook Attachments</h2><p>Microsoft Outlook sometimes sends 'winmail.dat' files that Android can't read. We extract the original PDF or Word files for you.</p>" },
        "bin": { "title": "Online BIN File Viewer - Hex Editor for Mobile", "desc": "Read raw binary data (.bin) on your smartphone or PC. Online hex viewer for developers.", "h1": "View .BIN Files (Hex)", "text": "<h2>Hex Analysis</h2><p>Inspect file headers and binary structures directly in your mobile browser.</p>" }
    },
    "ru": {
        "nav": {"pages_view": "Смотреть Pages", "pages_conv": "Pages в PDF", "dat": "Открыть .DAT", "winmail": "Winmail.dat", "bin": "Открыть .BIN"},
        "pages_view": {
            "title": "Открыть файл .Pages онлайн на Android и Windows бесплатно",
            "desc": "Как открыть файл .pages на телефоне Андроид или ПК? Бесплатный просмотрщик документов Apple Pages онлайн. Без установки программ.",
            "h1": "Просмотр файлов .Pages онлайн",
            "text": "<h2>Как открыть Pages на Android?</h2><p>Документы Apple Pages не открываются на Android по умолчанию. Наш сервис позволяет прочитать файл .pages прямо в браузере мобильного телефона без скачивания приложений.</p>"
        },
        "pages_conv": {
            "title": "Конвертер Pages в PDF онлайн - Для телефона и ПК",
            "desc": "Преобразовать .pages в pdf на Андроид и Windows. Точная конвертация документов Apple с сохранением шрифтов и картинок.",
            "h1": "Конвертация Pages в PDF",
            "text": "<h2>Универсальный PDF</h2><p>Отправляя файл в формате PDF, вы гарантируете, что он откроется на любом смартфоне. Мы используем профессиональные движки для рендеринга.</p>"
        },
        "dat": { "title": "Чем открыть файл .DAT? Онлайн просмотр на Android", "desc": "Не знаете, как открыть файл dat на телефоне? Загрузите его сюда. Мы проанализируем структуру и покажем содержимое.", "h1": "Открыть файл .DAT онлайн", "text": "<h2>Что внутри DAT?</h2><p>Файлы DAT часто встречаются во вложениях. Наш инструмент помогает распознать в них фото, видео или текст прямо на мобильном.</p>" },
        "winmail": { "title": "Распаковщик Winmail.dat онлайн для Android", "desc": "Пришло письмо с winmail.dat? Извлеките из него вложения (Word, PDF) на своем смартфоне за секунду.", "h1": "Распаковка Winmail.dat", "text": "<h2>Проблема Outlook на мобильных</h2><p>Андроид не понимает формат TNEF (winmail.dat). Наш сервис извлекает реальные файлы из этого контейнера.</p>" },
        "bin": { "title": "Читалка BIN файлов онлайн - Hex для Андроид", "desc": "Просмотр бинарных файлов на смартфоне. Анализ Hex-кода онлайн через браузер.", "h1": "Просмотр .BIN файлов", "text": "<h2>Анализ данных</h2><p>Просматривайте содержимое прошивок и неизвестных файлов в шестнадцатеричном виде.</p>" }
    },
    "es": {
        "nav": {"pages_view": "Ver .Pages", "pages_conv": "Convertir Pages", "dat": "Abrir .DAT", "winmail": "Abrir Winmail", "bin": "Ver .BIN"},
        "pages_view": {
            "title": "Abrir archivos .Pages Online en Android y Windows Gratis",
            "desc": "¿Cómo abrir archivos .pages en el celular? Visor online gratuito para documentos de Apple. Compatible con Android, iOS y Windows.",
            "h1": "Ver archivos .Pages Online",
            "text": "<h2>Abrir Pages en Android</h2><p>Visualiza tus documentos de Apple directamente en el navegador de tu móvil. No necesitas instalar apps pesadas ni tener iCloud.</p>"
        },
        "pages_conv": {
            "title": "Convertir Pages a PDF Online - Gratis y Rápido",
            "desc": "El mejor conversor de Pages a PDF para móviles. Transforma documentos de Mac a PDF desde tu Android o PC.",
            "h1": "Convertir Pages a PDF",
            "text": "<h2>Formato Universal</h2><p>Convierte tus archivos a PDF para asegurar que se vean bien en cualquier smartphone o tablet.</p>"
        },
        "dat": { "title": "Abrir archivo .DAT Online - Identificador para Móvil", "desc": "¿Qué es un archivo .dat? Analiza y abre archivos desconocidos en tu Android. Extrae imágenes y texto.", "h1": "Abrir archivos .DAT", "text": "<h2>Análisis de Archivos</h2><p>Descubre qué programa creó ese archivo DAT directamente desde tu navegador móvil.</p>" },
        "winmail": { "title": "Descomprimir Winmail.dat en Android y Windows", "desc": "Recupera adjuntos de correos con winmail.dat en tu móvil. Extrae PDF y fotos de archivos Outlook.", "h1": "Extraer Winmail.dat", "text": "<h2>Problema de Outlook</h2><p>Muchos teléfonos no abren winmail.dat. Nosotros extraemos los archivos originales por ti.</p>" },
        "bin": { "title": "Visor de archivos .BIN - Editor Hex para Android", "desc": "Analiza datos binarios brutos en tu celular. Inspecciona cabeceras hexadecimales online.", "h1": "Visor de Archivos Binarios", "text": "<h2>Para Desarrolladores</h2><p>Herramienta móvil para inspeccionar el código hexadecimal de cualquier archivo.</p>" }
    },
    "pt": {
        "nav": {"pages_view": "Ver .Pages", "pages_conv": "Converter Pages", "dat": "Abrir .DAT", "winmail": "Winmail.dat", "bin": "Ver .BIN"},
        "pages_view": {
            "title": "Abrir arquivo .Pages Online no Android e Windows",
            "desc": "Como abrir arquivo .pages no celular? Visualizador online gratuito de documentos Apple Pages. Sem instalação.",
            "h1": "Ver Arquivos .Pages Online",
            "text": "<h2>Visualize no Android</h2><p>Abra arquivos do Pages no seu smartphone ou tablet facilmente. Basta arrastar o arquivo e nós o renderizamos.</p>"
        },
        "pages_conv": {
            "title": "Converter Pages em PDF Online Grátis - Mobile",
            "desc": "Converta documentos .pages para PDF no seu Android ou PC. Mantenha a formatação original sem apps.",
            "h1": "Converter Pages para PDF",
            "text": "<h2>Garanta Compatibilidade</h2><p>O formato PDF é universal. Converta seus trabalhos no celular para garantir que todos possam lê-los.</p>"
        },
        "dat": { "title": "Como abrir arquivo .DAT no celular? Leitor Online", "desc": "Descubra o conteúdo de arquivos .dat no seu Android. Análise de estrutura e extração de данных.", "h1": "Abrir Arquivos .DAT", "text": "<h2>O que é un arquivo DAT?</h2><p>Usamos análise binária no seu navegador para descobrir o conteúdo de arquivos DAT genéricos.</p>" },
        "winmail": { "title": "Abrir Winmail.dat no Android - Extrair Anexos", "desc": "Corrija anexos winmail.dat do Outlook no seu smartphone. Recupere documentos Word e PDF.", "h1": "Extrator Winmail.dat", "text": "<h2>Correção para Celular</h2><p>Seu celular não abre o winmail.dat? Nós extraímos os arquivos originais do formato da Microsoft.</p>" },
        "bin": { "title": "Visualizador .BIN Online - Hex Dump para Mobile", "desc": "Visualize o código binário de qualquer arquivo no seu smartphone. Ferramenta de análise técnica.", "h1": "Visualizador Binário", "text": "<h2>Análise Hexadecimal</h2><p>Veja os bytes brutos do arquivo para identificar cabeçalhos diretamente no celular.</p>" }
    }
}

# --- ЛОГИКА РЕНДЕРИНГА ---
async def render(request: Request, lang: str, tool_slug: str):
    if lang not in CONTENT: lang = "en"
    tool_id = URL_MAP.get(tool_slug, "pages_view")
    data = CONTENT[lang].get(tool_id, CONTENT["en"][tool_id])
    nav_labels = CONTENT[lang]["nav"]
    base = "https://filemaster.online"
    links = {l: (f"/{l}/{tool_slug}" if l != "en" else f"/{tool_slug}") for l in ["en", "ru", "es", "pt"]}
    nav_urls = {tid: (f"/{lang}/{t_slug}" if lang != "en" else f"/{t_slug}") for tid, t_slug in ID_TO_URL.items()}

    return templates.TemplateResponse("index.html", {
        "request": request, "lang": lang, "title": data["title"], "desc": data["desc"],
        "h1": data["h1"], "seo_text": data["text"], "nav_labels": nav_labels,
        "nav_urls": nav_urls, "lang_links": links, "current_tool_id": tool_id, "base_url": base
    })

# --- СЛУЖЕБНЫЕ МАРШРУТЫ (ДОЛЖНЫ БЫТЬ ПЕРВЫМИ) ---

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    file_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/x-icon")
    return Response(status_code=204)

@app.get("/robots.txt")
async def robots():
    return Response(content="User-agent: *\nAllow: /\nSitemap: https://filemaster.online/sitemap.xml", media_type="text/plain")

@app.get("/sitemap.xml")
async def sitemap():
    base_url = "https://filemaster.online"
    urls = [f"<url><loc>{base_url}/</loc><priority>1.0</priority></url>"]
    for slug in URL_MAP.keys(): urls.append(f"<url><loc>{base_url}/{slug}</loc><priority>0.9</priority></url>")
    for lang in ["ru", "es", "pt"]:
        urls.append(f"<url><loc>{base_url}/{lang}</loc><priority>0.8</priority></url>")
        for slug in URL_MAP.keys(): urls.append(f"<url><loc>{base_url}/{lang}/{slug}</loc><priority>0.8</priority></url>")
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{"".join(urls)}</urlset>'
    return Response(content=xml, media_type="application/xml")

# --- ГЛАВНЫЕ МАРШРУТЫ ---

@app.get("/")
async def root(request: Request):
    accept_lang = request.headers.get("accept-language", "")
    if accept_lang:
        first_lang = accept_lang.split(",")[0].split("-")[0].lower()
        if first_lang in ["ru", "es", "pt"]:
            return RedirectResponse(url=f"/{first_lang}")
    return await render(request, "en", "pages-viewer")

@app.get("/{slug}")
async def tool_en(request: Request, slug: str):
    if slug in URL_MAP: return await render(request, "en", slug)
    if slug in CONTENT: return await render(request, slug, "pages-viewer")
    return JSONResponse(status_code=404, content={"message": "Not Found"})

@app.get("/{lang}/{slug}")
async def tool_lang(request: Request, lang: str, slug: str):
    if lang in CONTENT and slug in URL_MAP: return await render(request, lang, slug)
    return JSONResponse(status_code=404, content={"message": "Not Found"})

@app.get("/{lang}")
async def root_lang(request: Request, lang: str):
    if lang in CONTENT: return await render(request, lang, "pages-viewer")
    return JSONResponse(status_code=404, content={"message": "Not Found"})

# --- API ---

@app.post("/convert-pages")
def convert_pages(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(input_path, "wb") as b: shutil.copyfileobj(file.file, b)
    try:
        subprocess.run([LIBREOFFICE_PATH, '--headless', '--convert-to', 'pdf', '--outdir', UPLOAD_DIR, input_path], check=True)
        pdf_name = f"{file_id}_{file.filename.rsplit('.', 1)[0]}.pdf"
        return {"status": "success", "url": f"/download/{pdf_name}", "name": pdf_name}
    except: return JSONResponse(status_code=500, content={"message": "Error"})

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    path = os.path.join(UPLOAD_DIR, file_name)
    return FileResponse(path) if os.path.exists(path) else HTTPException(404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
