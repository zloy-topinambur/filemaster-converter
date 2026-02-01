from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
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

# Подключаем шаблоны
templates = Jinja2Templates(directory=BASE_DIR)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Путь к LibreOffice (Linux/Docker)
LIBREOFFICE_PATH = "soffice"

# --- URL MAPPING (Красивые ссылки для SEO) ---
# Ключ в URL -> Внутренний ID инструмента
URL_MAP = {
    "pages-viewer": "pages_view",
    "pages-to-pdf": "pages_conv",
    "open-dat-file": "dat",
    "winmail-dat-opener": "winmail",
    "view-bin-file": "bin"
}
# Обратный маппинг
ID_TO_URL = {v: k for k, v in URL_MAP.items()}

# --- SEO CONTENT DATABASE (4 ЯЗЫКА) ---
CONTENT = {
    "en": {
        "nav": {
            "pages_view": "View .Pages",
            "pages_conv": "Convert Pages",
            "dat": "Open .DAT",
            "winmail": "Fix Winmail",
            "bin": "View .BIN"
        },
        "pages_view": {
            "title": "Open .Pages Files Online on Windows & Android (Free Viewer)",
            "desc": "How to open .pages files without a Mac? Use our free online viewer. Read Apple Pages documents on Windows 10, 11, and Android instantly.",
            "h1": "View .Pages Files Online Free",
            "text": "<h2>How to open Pages file on PC?</h2><p>Apple Pages documents are not compatible with Microsoft Word by default. Our tool renders them in your browser safely.</p><h3>Features:</h3><ul><li>No software installation required</li><li>Works on Windows, Linux, Android</li><li>Secure & Private</li></ul>"
        },
        "pages_conv": {
            "title": "Convert Pages to PDF Online - Free & Secure",
            "desc": "Best free Pages to PDF converter. Transform Apple .pages documents into PDF format keeping fonts and layout. No registration needed.",
            "h1": "Convert Pages to PDF",
            "text": "<h2>Why convert to PDF?</h2><p>PDF is the universal standard for documents. Converting your Pages file ensures the recipient sees it exactly as you designed it.</p><ul><li>Preserves Fonts & Images</li><li>ISO Standard PDF</li><li>Automatic Deletion</li></ul>"
        },
        "dat": {
            "title": "Open .DAT File Online - Identify & View Content",
            "desc": "What is a .dat file? Upload it here to analyze the file signature (magic bytes) and view the hidden content (text, image, or video).",
            "h1": "Open .DAT Files Online",
            "text": "<h2>What is a DAT file?</h2><p>DAT stands for 'Data'. It's a generic container. Our tool analyzes the binary structure to determine if it's a picture, text, or a known application format.</p>"
        },
        "winmail": {
            "title": "Winmail.dat Opener - Extract Outlook Attachments",
            "desc": "Received a winmail.dat file? Extract PDF, Word, and Excel attachments from Outlook TNEF messages online.",
            "h1": "Winmail.dat Extractor",
            "text": "<h2>Fix Outlook Attachments</h2><p>When Outlook sends emails in RTF format, attachments often get wrapped in <strong>winmail.dat</strong>. We decode this proprietary TNEF format to recover your original files.</p>"
        },
        "bin": {
            "title": "Binary File Viewer - Online Hex Editor",
            "desc": "View raw binary data of any file. Inspect headers, hex code, and file structure online for free.",
            "h1": "View .BIN Files (Hex)",
            "text": "<h2>For Developers</h2><p>Inspect the raw hexadecimal representation of any file. Useful for debugging firmware, analyzing unknown file headers, and data recovery.</p>"
        }
    },
    "ru": {
        "nav": {
            "pages_view": "Смотреть Pages",
            "pages_conv": "Pages в PDF",
            "dat": "Открыть .DAT",
            "winmail": "Winmail.dat",
            "bin": "Открыть .BIN"
        },
        "pages_view": {
            "title": "Открыть файл .Pages онлайн на Windows и Android бесплатно",
            "desc": "Чем открыть файл .pages на компьютере? Онлайн просмотрщик документов Apple Pages для Windows. Без установки программ и регистрации.",
            "h1": "Просмотр файлов .Pages онлайн",
            "text": "<h2>Как открыть Pages на Windows?</h2><p>Windows не умеет открывать файлы .pages. Наш сервис решает эту проблему. Просто перетащите файл, и мы покажем его содержимое.</p><h3>Преимущества:</h3><ul><li>Работает на любом устройстве</li><li>Не нужно покупать Mac</li><li>Полностью бесплатно</li></ul>"
        },
        "pages_conv": {
            "title": "Конвертер Pages в PDF онлайн - Сохранение верстки",
            "desc": "Преобразовать .pages в pdf бесплатно. Точная конвертация документов Apple с сохранением шрифтов и картинок.",
            "h1": "Конвертация Pages в PDF",
            "text": "<h2>Зачем конвертировать в PDF?</h2><p>Отправляя файл в формате PDF, вы гарантируете, что он откроется у коллеги или преподавателя. Мы используем профессиональные движки рендеринга для лучшего качества.</p>"
        },
        "dat": {
            "title": "Чем открыть файл .DAT? Онлайн анализ и просмотр",
            "desc": "Не знаете, как открыть файл dat? Загрузите его сюда. Мы проанализируем структуру и покажем текст, фото или видео, скрытое внутри.",
            "h1": "Открыть файл .DAT онлайн",
            "text": "<h2>Что такое файл DAT?</h2><p>Это контейнер с данными. Внутри может быть что угодно: от сохранения игры до видео VCD. Мы анализируем 'цифровую подпись' файла, чтобы определить его реальный формат.</p>"
        },
        "winmail": {
            "title": "Распаковщик Winmail.dat онлайн - Открыть вложения",
            "desc": "Пришло письмо с вложением winmail.dat? Извлеките из него нормальные файлы (Word, Excel, PDF) за секунду.",
            "h1": "Распаковка Winmail.dat",
            "text": "<h2>Проблема Outlook</h2><p>Формат TNEF (winmail.dat) создается Outlook-ом. Другие почтовые клиенты его не понимают. Наш инструмент извлекает ваши файлы из этого контейнера.</p>"
        },
        "bin": {
            "title": "Читалка BIN файлов онлайн - Hex редактор",
            "desc": "Просмотр бинарных файлов. Анализ заголовков и структуры Hex-кода онлайн.",
            "h1": "Просмотр .BIN файлов",
            "text": "<h2>Инструмент для гиков</h2><p>Позволяет увидеть 'внутренности' файла в шестнадцатеричном формате. Полезно для анализа неизвестных форматов данных.</p>"
        }
    },
    "es": {
        "nav": {
            "pages_view": "Ver .Pages",
            "pages_conv": "Convertir Pages",
            "dat": "Abrir .DAT",
            "winmail": "Abrir Winmail",
            "bin": "Ver .BIN"
        },
        "pages_view": {
            "title": "Abrir archivos .Pages Online en Windows y Android Gratis",
            "desc": "¿Cómo abrir archivos .pages en PC? Visor online gratuito para documentos de Apple. Compatible con Windows 10 y Android.",
            "h1": "Ver archivos .Pages Online",
            "text": "<h2>Abrir Pages sin Mac</h2><p>Visualiza tus documentos de Apple directamente en el navegador. No necesitas instalar software adicional ni tener una cuenta de iCloud.</p>"
        },
        "pages_conv": {
            "title": "Convertir Pages a PDF Online - Gratis",
            "desc": "El mejor conversor de Pages a PDF. Transforma documentos de Mac a formato universal PDF manteniendo el formato.",
            "h1": "Convertir Pages a PDF",
            "text": "<h2>Formato Universal</h2><p>Convierte tus archivos a PDF para asegurar la máxima compatibilidad. Tus documentos se verán igual en cualquier dispositivo.</p>"
        },
        "dat": {
            "title": "Abrir archivo .DAT Online - Identificador de archivos",
            "desc": "¿Qué es un archivo .dat? Analiza y abre archivos desconocidos. Extrae imágenes y texto de archivos genéricos.",
            "h1": "Abrir archivos .DAT",
            "text": "<h2>Análisis de Archivos</h2><p>Analizamos la cabecera del archivo (Magic Bytes) para descubrir qué programa creó este archivo DAT y mostrarte su contenido.</p>"
        },
        "winmail": {
            "title": "Descomprimir Winmail.dat Online",
            "desc": "Recupera adjuntos de correos con winmail.dat. Extrae PDF, Docx y fotos de archivos TNEF de Outlook.",
            "h1": "Extraer Winmail.dat",
            "text": "<h2>Problema de Outlook</h2><p>Decodificamos el formato TNEF de Microsoft para que puedas acceder a los archivos adjuntos originales bloqueados en el archivo winmail.dat.</p>"
        },
        "bin": {
            "title": "Visor de archivos .BIN - Editor Hex",
            "desc": "Analiza datos binarios brutos. Inspecciona cabeceras hexadecimales online.",
            "h1": "Visor de Archivos Binarios",
            "text": "<h2>Para Desarrolladores</h2><p>Herramienta para inspeccionar el código hexadecimal de cualquier archivo. Útil para ingeniería inversa y análisis de datos.</p>"
        }
    },
    "pt": {
        "nav": {
            "pages_view": "Ver .Pages",
            "pages_conv": "Converter Pages",
            "dat": "Abrir .DAT",
            "winmail": "Winmail.dat",
            "bin": "Ver .BIN"
        },
        "pages_view": {
            "title": "Abrir arquivo .Pages Online no Windows e Android",
            "desc": "Como abrir arquivo .pages no PC? Visualizador online gratuito de documentos Apple Pages. Sem instalação.",
            "h1": "Ver Arquivos .Pages Online",
            "text": "<h2>Visualize documentos Apple</h2><p>Abra arquivos do Pages no Windows ou Linux facilmente. Basta arrastar o arquivo e nós o renderizamos no navegador.</p>"
        },
        "pages_conv": {
            "title": "Converter Pages em PDF Online Grátis",
            "desc": "Converta documentos .pages para PDF rapidamente. Mantenha a formatação original, fontes e imagens.",
            "h1": "Converter Pages para PDF",
            "text": "<h2>Garanta Compatibilidade</h2><p>O formato PDF é seguro e universal. Converta seus trabalhos escolares ou contratos para garantir que todos possam lê-los.</p>"
        },
        "dat": {
            "title": "Como abrir arquivo .DAT? Leitor Online",
            "desc": "Descubra o conteúdo de arquivos .dat desconhecidos. Análise de estrutura e extração de dados.",
            "h1": "Abrir Arquivos .DAT",
            "text": "<h2>O que é um arquivo DAT?</h2><p>É um arquivo de dados genérico. Usamos análise binária para descobrir o verdadeiro formato e exibir o conteúdo para você.</p>"
        },
        "winmail": {
            "title": "Abrir Winmail.dat Online - Extrair Anexos",
            "desc": "Corrija anexos winmail.dat do Outlook. Recupere seus documentos Word, Excel e PDF originais.",
            "h1": "Extrator Winmail.dat",
            "text": "<h2>Correção para Outlook</h2><p>Seus anexos sumiram? Nós extraímos os arquivos originais do formato proprietário TNEF da Microsoft.</p>"
        },
        "bin": {
            "title": "Visualizador .BIN Online - Hex Dump",
            "desc": "Visualize o código binário de qualquer arquivo. Ferramenta para análise técnica e forense.",
            "h1": "Visualizador Binário",
            "text": "<h2>Análise Hexadecimal</h2><p>Veja os bytes brutos do arquivo para identificar cabeçalhos ou recuperar dados corrompidos.</p>"
        }
    }
}

