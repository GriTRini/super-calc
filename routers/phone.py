from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
import json
import os
import math

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 1. 경로 설정 (phones.json 위치 찾기)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(root_dir, "phones.json")

# 2. JSON 데이터 로드 함수
def load_phone_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {str(item['id']): item for item in data}
            return data
    except Exception as e:
        print(f"DB Load Error: {e}")
        return {}

# ---------------------------------------------------------
# [GET] 메인 화면
# ---------------------------------------------------------
@router.get("/")
async def show_home(request: Request):
    phones = load_phone_db()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "phones": phones,
        "result": None
    })

# ---------------------------------------------------------
# [POST] 계산 및 분석 로직
# ---------------------------------------------------------
@router.post("/calc")
async def calculate(
    request: Request,
    phone_code: str = Form(...),
    device_price: int = Form(...),          # 기기값
    mvno_cost: int = Form(default=0),       # 알뜰폰 요금
    
    # [요금제 관련]
    plan_cost: int = Form(default=0),       # 초기 요금제
    plan_period: int = Form(default=6),     # 초기 유지 기간
    plan_cost_after: int = Form(default=0), # 변경 후 요금제
    
    carrier_type: str = Form(...),          # gongsi / seonyak
    subsidy: int = Form(default=0),         # 공시지원금
    store_subsidy: int = Form(default=0),   # 대리점 징
    
    # [부가서비스]
    addon_cost: int = Form(default=0),      # 월 금액
    addon_months: int = Form(default=0),    # 유지 기간
    
    add_discount: int = Form(default=0)     # 추가 월 할인
):
    phones = load_phone_db()
    
    # --- [A] 자급제 + 알뜰폰 (2년 총액) ---
    self_total = device_price + (mvno_cost * 24)

    # --- [B] 통신사 약정 (2년 총액) ---
    carrier_principal = 0
    carrier_method_text = ""
    
    # B-1. 요금제 기간별 비용 계산
    period_a = plan_period
    period_b = 24 - plan_period
    if period_b < 0: period_b = 0

    final_plan_after = plan_cost_after if plan_cost_after > 0 else plan_cost
    plan_total_cost = 0

    if carrier_type == "gongsi":
        # [공시] 할부원금 = 기기값 - 공시 - 징
        carrier_principal = device_price - subsidy - store_subsidy
        carrier_method_text = "공시지원금"
        # 요금 할인 없음
        plan_total_cost = (plan_cost * period_a) + (final_plan_after * period_b)

    else: 
        # [선약] 할부원금 = 기기값 - 징 (공시 0)
        carrier_principal = device_price - store_subsidy
        carrier_method_text = "선택약정(25%)"
        # 요금 25% 할인
        cost_a_discounted = int(plan_cost * 0.75)
        cost_b_discounted = int(final_plan_after * 0.75)
        plan_total_cost = (cost_a_discounted * period_a) + (cost_b_discounted * period_b)

    # 추가 월 할인 차감
    plan_total_cost -= (add_discount * 24)

    # 할부원금 0원 미만 방지
    if carrier_principal < 0: carrier_principal = 0

    # B-2. 할부 이자 (연 5.9%)
    carrier_interest = 0
    if carrier_principal > 0:
        annual_rate = 0.059
        monthly_rate = annual_rate / 12
        months = 24
        monthly_payment = carrier_principal * (monthly_rate * math.pow(1 + monthly_rate, months)) / (math.pow(1 + monthly_rate, months) - 1)
        carrier_interest = int((monthly_payment * 24) - carrier_principal)
    
    # B-3. 부가서비스 총액
    addon_total_cost = addon_cost * addon_months
    
    # B-4. 통신사 최종 총 비용
    carrier_total = int(carrier_principal + carrier_interest + plan_total_cost + addon_total_cost)

    # --- [C] 승자 판정 및 분석 ---
    needed_additional_subsidy = 0
    target_monthly_plan = 0

    if self_total < carrier_total:
        winner = "self"
        diff_price = carrier_total - self_total
        recommend_text = "자급제 + 알뜰폰 승리!"
        
        # [분석] 얼마나 더 깎아야 하나?
        needed_additional_subsidy = diff_price
        
        # [분석] 요금제를 얼마로 낮춰야 하나?
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

    # --- [D] 템플릿 반환 ---
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
        "input_add_discount": add_discount,
        
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
        
        # 분석 데이터
        "needed_additional_subsidy": needed_additional_subsidy,
        "target_monthly_plan": target_monthly_plan
    })