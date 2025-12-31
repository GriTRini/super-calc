from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from routers import phone  # routers 폴더의 phone.py 가져오기

app = FastAPI()

# 1. 정적 파일 마운트 (CSS, JS, 이미지)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. 라우터 등록
app.include_router(phone.router)

# ==========================================================
# [모니터링] 서버 절전 방지용 (UptimeRobot 연결)
# ==========================================================
@app.get("/ping")
async def ping():
    return {"status": "alive"}

# ==========================================================
# [SEO] 검색엔진 최적화 및 소유권 확인
# ==========================================================
@app.get("/google30ad8eaea48a0cb8.html", include_in_schema=False)
async def google_verification():
    return Response(content="google-site-verification: google30ad8eaea48a0cb8", media_type="text/html")

@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    content = """User-agent: *
Allow: /
Sitemap: https://super-calc.onrender.com/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")

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