# marcap-data
주식 가격 자동 수집을 위한 리포지토리

## 개요
이 리포지토리는 KRX(한국거래소)의 주식 가격 데이터를 자동으로 수집하여 저장합니다.

## 기능
- 매일 자동으로 KRX 주식 시장 데이터 수집
- CSV 형식으로 데이터 저장
- GitHub Actions를 통한 자동화

## 사용 방법

### 로컬에서 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 데이터 수집 실행
python fetch_krx_data.py
```

### 자동 수집
- GitHub Actions 워크플로우가 매 평일 오후 9시(KST)에 자동으로 실행됩니다
- 수집된 데이터는 `data/` 디렉토리에 저장됩니다
- 수동으로 워크플로우를 실행할 수도 있습니다 (Actions 탭에서 "Run workflow" 클릭)

## 데이터 형식
수집된 데이터는 `data/krx_data_YYYY-MM-DD.csv` 형식으로 저장됩니다.

## 라이선스
MIT
