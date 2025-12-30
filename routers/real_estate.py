from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/real-estate")
async def show_real_estate_page(request: Request):
    return templates.TemplateResponse("real_estate.html", {
        "request": request,
        "result": None
    })

@router.post("/real-estate/calc")
async def calculate_fee(
    request: Request, 
    transaction_type: str = Form(...),  # 'sale'(매매) or 'lease'(임대차)
    price: int = Form(...)
):
    fee = 0
    max_fee = 0 # 한도액 (0이면 한도 없음)
    rate = 0.0

    # --- 계산 로직 (주택 기준) ---
    if transaction_type == "sale":  # 매매/교환
        if price < 50000000:
            rate = 0.6
            max_fee = 250000
        elif price < 200000000:
            rate = 0.5
            max_fee = 800000
        elif price < 900000000:
            rate = 0.4
        elif price < 1200000000:
            rate = 0.5
        elif price < 1500000000:
            rate = 0.6
        else: # 15억 이상
            rate = 0.7
            
    else:  # 임대차 (전세/월세)
        if price < 50000000:
            rate = 0.5
            max_fee = 200000
        elif price < 100000000:
            rate = 0.4
            max_fee = 300000
        elif price < 600000000:
            rate = 0.3
        elif price < 1200000000:
            rate = 0.4
        elif price < 1500000000:
            rate = 0.5
        else: # 15억 이상
            rate = 0.6

    # 수수료 계산 (단위: %)
    calc_fee = int(price * (rate / 100))

    # 한도액 체크
    if max_fee > 0 and calc_fee > max_fee:
        final_fee = max_fee
    else:
        final_fee = calc_fee

    # 부가세 10% 별도
    vat = int(final_fee * 0.1)
    total = final_fee + vat

    return templates.TemplateResponse("real_estate.html", {
        "request": request,
        "transaction_type": "매매" if transaction_type == "sale" else "전/월세",
        "price": price,
        "rate": rate,
        "fee": final_fee,
        "vat": vat,
        "total": total,
        "result": True
    })