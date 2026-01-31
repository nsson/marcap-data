# marcap-data

주식 가격 자동 수집을 위한 리포지토리. [KRX Data Marketplace](https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd) 전종목 시세를 수집합니다.

## KRX 로그인 (필수)

KRX 사이트 개편 후 **로그인**이 있어야 데이터를 받을 수 있습니다. **Playwright** 브라우저 자동화를 사용합니다.

### 로컬 실행

1. Playwright Chromium 설치 (최초 1회):

```bash
pip install -r requirements.txt
playwright install chromium
```

2. 환경 변수로 KRX 계정을 넣어 실행합니다:

```bash
export KRX_USER_ID="your_id"
export KRX_PASSWORD="your_password"
python krx_collect.py
```

- **카카오/네이버 로그인** 사용 시: `KRX_LOGIN_MODE=manual` 설정 후 실행하면 브라우저가 열리며, 직접 로그인한 뒤 터미널에서 Enter를 누르면 됩니다.
- **브라우저 표시** (디버깅): `KRX_HEADLESS=0` 설정 시 headless가 꺼집니다.

### GitHub Actions 자동 실행

워크플로에 Playwright Chromium 설치 단계가 포함되어 있습니다 (별도 설정 불필요).

1. [KRX Data Marketplace](https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd)에서 회원가입/로그인 가능한 계정 준비
2. 저장소 **Settings → Secrets and variables → Actions** 에서 시크릿 추가:
   - `KRX_USER_ID`: KRX 로그인 ID
   - `KRX_PASSWORD`: KRX 로그인 비밀번호
3. 워크플로는 매일 00:00 UTC(한국 09:00)에 실행되며, 수동 실행도 가능합니다.

로그인 폼 필드명이 사이트와 다르면 환경변수로 지정할 수 있습니다(기본값: `userId`, `userPwd`).

- `KRX_LOGIN_USER_FIELD`: ID 입력 필드 name
- `KRX_LOGIN_PWD_FIELD`: 비밀번호 입력 필드 name

## 개발 환경 (Python 인터프리터)

Cursor/VS Code에서 "invalid" 인터프리터가 뜨는 경우, **프로젝트에 `.venv`가 없기 때문**입니다. Poetry는 기본적으로 가상환경을 전역 캐시에 만들기 때문에, 아래 순서대로 한 번만 실행하세요.

```bash
# 1) 기존 가상환경 제거(전역 캐시에 있던 것)
poetry env remove --all

# 2) 프로젝트 폴더에 .venv 생성 후 의존성 설치
poetry install
```

`poetry.toml`에 `in-project = true`가 있어서, 이제 `.venv`가 프로젝트 루트에 생깁니다.  
이후 Cursor에서 **Ctrl+Shift+P** → "Python: Select Interpreter" → `.\\.venv\\Scripts\\python.exe` 를 선택하면 됩니다.

## 대안: KRX OPEN API

로그인 대신 **API 인증키**를 쓰려면 [KRX OPEN API](https://openapi.krx.co.kr)에서 인증키를 신청한 뒤, 전종목 시세에 해당하는 API(유가증권/코스닥/코넥스 일별매매정보)를 사용할 수 있습니다. 인증키는 마이페이지에서 신청·승인 후 `AUTH_KEY` 헤더로 사용합니다.
