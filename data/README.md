# KRX 데이터 디렉토리

이 디렉토리에는 GitHub Actions 워크플로우를 통해 자동으로 수집된 KRX 주식 가격 데이터가 저장됩니다.

## 파일 형식

파일명: `krx_data_YYYY-MM-DD.csv`

## 데이터 컬럼

pykrx 라이브러리를 통해 수집되는 데이터는 다음 정보를 포함합니다:
- 티커 (종목 코드)
- 시가 (Open)
- 고가 (High)
- 저가 (Low)
- 종가 (Close)
- 거래량 (Volume)
- 거래대금 (Trading Value)
- 시가총액 (Market Cap)
- 상장주식수 (Listed Shares)
- 등락률 등

## 수집 주기

매 평일 오후 9시(KST)에 자동으로 수집됩니다.
