from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/salary")
async def show_salary_page(request: Request):
    return templates.TemplateResponse("salary.html", {"request": request, "result": None})

@router.post("/salary/calc")
async def calculate_salary(
    request: Request,
    calc_type: str = Form(...),       # salary(직장인), hourly(알바), freelancer
    
    # [직장인/프리랜서용 입력]
    amount: int = Form(default=0),
    salary_type: str = Form(default="year"),
    severance_type: str = Form(default="separate"),
    
    # [알바용 입력]
    hourly_wage: int = Form(default=0),        # 시급
    daily_hours: int = Form(default=8),        # 일일 근무시간
    weekly_days: int = Form(default=5),        # 주 근무일수
    overtime_hours: int = Form(default=0),     # 월 연장근무
    juhyu_state: str = Form(default="excluded"), # 주휴수당 (included/excluded)
    tax_type: str = Form(default="none"),      # 세금 (none, 3.3, 4major)
    probation: str = Form(default="no"),       # 수습 (yes/no)

    # [공통 옵션]
    non_taxable: int = Form(default=200000),
    dependents: int = Form(default=1),
    children: int = Form(default=0)
):
    # 결과 변수 초기화
    monthly_salary = 0  # 세전 월급
    base_hourly_rate = 0 # 적용 시급 (수습 적용 후)
    holiday_pay = 0     # 주휴수당
    overtime_pay = 0    # 연장수당
    
    pension = 0; health = 0; care = 0; employ = 0
    tax = 0; local_tax = 0; total_tax = 0
    final_pay = 0

    # -----------------------------------------------
    # 1. 세전 월급(Monthly Salary) 계산
    # -----------------------------------------------
    if calc_type == "salary": # 직장인
        if salary_type == "year":
            monthly_salary = int(amount / 13) if severance_type == "included" else int(amount / 12)
        else:
            monthly_salary = amount

    elif calc_type == "hourly": # 알바 (로직 고도화)
        # (1) 시급 결정 (수습 적용 여부)
        base_hourly_rate = hourly_wage
        if probation == "yes":
            base_hourly_rate = int(hourly_wage * 0.9) # 90% 적용

        # (2) 주간 기본 근무 시간
        weekly_hours = daily_hours * weekly_days
        
        # (3) 월 기본급 (4.345주 기준)
        # 월 소정근로시간 = 주당시간 * 4.345
        monthly_base_pay = weekly_hours * 4.345 * base_hourly_rate
        
        # (4) 주휴수당 계산
        # 주 15시간 이상 근무 & 포함 선택 시
        if juhyu_state == "included" and weekly_hours >= 15:
            # 주휴시간: (주40시간 기준 비례) min(40, 주근로시간) / 40 * 8
            # 통상 주 5일 40시간이면 8시간, 주 20시간이면 4시간
            juhyu_hours_per_week = (min(weekly_hours, 40) / 40) * 8
            holiday_pay = int(juhyu_hours_per_week * 4.345 * base_hourly_rate)
        
        # (5) 연장 수당 (1.5배)
        overtime_pay = int(overtime_hours * base_hourly_rate * 1.5)

        monthly_salary = int(monthly_base_pay + holiday_pay + overtime_pay)

    elif calc_type == "freelancer": # 프리랜서
        monthly_salary = amount
        non_taxable = 0 

    # 10원 단위 절사
    monthly_salary = (monthly_salary // 10) * 10


    # -----------------------------------------------
    # 2. 공제액 계산 (세금)
    # -----------------------------------------------
    # 알바 세금 유형 처리
    calc_tax_method = "4major" # 기본값
    
    if calc_type == "hourly":
        if tax_type == "none":
            calc_tax_method = "none"
        elif tax_type == "3.3":
            calc_tax_method = "freelancer" # 3.3% 계산 로직과 동일
        else:
            calc_tax_method = "4major"
    elif calc_type == "freelancer":
        calc_tax_method = "freelancer"
    
    # --- 실제 세금 계산 실행 ---
    if calc_tax_method == "none":
        total_tax = 0
        final_pay = monthly_salary
        
    elif calc_tax_method == "freelancer":
        total_tax = int(monthly_salary * 0.033)
        final_pay = monthly_salary - total_tax

    else: # 4대보험 (직장인 or 알바 4대보험)
        tax_base = monthly_salary - non_taxable
        if tax_base < 0: tax_base = 0

        pension = int(tax_base * 0.045)
        if pension > 277650: pension = 277650 # 상한액 약식
        
        health = int(tax_base * 0.03545)
        care = int(health * 0.1295)
        employ = int(tax_base * 0.009)

        # 소득세 (간이세액 약식)
        family_deduction = (dependents + children) * 150000 
        income_tax_base = tax_base - family_deduction - (pension+health+care+employ)
        if income_tax_base < 0: income_tax_base = 0

        if monthly_salary < 1060000: tax = 0
        elif monthly_salary < 3000000: tax = int(income_tax_base * 0.015) 
        elif monthly_salary < 5000000: tax = int(income_tax_base * 0.045) 
        elif monthly_salary < 10000000: tax = int(income_tax_base * 0.10)
        else: tax = int(income_tax_base * 0.20)
        
        if children > 0 and tax > 0: tax -= (children * 10000)
        if tax < 0: tax = 0
        
        tax = (tax // 10) * 10
        local_tax = int(tax * 0.1)
        local_tax = (local_tax // 10) * 10

        total_tax = pension + health + care + employ + tax + local_tax
        final_pay = monthly_salary - total_tax

    final_pay = (final_pay // 10) * 10

    return templates.TemplateResponse("salary.html", {
        "request": request,
        "calc_type": calc_type,
        "salary_type": salary_type,
        "monthly_salary": monthly_salary,
        "base_hourly_rate": base_hourly_rate, # 추가: 시급
        "holiday_pay": holiday_pay,           # 추가: 주휴수당
        "overtime_pay": overtime_pay,         # 추가: 연장수당
        "pension": pension,
        "health": health,
        "care": care,
        "employ": employ,
        "income_tax": tax,
        "local_tax": local_tax,
        "total_tax": total_tax,
        "result": final_pay
    })