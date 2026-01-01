from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
import json
import os
import math

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 1. 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(root_dir, "phones.json")

# 2. 데이터 로드
def load_phone_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {str(item['id']): item for item in data}
            return data
    except Exception as e:
        return {}

# [GET] 메인 화면
@router.get("/")
async def show_home(request: Request):
    phones = load_phone_db()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "phones": phones,
        "result": None
    })

# [POST] 계산 로직
@router.post("/calc")
async def calculate(
    request: Request,
    phone_code: str = Form(...),
    device_price: int = Form(...),
    mvno_cost: int = Form(default=0),
    plan_cost: int = Form(default=0),
    plan_period: int = Form(default=6),
    plan_cost_after: int = Form(default=0),
    carrier_type: str = Form(...),
    subsidy: int = Form(default=0),
    store_subsidy: int = Form(default=0),
    addon_cost: int = Form(default=0),
    addon_months: int = Form(default=0),
    
    # [수정] 할인 관련 파라미터 2개
    add_discount: int = Form(default=0),           # 입력 숫자
    add_discount_type: str = Form(default="amount") # amount(원) 또는 rate(%)
):
    phones = load_phone_db()
    
    # 자급제 계산
    self_total = device_price + (mvno_cost * 24)

    # 통신사 계산
    carrier_principal = 0
    carrier_method_text = ""
    
    period_a = plan_period
    period_b = 24 - plan_period
    if period_b < 0: period_b = 0
    final_plan_after = plan_cost_after if plan_cost_after > 0 else plan_cost
    plan_total_cost = 0

    if carrier_type == "gongsi":
        carrier_principal = device_price - subsidy - store_subsidy
        carrier_method_text = "공시지원금"
        # 요금제 총액 (할인 전)
        plan_total_cost = (plan_cost * period_a) + (final_plan_after * period_b)
    else: 
        carrier_principal = device_price - store_subsidy
        carrier_method_text = "선택약정(25%)"
        # 선택약정 25% 적용
        cost_a_discounted = int(plan_cost * 0.75)
        cost_b_discounted = int(final_plan_after * 0.75)
        plan_total_cost = (cost_a_discounted * period_a) + (cost_b_discounted * period_b)

    # -------------------------------------------------------
    # [핵심 로직] 추가 월 할인 계산 (금액 vs 비율)
    # -------------------------------------------------------
    monthly_discount_amount = 0
    
    if add_discount_type == "rate":
        # 비율(%) 할인인 경우: 요금제의 N%를 계산
        # (주의: 기간별 요금제가 다르므로 각각 계산해서 합산하거나, 평균을 내야 함.
        #  여기서는 편의상 '현재 적용되는 요금제' 기준으로 각각 깎아줍니다.)
        
        # 기간 A 할인액 (월)
        discount_a = int(plan_cost * (add_discount / 100))
        # 기간 B 할인액 (월)
        discount_b = int(final_plan_after * (add_discount / 100))
        
        # 총 할인액 = (기간A 할인 * 개월수) + (기간B 할인 * 개월수)
        total_discount = (discount_a * period_a) + (discount_b * period_b)
        
        # 결과 표기를 위해 평균 월 할인액으로 저장 (참고용)
        monthly_discount_amount = int(total_discount / 24)
        
        # 총 통신비에서 차감
        plan_total_cost -= total_discount

    else:
        # 금액(원) 할인인 경우: 입력된 금액 * 24개월
        monthly_discount_amount = add_discount
        plan_total_cost -= (add_discount * 24)
    # -------------------------------------------------------

    if carrier_principal < 0: carrier_principal = 0

    carrier_interest = 0
    if carrier_principal > 0:
        annual_rate = 0.059
        monthly_rate = annual_rate / 12
        months = 24
        monthly_payment = carrier_principal * (monthly_rate * math.pow(1 + monthly_rate, months)) / (math.pow(1 + monthly_rate, months) - 1)
        carrier_interest = int((monthly_payment * 24) - carrier_principal)
    
    addon_total_cost = addon_cost * addon_months
    carrier_total = int(carrier_principal + carrier_interest + plan_total_cost + addon_total_cost)

    # 승자 판정
    needed_additional_subsidy = 0
    target_monthly_plan = 0

    if self_total < carrier_total:
        winner = "self"
        diff_price = carrier_total - self_total
        recommend_text = "자급제 + 알뜰폰 승리!"
        needed_additional_subsidy = diff_price
        target_plan_total = plan_total_cost - diff_price
        if target_plan_total < 0:
            target_monthly_plan = 0
        else:
            if carrier_type == "seonyak":
                target_monthly_plan = int((target_plan_total / 24) / 0.75)
            else:
                target_monthly_plan = int(target_plan_total / 24)
    else:
        winner = "carrier"
        diff_price = self_total - carrier_total
        recommend_text = f"통신사 ({carrier_method_text}) 승리!"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "phones": phones,
        "selected_code": phone_code,
        "result": True,
        
        "input_price": device_price,
        "input_mvno": mvno_cost,
        "input_plan": plan_cost,
        "input_plan_period": plan_period,
        "input_plan_after": plan_cost_after,
        "carrier_type": carrier_type,
        "input_subsidy": subsidy,
        "input_store_subsidy": store_subsidy,
        "input_addon_cost": addon_cost,
        "input_addon_months": addon_months,
        
        # [수정] 할인 관련 값 반환
        "input_add_discount": add_discount,
        "input_add_discount_type": add_discount_type,
        
        "self_total": self_total,
        "carrier_total": carrier_total,
        "carrier_principal": carrier_principal,
        "carrier_interest": carrier_interest,
        "plan_total_cost": plan_total_cost,
        "addon_total_cost": addon_total_cost,
        "carrier_method_text": carrier_method_text,
        "winner": winner,
        "recommend_text": recommend_text,
        "diff_price": diff_price,
        "needed_additional_subsidy": needed_additional_subsidy,
        "target_monthly_plan": target_monthly_plan
    })