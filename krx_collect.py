"""
KRX Data Marketplace 전종목 시세 수집 (로그인 대응).
- 로그인: Playwright 브라우저 자동화 사용 (KRX SSO 대응)
- 환경변수 KRX_USER_ID, KRX_PASSWORD 설정 시 세션 로그인 후 API 호출
- GitHub Actions: Secrets에 KRX_USER_ID, KRX_PASSWORD 등록, playwright install chromium 필요
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import os

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


def _get_cookies_via_playwright() -> list[dict]:
    """Playwright로 KRX 로그인 후 쿠키 추출. (카카오/네이버 로그인 시 KRX_LOGIN_MODE=manual)"""
    from playwright.sync_api import sync_playwright

    user_field = os.environ.get("KRX_LOGIN_USER_FIELD", "userId")
    pwd_field = os.environ.get("KRX_LOGIN_PWD_FIELD", "userPwd")
    user_id = os.environ["KRX_USER_ID"]
    password = os.environ["KRX_PASSWORD"]
    headless = os.environ.get("KRX_HEADLESS", "1") == "1"
    manual_login = os.environ.get("KRX_LOGIN_MODE", "").lower() == "manual"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent=headers["User-Agent"],
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()

        try:
            # 1. 시가총액 메뉴 페이지 접근 (로그인 필요 시 리다이렉트됨)
            page.goto(MENU_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)

            # 2. 로그인
            if manual_login:
                # 카카오/네이버 등: 브라우저에서 직접 로그인 후 아무 키 입력
                input("브라우저에서 로그인 완료 후 Enter를 누르세요...")
            else:
                # userId/userPwd 폼 로그인
                user_input = page.locator(
                    f'input[name="{user_field}"], input#userId, input[id*="userId"]'
                ).first
                if user_input.is_visible(timeout=3000):
                    user_input.fill(user_id)
                    pwd_input = page.locator(
                        f'input[name="{pwd_field}"], input#userPwd, input[type="password"]'
                    ).first
                    pwd_input.fill(password)
                    page.locator(
                        'button[type="submit"], input[type="submit"], .btn-login, [class*="login"]'
                    ).first.click()
                    page.wait_for_load_state("networkidle", timeout=30000)
                    page.wait_for_timeout(3000)

            # 3. 메뉴 페이지 재방문 (세션 확립)
            page.goto(MENU_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            cookies = context.cookies()
        finally:
            browser.close()

    return cookies


def login_and_fetch(_session: requests.Session) -> requests.Response:
    """Playwright로 로그인 후 쿠키를 requests Session에 주입해 getJsonData 호출."""
    cookies = _get_cookies_via_playwright()

    session = requests.Session()
    for c in cookies:
        session.cookies.set(
            c["name"],
            c["value"],
            domain=c.get("domain", ""),
            path=c.get("path", "/"),
        )

    session.headers.update(headers)
    return session.post(DATA_URL, data=payload, headers=headers, timeout=60)


def fetch_without_login() -> requests.Response:
    """로그인 없이 API 호출 (과거 방식, 로그인 필수 정책 이후 실패할 수 있음)."""
    return requests.post(DATA_URL, data=payload, headers=headers, timeout=60)


def is_login_required(response: requests.Response) -> bool:
    """응답이 로그인 필요(또는 실패) 상태인지 판단."""
    if response.status_code != 200:
        return True
    ct = response.headers.get("Content-Type", "")
    if "application/json" not in ct:
        return True
    try:
        data = response.json()
        if "OutBlock_1" not in data or not data["OutBlock_1"]:
            return True
        return False
    except Exception:
        return True


# 로그인 정보가 있으면 세션 로그인 후 요청, 없으면 기존 방식
if os.environ.get("KRX_USER_ID") and os.environ.get("KRX_PASSWORD"):
    session = requests.Session()
    response = login_and_fetch(session)
else:
    response = fetch_without_login()

if is_login_required(response):
    if not (os.environ.get("KRX_USER_ID") and os.environ.get("KRX_PASSWORD")):
        print(
            "KRX 데이터댐이 로그인을 요구합니다. 환경변수 KRX_USER_ID, KRX_PASSWORD를 설정하거나 "
            "GitHub Actions Secrets에 등록하세요."
        )
    else:
        print("로그인 실패 또는 세션 만료. ID/비밀번호와 로그인 폼 필드명을 확인하세요.")
    if response.status_code == 400:
        print(f"[디버그] 400 응답 본문: {response.text[:500]}")
    raise SystemExit(1)

stock_data = response.json()["OutBlock_1"]
st = pd.DataFrame(stock_data)

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
    exit()

if "ISU_CD" in st.columns:
    del st["ISU_CD"]

num_list = ["Close", "Open", "High", "Low", "Volume", "Amount", "Marcap", "Stocks"]
for j in num_list:
    st[j] = st[j].apply(lambda x: int(x.replace(",", "")))
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
