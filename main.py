from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import salary, real_estate, severance

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 라우터 등록
app.include_router(salary.router)
app.include_router(real_estate.router)  # <--- [수정 2] 이 줄 추가!
app.include_router(severance.router)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})