from tvDatafeed import TvDatafeed, Interval
import requests
import time
import datetime

STOCK_PRICE_API_URL = "https://cse-maverick-be-platform.onrender.com/api/ohlcv/{company_symbol}"

tv = TvDatafeed()

def fetch_ohlcv(intval: str,company_symbol: str, bars: int = 400, max_retries: int = 10):
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[fetch_ohlcv] Starting attempt {attempt}/{max_retries} for {company_symbol}")
            
            data = tv.get_hist(
                symbol=company_symbol,
                exchange="CSELK",
                interval=intval ,
                n_bars=bars
            )
            
            print(f"[fetch_ohlcv] Attempt {attempt}: Received data: {data is not None}, Empty: {data.empty if data is not None else 'N/A'}")
            
            if data is None:
                raise ValueError("Received None data from TV")
            
            if data.empty:
                raise ValueError("Received empty OHLCV data from TV")
            
            print(f"[fetch_ohlcv] Attempt {attempt}: Success! Returning {len(data)} rows")
            return data.sort_index()
            
        except Exception as e:
            last_exception = e
            print(f"[fetch_ohlcv] Attempt {attempt}/{max_retries} failed: {type(e).__name__}: {e}")
            
            if attempt < max_retries:
                print(f"[fetch_ohlcv] Waiting 2 seconds before retry...")
                time.sleep(2)
            else:
                print(f"[fetch_ohlcv] All {max_retries} attempts exhausted")
    
    # If we reach here, all retries failed
    print(f"[fetch_ohlcv] Raising final exception after {max_retries} failed attempts")
    raise RuntimeError(
        f"Failed to fetch OHLCV data for {company_symbol} after {max_retries} retries"
    ) from last_exception


def fetch_latest_price(company_symbol: str) -> float:
    url = STOCK_PRICE_API_URL.format(company_symbol=company_symbol)
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        try:
            payload = response.json()
        except requests.exceptions.JSONDecodeError:
            raise ValueError(f"Invalid JSON response for symbol {company_symbol}")
        
        ohlcv_list = payload.get("ohlcv")
        if not ohlcv_list or not isinstance(ohlcv_list, list):
            raise ValueError(f"No valid OHLCV data returned for symbol {company_symbol}")
        
        # Filter out items without required fields
        valid_ohlcv = []
        for item in ohlcv_list:
            if isinstance(item, dict) and "date" in item and "close" in item:
                try:
                    # Validate date format
                    datetime.datetime.strptime(item["date"], "%Y-%m-%d")
                    # Validate close price
                    float(item["close"])
                    valid_ohlcv.append(item)
                except (ValueError, TypeError):
                    continue  # Skip invalid entries
        
        if not valid_ohlcv:
            raise ValueError(f"No valid price data found for symbol {company_symbol}")
        
        # Sort by date
        valid_ohlcv.sort(key=lambda x: datetime.datetime.strptime(x["date"], "%Y-%m-%d"))
        
        latest_close = float(valid_ohlcv[-1]["close"])
        print(f"Latest price for {company_symbol}: {latest_close}")
        
        return latest_close
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch price data for {company_symbol}: {str(e)}")