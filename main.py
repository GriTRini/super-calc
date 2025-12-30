from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import salary, real_estate, severance, phone

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 라우터 등록
app.include_router(salary.router)
app.include_router(real_estate.router)
app.include_router(severance.router)
app.include_router(phone.router)

# 1. 메인 홈
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 2. [SEO] Robots.txt (검색 로봇 환영 메시지)
@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    # 사이트맵 주소를 실제 배포 주소로 바꿔주세요!
    content = """User-agent: *
Allow: /
Sitemap: https://YOUR-APP-NAME.onrender.com/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")

# 3. [SEO] Sitemap.xml (사이트 지도)
@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    # 실제 배포 주소로 꼭 변경하세요! (예: https://super-calc-123.onrender.com)
    base_url = "https://super-calc.onrender.com"
    
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{base_url}/salary</loc>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/real-estate</loc>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{base_url}/severance</loc>
        <priority>0.8</priority>
    </url>
</urlset>
"""
    return Response(content=content, media_type="application/xml")