from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/severance")
async def show_severance_page(request: Request):
    return templates.TemplateResponse("severance.html", {"request": request, "result": None})

@router.post("/severance/calc")
async def calculate_severance(
    request: Request,
    start_date: str = Form(...),       # 입사일 (YYYY-MM-DD)
    end_date: str = Form(...),         # 퇴사일 (YYYY-MM-DD)
    monthly_salary: int = Form(...),   # 월 기본급
    annual_bonus: int = Form(default=0), # 연간 상여금
    annual_leave: int = Form(default=0)  # 연차 수당
):
    # 1. 날짜 파싱
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # 2. 재직일수 계산 (퇴사일 - 입사일)
    # 보통 퇴직금 산정시 퇴사일은 근무 마지막 다음날로 보지만, 
    # 계산기 편의상 입력한 날짜까지 근무한 것으로 간주하여 +1일 처리하거나 차이 계산
    service_days = (end - start).days
    
    if service_days < 365:
        # 1년 미만은 원칙적으로 퇴직금 없음 (경고용)
        is_eligible = False
    else:
        is_eligible = True

    # 3. 퇴사 전 3개월 기간 계산 (평균임금 산정용)
    # 퇴사일로부터 3개월 전 날짜 구하기
    # (정확한 3개월 일수 계산: 89일~92일 변동)
    three_months_ago = end - timedelta(days=91) # 대략적 계산 (법적으로는 역에 의한 3개월)
    
    # 실제 3개월 간의 총 일수 (분모)
    three_months_days = (end - three_months_ago).days
    
    # 4. 3개월 간의 임금 총액 (분자)
    # (1) 3개월치 월급 (기본급 * 3)
    # *참고: 실제로는 월할 계산해야 하나, '최근 3개월 동일' 옵션 기준으로 단순화
    total_3m_salary = monthly_salary * 3
    
    # (2) 상여금 가산 (연간 상여금 * 3/12)
    bonus_part = annual_bonus * (3/12)
    
    # (3) 연차수당 가산 (연차수당 * 3/12)
    leave_part = annual_leave * (3/12)
    
    total_wages_3m = total_3m_salary + bonus_part + leave_part

    # 5. 1일 평균임금 계산
    avg_daily_wage = total_wages_3m / three_months_days

    # 6. 최종 퇴직금 계산
    # 공식: 1일 평균임금 * 30일 * (재직일수 / 365)
    severance_pay = avg_daily_wage * 30 * (service_days / 365)
    
    # 정수 변환 (원 단위 절사)
    severance_pay = int(severance_pay // 10) * 10
    avg_daily_wage = int(avg_daily_wage // 10) * 10

    return templates.TemplateResponse("severance.html", {
        "request": request,
        "result": True,
        "is_eligible": is_eligible,
        "start_date": start_date,
        "end_date": end_date,
        "service_days": service_days,
        "avg_daily_wage": avg_daily_wage,
        "severance_pay": severance_pay,
        
        # 입력값 유지
        "monthly_salary": monthly_salary,
        "annual_bonus": annual_bonus,
        "annual_leave": annual_leave
    })