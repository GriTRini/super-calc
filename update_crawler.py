import json
import time
import os
import re

# 셀레니움 라이브러리
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

current_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(current_dir, "phones.json")

def get_real_price(driver, keyword):
    """
    [개선됨] 리스트를 순회하며 진짜 가격을 찾을 때까지 검사
    """
    print(f"🔍 검색 중: '{keyword}' ... ", end="")
    
    try:
        # 1. 다나와 검색 URL 이동
        url = f"https://search.danawa.com/dsearch.php?query={keyword}"
        driver.get(url)
        
        # [변경] 로딩 대기 시간 3초로 늘림 (인터넷 느릴 때 대비)
        time.sleep(3) 
        
        # 2. 상품 리스트 전체 가져오기 (광고 포함 모든 리스트)
        # .prod_item 클래스를 가진 모든 요소를 찾음
        items = driver.find_elements(By.CSS_SELECTOR, ".prod_list .prod_item")
        
        for item in items:
            try:
                # 해당 상품 박스 안에서 '가격' 요소 찾기
                # 보통 .price_sect > a > strong 구조임
                price_element = item.find_element(By.CSS_SELECTOR, ".price_sect strong")
                price_text = price_element.text
                
                # 숫자만 추출 (예: "1,250,000원" -> 1250000)
                price = int(re.sub(r"[^0-9]", "", price_text))
                
                # [중요] 필터링 로직
                # 1. 가격이 10만원 미만이면 (케이스, 필름 등) -> 무시하고 다음 상품으로
                if price < 100000:
                    continue
                
                # 2. 여기까지 왔으면 유효한 가격임 -> 리턴
                print(f"✅ 찾음: {price:,}원")
                return price
                
            except Exception:
                # 이 상품 박스에는 가격표가 없거나 구조가 다름 -> 다음 상품으로 넘어감
                continue
        
        # 리스트를 끝까지 다 뒤졌는데도 적당한 가격을 못 찾음
        print(f"❌ 실패 (유효한 상품 없음)")
        return 0

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return 0

def main():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # [추가] 봇 탐지 회피를 위한 User-Agent 설정
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # 드라이버 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # === [기종 목록은 그대로 유지] ===
    target_phones = {
        # ... (아까 작성하신 목록 그대로 두시면 됩니다) ...
        # 테스트용으로 몇 개만 예시로 남겨둡니다. 덮어쓸 땐 전체 목록 넣으세요.
        "iphone17_256": "아이폰 17 자급제 256GB",
        "s25_ultra_256": "갤럭시 S25 울트라 자급제 256GB",
        "zflip7_256": "갤럭시 Z플립7 자급제 256GB",
    }
    
    new_data = {}

    print(f"=== 📱 가격 정밀 크롤링 시작 ===")
    
    for code, search_keyword in target_phones.items():
        market_price = get_real_price(driver, search_keyword)
        
        if market_price > 0:
            store_price = int(market_price * 1.15) 
            store_price = (store_price // 100) * 100 
        else:
            store_price = 0
            # 실패 시 로그만 남기고 계속 진행
            print(f"   ↳ ⚠️ '{search_keyword}' 가격을 못 찾았습니다.")

        clean_name = search_keyword.replace(" 자급제", "")

        new_data[code] = {
            "name": clean_name,
            "market_price": market_price,
            "store_price": store_price
        }

    driver.quit()

    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 업데이트 완료! '{DB_FILE}' 저장됨.")
    except Exception as e:
        print(f"\n❌ 저장 실패: {e}")

if __name__ == "__main__":
    main()