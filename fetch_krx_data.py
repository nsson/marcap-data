#!/usr/bin/env python3
"""
KRX 주식 가격 데이터 수집 스크립트
Fetch stock price data from Korea Exchange (KRX)
"""

import os
from datetime import datetime, timedelta
import pandas as pd
from pykrx import stock


def fetch_krx_data(date=None):
    """
    Fetch KRX market data for a specific date
    
    Args:
        date: Date in YYYY-MM-DD format. If None, uses previous business day
    
    Returns:
        DataFrame with market data
    """
    if date is None:
        # Get previous business day (exclude weekends)
        today = datetime.now()
        days_back = 1
        if today.weekday() == 0:  # Monday
            days_back = 3
        elif today.weekday() == 6:  # Sunday
            days_back = 2
        date = (today - timedelta(days=days_back)).strftime('%Y%m%d')
    else:
        # Convert YYYY-MM-DD to YYYYMMDD format
        date = date.replace('-', '')
    
    print(f"Fetching KRX data for {date}...")
    
    try:
        # Get market cap data for all stocks (includes OHLCV)
        df = stock.get_market_cap_by_ticker(date, market="ALL")
        
        if df is None or df.empty:
            print(f"No data available for {date}")
            return None
        
        # Reset index to make ticker a column
        df = df.reset_index()
        df['Date'] = date
        
        print(f"Successfully fetched {len(df)} records")
        return df
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def save_data(df, output_dir='data'):
    """
    Save dataframe to CSV file
    
    Args:
        df: DataFrame to save
        output_dir: Directory to save the file
    """
    if df is None or df.empty:
        print("No data to save")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get date from the data
    if 'Date' in df.columns:
        date_str = df['Date'].iloc[0]
        # Convert YYYYMMDD to YYYY-MM-DD
        if len(date_str) == 8:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Save to CSV
    filename = f"{output_dir}/krx_data_{date_str}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Data saved to {filename}")
    
    return filename


def main():
    """Main function"""
    print("=== KRX Stock Price Data Collection ===")
    
    # Fetch data
    df = fetch_krx_data()
    
    # Save data
    if df is not None:
        save_data(df)
        print("Data collection completed successfully!")
    else:
        print("Data collection failed!")
        exit(1)


if __name__ == '__main__':
    main()
