from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import salary # 다른 계산기를 만들면 여기에 import 추가

app = FastAPI()

# 정적 파일(CSS) 연결
app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 라우터 등록 (기능 연결)
app.include_router(salary.router)

# 메인 홈 라우터
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# (선택사항) 로컬에서 바로 실행할 때를 위한 코드
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)