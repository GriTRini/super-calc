from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import phone  # 다른 라우터 제거, phone만 남김

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 폰 계산기 라우터 등록
app.include_router(phone.router)

# [SEO] Robots.txt
@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    # 실제 도메인으로 변경하세요
    content = """User-agent: *
Allow: /
Sitemap: https://super-calc.onrender.com/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")

# [SEO] Sitemap.xml (구조가 단순해짐)
@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    base_url = "https://super-calc.onrender.com"
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <priority>1.0</priority>
        <changefreq>daily</changefreq>
    </url>
</urlset>
"""
    return Response(content=content, media_type="application/xml")