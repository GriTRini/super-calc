import json
import os
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(root_dir, "phones.json")

def load_phone_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

# [중요] 접속하자마자 계산기 보여줌 (메인 페이지)
@router.get("/")
async def show_home(request: Request):
    phones = load_phone_db()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "phones": phones,
        "result": None
    })

# 계산 요청 처리
@router.post("/calc")
async def calculate(
    request: Request,
    phone_code: str = Form(...),
    mvno_cost: int = Form(default=0),
    plan_cost: int = Form(default=0),
    carrier_type: str = Form(...),
    subsidy: int = Form(default=0),
    add_discount: int = Form(default=0)
):
    phones = load_phone_db()
    phone_info = phones.get(phone_code)

    if not phone_info:
        return templates.TemplateResponse("index.html", {"request": request, "phones": phones, "result": None})

    market_price = phone_info['market_price']
    store_price = phone_info['store_price']

    # 1. 자급제 계산
    self_total = market_price + (mvno_cost * 24)

    # 2. 통신사 계산
    additional_discount_total = add_discount * 24
    if carrier_type == "gongsi":
        carrier_method_text = "공시지원금"
        carrier_principal = max(0, store_price - subsidy)
        discount_total = additional_discount_total
    else:
        carrier_method_text = "선택약정"
        carrier_principal = store_price
        seonyak_discount = int(plan_cost * 0.25 * 24)
        discount_total = seonyak_discount + additional_discount_total

    carrier_interest = int(carrier_principal * 0.0618)
    carrier_total = (carrier_principal + carrier_interest) + (plan_cost * 24) - discount_total

    # 3. 결과 판정
    winner = "self" if self_total < carrier_total else "carrier"
    diff_price = abs(self_total - carrier_total)
    recommend_text = "자급제 + 알뜰폰 승!" if winner == "self" else f"통신사 {carrier_method_text} 승!"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "phones": phones,
        "selected_code": phone_code,
        "result": True,
        "input_mvno": mvno_cost, "input_plan": plan_cost,
        "carrier_type": carrier_type, "input_subsidy": subsidy, "input_add_discount": add_discount,
        "market_price": market_price, "store_price": store_price,
        "self_total": self_total, "carrier_total": carrier_total,
        "carrier_principal": carrier_principal, "carrier_interest": carrier_interest,
        "discount_total": discount_total, "carrier_method_text": carrier_method_text,
        "winner": winner, "recommend_text": recommend_text, "diff_price": diff_price
    })