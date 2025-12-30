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
    transaction_type: str = Form(...), # sale, jeonse, monthly
    building_type: str = Form(...),    # house, officetel
    price_unit: int = Form(...)        # 만원 단위 입력값
):
    # 만원 단위 -> 원 단위 변환
    price = price_unit * 10000
    
    fee = 0
    max_fee = 0
    rate = 0.0

    # 1. 주택(House) 계산 로직
    if building_type == "house":
        if transaction_type == "sale":  # 매매
            if price < 50000000:
                rate = 0.6; max_fee = 250000
            elif price < 200000000:
                rate = 0.5; max_fee = 800000
            elif price < 900000000:
                rate = 0.4
            elif price < 1200000000:
                rate = 0.5
            elif price < 1500000000:
                rate = 0.6
            else:
                rate = 0.7
        else:  # 임대차 (전월세)
            if price < 50000000:
                rate = 0.5; max_fee = 200000
            elif price < 100000000:
                rate = 0.4; max_fee = 300000
            elif price < 600000000:
                rate = 0.3
            elif price < 1200000000:
                rate = 0.4
            elif price < 1500000000:
                rate = 0.5
            else:
                rate = 0.6

    # 2. 오피스텔(Officetel) 계산 로직 (주거용 기준 단순화)
    elif building_type == "officetel":
        if transaction_type == "sale":
            rate = 0.5 # 매매 0.5%
        else:
            rate = 0.4 # 임대차 0.4%

    # 수수료 계산
    calc_fee = int(price * (rate / 100))

    # 한도액 체크
    if max_fee > 0 and calc_fee > max_fee:
        final_fee = max_fee
    else:
        final_fee = calc_fee
        
    # 10원 단위 절사 (보통 중개보수는 원단위까지 나오지만 깔끔하게)
    final_fee = (final_fee // 10) * 10

    vat = int(final_fee * 0.1)
    total = final_fee + vat

    # 화면에 보여줄 텍스트 변환
    trans_kor = "매매" if transaction_type == "sale" else ("전세" if transaction_type == "jeonse" else "월세")
    build_kor = "주택" if building_type == "house" else "오피스텔"

    return templates.TemplateResponse("real_estate.html", {
        "request": request,
        "result": True,
        "price": price,
        "rate": rate,
        "fee": final_fee,
        "vat": vat,
        "total": total,
        "max_fee": max_fee,
        "trans_kor": trans_kor,
        "build_kor": build_kor
    })