# --- ЛОГИКА РЕНДЕРИНГА ---
async def render(request: Request, lang: str, tool_slug: str):
    # Fallbacks
    if lang not in CONTENT: lang = "en"
    tool_id = URL_MAP.get(tool_slug, "pages_view")
    
    # Get Data
    data = CONTENT[lang].get(tool_id, CONTENT["en"][tool_id])
    nav_labels = CONTENT[lang]["nav"]
    
    # Hreflangs & Links Generation
    base = "https://filemaster.online"
    # Генерируем ссылки на текущий инструмент для всех языков
    links = {}
    for l in ["en", "ru", "es", "pt"]:
        prefix = f"/{l}" if l != "en" else ""
        links[l] = f"{prefix}/{tool_slug}"

    # Генерируем навигацию для текущего языка
    nav_urls = {}
    lang_prefix = f"/{lang}" if lang != "en" else ""
    for tid, t_slug in ID_TO_URL.items():
        nav_urls[tid] = f"{lang_prefix}/{t_slug}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "lang": lang,
        "title": data["title"],
        "desc": data["desc"],
        "h1": data["h1"],
        "seo_text": data["text"],
        "nav_labels": nav_labels,
        "nav_urls": nav_urls,
        "lang_links": links,
        "current_tool_id": tool_id,
        "base_url": base
    })

