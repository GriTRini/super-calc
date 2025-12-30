from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 1. 입력 화면 보여주기
@router.get("/salary")
async def show_salary_page(request: Request):
    return templates.TemplateResponse("salary.html", {
        "request": request,
        "result": None # 처음엔 결과 없음
    })

# 2. 계산 실행 및 결과 보여주기
@router.post("/salary/calc")
async def calculate_salary(request: Request, income: int = Form(...)):
    # 3.3% 세금 계산 로직
    tax = int(income * 0.033)
    result = income - tax
    
    return templates.TemplateResponse("salary.html", {
        "request": request,
        "original": income,
        "tax": tax,
        "result": result
    })