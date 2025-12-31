import json
import time
import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === 1. 설정 ===
current_dir = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(current_dir, "phones.json")

# === 2. 타겟 데이터 (찾고자 하는 모델) ===
target_phones = {
    # 삼성 모델 (삼성닷컴 리스트에서 찾음)
    "s25_256": {"name": "갤럭시 S25", "market_price": 0, "store_price": 0},
    "s25_plus_256": {"name": "갤럭시 S25+", "market_price": 0, "store_price": 0},
    "s25_ultra_256": {"name": "갤럭시 S25 울트라", "market_price": 0, "store_price": 0},
    "zflip7_256": {"name": "갤럭시 Z 플립7", "market_price": 0, "store_price": 0},
    
    # 애플 모델 (프리스비에서 찾음)
    "iphone17_256": {"name": "아이폰 17 256GB", "market_price": 0, "store_price": 0},
    "iphone17_pro_256": {"name": "아이폰 17 프로 256GB", "market_price": 0, "store_price": 0},
}

def create_driver():
    """드라이버 설정"""
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new") # 화면 안 보려면 주석 해제
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_samsung_prices_from_list(driver):
    """
    삼성닷컴 '전체 스마트폰' 페이지를 한 번 훑어서
    현재 페이지에 있는 모든 폰의 {이름: 가격} 딕셔너리를 반환합니다.
    """
    url = "https://www.samsung.com/sec/smartphones/all-smartphones/"
    print(f"   🔎 [삼성닷컴] 전체 리스트 스캔 중 ({url})...")

    driver.get(url)
    price_map = {}

    try:
        # 1. 리스트 로딩 대기
        wait = WebDriverWait(driver, 10)
        # 제품 카드들이 로딩될 때까지 대기 (클래스명은 삼성닷컴 구조에 따라 유동적일 수 있어 포함 검색 사용)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='product-card']")))
        
        # 2. '더보기' 버튼이 있다면 클릭해서 목록을 더 불러오는 로직 (선택 사항)
        # 삼성닷컴은 스크롤 시 자동 로딩되거나 '더보기' 버튼이 있을 수 있음
        # 여기서는 간단히 스크롤을 좀 내려줍니다.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # 3. 모든 제품 카드 찾기
        cards = driver.find_elements(By.CSS_SELECTOR, "div[class*='product-card']")
        
        for card in cards:
            try:
                # 제품명 추출 (보통 h3 태그나 name 클래스)
                # 삼성닷컴 구조: .pd03-product-card__product-name-text 또는 .name
                try:
                    name_el = card.find_element(By.CSS_SELECTOR, "span[class*='name-text'], a[class*='name-text'], .name")
                    name = name_el.text.strip()
                except:
                    continue # 이름 없으면 패스

                # 가격 추출
                # 삼성닷컴 구조: .pd03-product-card__price-text 또는 .price-number
                try:
                    price_el = card.find_element(By.CSS_SELECTOR, "span[class*='price-text'], .price-number")
                    # "1,200,000원" -> 1200000 변환
                    price_text = price_el.text
                    # 혜택가/회원가 등이 같이 있을 경우 줄바꿈으로 나뉠 수 있음. 첫 번째 숫자만 가져옴.
                    price = int(re.sub(r"[^0-9]", "", price_text.split('\n')[0]))
                except:
                    continue # 가격 없으면(판매중지 등) 패스
                
                # 정제된 이름과 가격 저장
                # "갤럭시 S25 자급제" -> "갤럭시S25" (공백 제거, 자급제 제거)
                clean_name = name.replace(" ", "").replace("자급제", "").replace("5G", "").upper()
                
                # 이미 있으면(색상별 중복 등) 더 싼 가격으로 업데이트 (혜택가 기준)
                if clean_name in price_map:
                    price_map[clean_name] = min(price_map[clean_name], price)
                else:
                    price_map[clean_name] = price
                    
                # 디버깅용 출력 (너무 많으면 주석 처리)
                # print(f"      발견: {name} / {price:,}원")

            except Exception:
                continue
        
        print(f"      ✅ 총 {len(price_map)}개의 기기 정보를 수집했습니다.")
        return price_map

    except Exception as e:
        print(f"      ❌ 스캔 실패: {e}")
        return {}

def get_frisbee_price(driver, model_name):
    """(기존 유지) 프리스비 아이폰 검색"""
    keyword = model_name.replace("(", "").replace(")", "").replace("자급제", "").strip()
    url = f"https://www.frisbeekorea.com/goods/goods_search.php?keyword={keyword}"
    print(f"   🔎 [프리스비] '{keyword}' 검색...", end="", flush=True)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".goods_list")))
        items = driver.find_elements(By.CSS_SELECTOR, ".goods_list li")
        
        for item in items[:5]:
            try:
                name = item.find_element(By.CSS_SELECTOR, ".item_tit").text.strip()
                if any(x in name for x in ["케이스", "필름", "스트랩"]): continue
                
                price_el = item.find_element(By.CSS_SELECTOR, ".item_price")
                price = int(re.sub(r"[^0-9]", "", price_el.text))
                if price < 500000: continue

                print(f" -> ✅ {price:,}원")
                return price
            except: continue
        print(" -> ❌ 못 찾음")
        return 0
    except:
        print(" -> ❌ 에러")
        return 0

def main():
    driver = create_driver()
    
    # 1. 삼성폰 일괄 수집 (한 번만 접속)
    samsung_prices = get_samsung_prices_from_list(driver)
    
    print(f"=== 📱 매칭 및 업데이트 시작 ===")
    
    for key, info in target_phones.items():
        name = info["name"]
        
        # 브랜드 분기
        if "갤럭시" in name or "S2" in name or "Z" in name:
            # 수집해둔 삼성 가격표에서 찾기
            # 비교를 위해 타겟 이름도 정제 (갤럭시 S25 -> 갤럭시S25)
            target_clean = name.replace(" ", "").replace("자급제", "").replace("5G", "").upper()
            
            # 부분 일치 검색 (예: '갤럭시S25'를 찾는데 수집된 키에 '갤럭시S25256GB'가 있으면 매칭)
            matched_price = 0
            for scanned_name, price in samsung_prices.items():
                if target_clean in scanned_name:
                    matched_price = price
                    break
            
            if matched_price > 0:
                print(f"   ✅ [매칭성공] {name} -> {matched_price:,}원")
                market_price = matched_price
            else:
                print(f"   ⚠️ [미출시/못찾음] {name}")
                market_price = 0
                
        elif "아이폰" in name or "iphone" in name.lower():
            # 아이폰은 개별 검색 (프리스비)
            market_price = get_frisbee_price(driver, name)
            time.sleep(1)
        else:
            market_price = 0

        # 가격 저장 및 매장가 계산
        if market_price > 0:
            store_price = int(market_price * 1.15)
            store_price = (store_price // 100) * 100
        else:
            store_price = 0
            
        target_phones[key]["market_price"] = market_price
        target_phones[key]["store_price"] = store_price

    driver.quit()

    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(target_phones, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 저장 완료: {DB_FILE}")
    except Exception as e:
        print(f"\n❌ 저장 실패: {e}")

if __name__ == "__main__":
    main()