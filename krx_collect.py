import requests
import pandas as pd
from datetime import datetime, timedelta
import os

today = datetime.now()
prev_day = today - timedelta(days=1)
day_str = prev_day.strftime('%Y%m%d')
year_str = prev_day.strftime('%Y')
save_dir = 'data'
os.makedirs(save_dir, exist_ok=True)

filename = os.path.join(save_dir, f"marcap-{year_str}.parquet")

url = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
data = {
    'bld': 'dbms/MDC/STAT/standard/MDCSTAT01501',
    'locale': 'ko_KR',
    'mktId' : 'ALL',
    'trdDd' : day_str,
    'share' : '1',
    'money' : '1',
    'csvxls_isNo': 'false'
}

header = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101"
}

response = requests.post(url, data=data, headers = header)

stock_data = response.json()['OutBlock_1']
st = pd.DataFrame(stock_data)

st.rename(
    columns={'ISU_SRT_CD': 'Code', 'ISU_ABBRV': 'Name', 'MKT_NM': 'Market', 'SECT_TP_NM': 'Dept',
             'TDD_CLSPRC':'Close', 'FLUC_TP_CD':'ChangeCode', 'CMPPREVDD_PRC':'Changes', 'FLUC_RT':'ChagesRatio' ,
             'TDD_OPNPRC':'Open', 'TDD_HGPRC':'High','TDD_LWPRC':'Low','ACC_TRDVOL':'Volume','ACC_TRDVAL':'Amount',
             'MKTCAP':'Marcap','LIST_SHRS':'Stocks', 'MKT_ID':'MarketId'},
    inplace=True)  # 거래대금 기준

if st['Close'][0] == '-' and st['Close'][1] == '-':
    exit()

if 'ISU_CD' in st.columns:
    del(st['ISU_CD'])

num_list = ['Close','Open','High','Low','Volume','Amount','Marcap','Stocks']
for j in num_list:
    st[j] = st[j].apply(lambda x: int(x.replace(',','')))
st['Date'] = pd.to_datetime(day_str)
st['Rank'] = st['Marcap'].rank(ascending=False)

if os.path.exists(filename):
    old_df = pd.read_parquet(filename)
    new_df = pd.concat([old_df, st], ignore_index=True)
else:
    new_df = st

new_df['ChangeCode']=new_df['ChangeCode'].astype('str')
new_df['Changes']=new_df['Changes'].astype('str')
new_df['ChagesRatio']=new_df['ChagesRatio'].astype('str')

new_df.to_parquet(filename, index=False)
