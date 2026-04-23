import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Ultimate Stock Screener", layout="wide")

st.title("🛠️ סורק מניות מתקדם - פילטרים מלאים")

# רשימת המניות לסריקה
mega_list = [
    'TSLA', 'NVDA', 'AMD', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'PLTR', 
    'MARA', 'COIN', 'MSTR', 'UPST', 'SOFI', 'GME', 'AMC', 'AI', 'RIVN', 'LCID', 
    'SMCI', 'ARM', 'MU', 'INTC', 'TSM', 'SQ', 'PYPL', 'HOOD', 'SHOP', 'SNOW',
    'DKNG', 'U', 'PATH', 'IONQ', 'QS', 'PLUG', 'NVAX', 'MRNA', 'ABNB', 'DASH'
]

def scan_pro(tickers, filters):
    results = []
    prog = st.progress(0)
    for i, ticker in enumerate(tickers):
        try:
            t = yf.Ticker(ticker)
            info = t.info
            
            # שליפת נתונים
            beta = info.get('beta', 0)
            pe = info.get('trailingPE', None)
            vol = info.get('averageVolume', 0)
            mkt_cap = info.get('marketCap', 0) / 1_000_000_000
            price = info.get('currentPrice', 0)
            
            # לוגיקת פילטרים
            if beta < filters['min_beta']: continue
            if mkt_cap > filters['max_cap']: continue
            if vol < filters['min_vol']: continue
            if filters['max_pe'] and (pe is None or pe > filters['max_pe']): continue
            
            results.append({
                'מניה': ticker,
                'מחיר': price,
                'Beta': beta,
                'מכפיל רווח (P/E)': pe if pe else "N/A",
                'מחזור יומי ממוצע': f"{vol:,}",
                'שווי שוק ($B)': round(mkt_cap, 2)
            })
        except:
            continue
        prog.progress((i + 1) / len(tickers))
    return pd.DataFrame(results)

# --- תפריט פילטרים בצד ---
st.sidebar.header("⚙️ הגדרות סריקה")

f_beta = st.sidebar.slider("Beta מינימלית", 0.0, 4.0, 1.2)
f_cap = st.sidebar.number_input("שווי שוק מקסימלי ($B)", value=500)
f_vol = st.sidebar.number_input("מחזור מסחר מינימלי (מניות)", value=1000000)
f_pe = st.sidebar.number_input("מכפיל רווח מקסימלי (0 = התעלם)", value=0)

filters = {
    'min_beta': f_beta,
    'max_cap': f_cap,
    'min_vol': f_vol,
    'max_pe': f_pe if f_pe > 0 else None
}

if st.button('🚀 הרץ סריקה מתקדמת'):
    st.info(f"סורק לפי פילטרים מותאמים אישית...")
    data = scan_pro(mega_list, filters)
    
    if not data.empty:
        st.success(f"נמצאו {len(data)} מניות!")
        st.dataframe(data)
    else:
        st.warning("לא נמצאו מניות שעונות על כל הפילטרים. נסה להקל בתנאים.")


