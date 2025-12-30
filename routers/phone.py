import json
import os
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ==========================================================
# [경로 설정]
# ==========================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(root_dir, "phones.json")

def load_phone_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

@router.get("/phone")
async def show_phone_page(request: Request):
    phones = load_phone_db()
    # 첫 로딩 시에는 계산 결과 없이 화면만 렌더링
    return templates.TemplateResponse("phone.html", {
        "request": request,
        "phones": phones,
        "result": None
    })

@router.post("/phone/calc")
async def calculate_phone(
    request: Request,
    phone_code: str = Form(...),
    mvno_cost: int = Form(default=0),     # 자급제: 알뜰폰 요금
    plan_cost: int = Form(default=0),     # 통신사: 요금제
    carrier_type: str = Form(...),        # gongsi(공시) 또는 seonyak(선약)
    subsidy: int = Form(default=0),       # 공시지원금
    add_discount: int = Form(default=0)   # 통신사 추가 할인 (가족결합 등)
):
    phones = load_phone_db()
    phone_info = phones.get(phone_code)

    if not phone_info:
        return templates.TemplateResponse("phone.html", {"request": request, "phones": phones, "result": None})

    market_price = phone_info['market_price'] # 자급제 가격
    store_price = phone_info['store_price']   # 출고가 (정가)

    # ----------------------------------------------------
    # 1. [왼쪽] 자급제 + 알뜰폰 계산
    # ----------------------------------------------------
    # 총 비용 = 기기값 + (월요금 * 24)
    self_total = market_price + (mvno_cost * 24)


    # ----------------------------------------------------
    # 2. [오른쪽] 통신사 계산 (선택한 방식에 따라 분기)
    # ----------------------------------------------------
    carrier_principal = 0   # 할부원금
    carrier_interest = 0    # 할부이자
    discount_total = 0      # 총 요금 할인액 (선약 + 추가할인)
    carrier_method_text = ""

    # (A) 공통: 추가 할인 (가족결합 등) - 24개월치
    additional_discount_total = add_discount * 24

    if carrier_type == "gongsi":
        # === 공시지원금 방식 ===
        carrier_method_text = "공시지원금"
        
        # 할부원금 = 출고가 - 공시지원금
        carrier_principal = store_price - subsidy
        if carrier_principal < 0: carrier_principal = 0
        
        # 할인 총액 = 추가할인만 해당 (공시는 기기값에서 깠으므로)
        discount_total = additional_discount_total

    else:
        # === 선택약정 방식 ===
        carrier_method_text = "선택약정"
        
        # 할부원금 = 출고가 그대로
        carrier_principal = store_price
        
        # 할인 총액 = (요금제 25% * 24) + 추가할인
        seonyak_discount = int(plan_cost * 0.25 * 24)
        discount_total = seonyak_discount + additional_discount_total

    # 할부이자 계산 (연 5.9%, 원리금균등상환 근사치: 원금 * 5.9% * 2년 / 2) -> 약 6.18%
    carrier_interest = int(carrier_principal * 0.0618)

    # 통신사 총 비용 = (할부원금 + 이자) + (월요금 * 24) - (총 요금 할인)
    carrier_total = (carrier_principal + carrier_interest) + (plan_cost * 24) - discount_total


    # ----------------------------------------------------
    # 3. 결과 비교
    # ----------------------------------------------------
    winner = "self" if self_total < carrier_total else "carrier"
    diff_price = abs(self_total - carrier_total)
    recommend_text = "자급제 + 알뜰폰 승!" if winner == "self" else f"통신사 {carrier_method_text} 승!"

    return templates.TemplateResponse("phone.html", {
        "request": request,
        "phones": phones,
        "selected_code": phone_code,
        "result": True,
        
        # 입력값 유지
        "input_mvno": mvno_cost,
        "input_plan": plan_cost,
        "carrier_type": carrier_type,
        "input_subsidy": subsidy,
        "input_add_discount": add_discount,

        # 결과 데이터
        "market_price": market_price,
        "store_price": store_price,
        
        "self_total": self_total,
        
        "carrier_total": carrier_total,
        "carrier_principal": carrier_principal,
        "carrier_interest": carrier_interest,
        "discount_total": discount_total,
        "carrier_method_text": carrier_method_text,
        
        "winner": winner,
        "recommend_text": recommend_text,
        "diff_price": diff_price
    })