# --- МАРШРУТЫ ---

@app.get("/sitemap.xml")
async def sitemap():
    base = "https://filemaster.online"
    urls = []
    # Generate all combinations
    for lang in ["en", "ru", "es", "pt"]:
        prefix = f"/{lang}" if lang != "en" else ""
        for slug in URL_MAP.keys():
            urls.append(f"<url><loc>{base}{prefix}/{slug}</loc><changefreq>weekly</changefreq></url>")
            
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        {''.join(urls)}
    </urlset>"""
    return JSONResponse(content=xml, media_type="application/xml")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    p = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(p): return FileResponse(p)
    return JSONResponse(status_code=204)

# 1. Routes EN (Default)
@app.get("/")
async def root(request: Request):
    return await render(request, "en", "pages-viewer")

@app.get("/{slug}")
async def tool_en(request: Request, slug: str):
    if slug in URL_MAP: return await render(request, "en", slug)
    return JSONResponse(status_code=404, content={"message": "Not Found"})

# 2. Routes Langs
@app.get("/{lang}/{slug}")
async def tool_lang(request: Request, lang: str, slug: str):
    if lang in CONTENT and slug in URL_MAP:
        return await render(request, lang, slug)
    return JSONResponse(status_code=404, content={"message": "Not Found"})

@app.get("/{lang}")
async def root_lang(request: Request, lang: str):
    if lang in CONTENT:
        return await render(request, lang, "pages-viewer")
    return JSONResponse(status_code=404, content={"message": "Not Found"})

# --- API ENDPOINTS (Оставлены как есть) ---
@app.post("/convert-pages")
def convert_pages(file: UploadFile = File(...)):
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
