"""
KRX 시가총액 수집 - Selenium Chrome WebDriver 버전 (수동 로그인 검증용)

Chrome을 직접 열어 수동으로 로그인한 뒤 데이터를 수집합니다.
로그인/API 동작 검증용 독립 스크립트입니다.

필요 패키지:
    pip install selenium webdriver-manager pandas pyarrow requests
"""
import sys
from datetime import datetime, timedelta
import os

# 의존성 체크
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("필요 패키지: pip install selenium webdriver-manager pandas pyarrow requests")
    sys.exit(1)

import requests
import pandas as pd

BASE_URL = "https://data.krx.co.kr"
DATA_URL = f"{BASE_URL}/comm/bldAttendant/getJsonData.cmd"
MENU_URL = f"{BASE_URL}/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101"

today = datetime.now()
prev_day = today - timedelta(days=1)
day_str = prev_day.strftime("%Y%m%d")
year_str = prev_day.strftime("%Y")
save_dir = "data"
os.makedirs(save_dir, exist_ok=True)
filename = os.path.join(save_dir, f"marcap-{year_str}.parquet")

payload = {
    "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
    "locale": "ko_KR",
    "mktId": "ALL",
    "trdDd": day_str,
    "share": "1",
    "money": "1",
    "csvxls_isNo": "false",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{BASE_URL}/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101",
    "Origin": BASE_URL,
}


def main():
    print("=" * 60)
    print("KRX 시가총액 수집 (Selenium Chrome - 수동 로그인)")
    print("=" * 60)
    print("\n1. Chrome 브라우저가 곧 열립니다.")
    print("2. 로그인 페이지가 나오면 직접 로그인해 주세요.")
    print("3. 시가총액 데이터가 보이는 페이지까지 이동해 주세요.")
    print("4. 준비가 되면 터미널에서 Enter를 누르세요.\n")

    # ChromeDriver 자동 다운로드 및 옵션 (headless=False → 창 표시)
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # 시가총액 메뉴로 이동 (로그인 필요 시 리다이렉트됨)
        print("시가총액 메뉴 페이지로 이동 중...")
        driver.get(MENU_URL)

        # 사용자가 수동으로 로그인 후 Enter 입력 대기
        input("\n>>> 로그인 완료 후, 데이터가 보이는 화면에서 Enter를 누르세요: ")

        # 메뉴 페이지 재방문 (세션 확립)
        print("\n세션 확인을 위해 페이지 재방문 중...")
        driver.get(MENU_URL)
        input(">>> 한 번 더 Enter를 누르면 데이터 수집을 시작합니다: ")

        # Selenium 쿠키 → requests용 형식으로 변환
        cookies = driver.get_cookies()
        session = requests.Session()
        for c in cookies:
            session.cookies.set(
                c["name"],
                c["value"],
                domain=c.get("domain", ""),
                path=c.get("path", "/"),
            )
        session.headers.update(headers)

        # getJsonData API 호출
        print("\ngetJsonData API 호출 중...")
        response = session.post(DATA_URL, data=payload, headers=headers, timeout=60)

        print(f"  HTTP 상태: {response.status_code}")
        print(f"  응답 본문 (처음 200자): {response.text[:200]}")

        if response.status_code != 200:
            print(f"\n[오류] HTTP {response.status_code}")
            return 1

        try:
            data = response.json()
        except Exception:
            print(f"\n[오류] JSON 파싱 실패. 응답: {response.text[:500]}")
            return 1

        if "OutBlock_1" not in data or not data["OutBlock_1"]:
            print(f"\n[오류] OutBlock_1 없음 (로그인 필요 또는 데이터 없음)")
            print(f"  응답: {str(data)[:300]}")
            return 1

        stock_data = data["OutBlock_1"]
        st = pd.DataFrame(stock_data)

        # 컬럼 매핑 (krx_collect.py와 동일)
        st.rename(
            columns={
                "ISU_SRT_CD": "Code",
                "ISU_ABBRV": "Name",
                "MKT_NM": "Market",
                "SECT_TP_NM": "Dept",
                "TDD_CLSPRC": "Close",
                "FLUC_TP_CD": "ChangeCode",
                "CMPPREVDD_PRC": "Changes",
                "FLUC_RT": "ChagesRatio",
                "TDD_OPNPRC": "Open",
                "TDD_HGPRC": "High",
                "TDD_LWPRC": "Low",
                "ACC_TRDVOL": "Volume",
                "ACC_TRDVAL": "Amount",
                "MKTCAP": "Marcap",
                "LIST_SHRS": "Stocks",
                "MKT_ID": "MarketId",
            },
            inplace=True,
        )

        if st["Close"][0] == "-" and st["Close"][1] == "-":
            print("\n[오류] 거래일 아님")
            return 1

        if "ISU_CD" in st.columns:
            del st["ISU_CD"]

        num_list = ["Close", "Open", "High", "Low", "Volume", "Amount", "Marcap", "Stocks"]
        for j in num_list:
            st[j] = st[j].apply(lambda x: int(str(x).replace(",", "")))
        st["Date"] = pd.to_datetime(day_str)
        st["Rank"] = st["Marcap"].rank(ascending=False)

        if os.path.exists(filename):
            old_df = pd.read_parquet(filename)
            new_df = pd.concat([old_df, st], ignore_index=True)
        else:
            new_df = st

        new_df["ChangeCode"] = new_df["ChangeCode"].astype("str")
        new_df["Changes"] = new_df["Changes"].astype("str")
        new_df["ChagesRatio"] = new_df["ChagesRatio"].astype("str")

        new_df.to_parquet(filename, index=False)
        print(f"\n[완료] {filename} 저장됨 (행 수: {len(new_df)})")
        return 0

    finally:
        input("\n>>> Enter를 누르면 브라우저가 종료됩니다: ")
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())
