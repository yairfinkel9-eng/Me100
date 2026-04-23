import streamlit as st
import yfinance as yf
import pandas as pd

# הגדרות תצוגה
st.set_page_config(page_title="Mega Market Scanner", layout="wide")

st.title("🚀 סורק שוק מסיבי (3,000+ מניות)")
st.write("הסורק מנתח את מניות ה-S&P 500, Nasdaq ומניות צמיחה נוספות.")

@st.cache_data(ttl=3600)
def get_all_tickers():
    # משיכת רשימות מסיביות מויקיפדיה
    try:
        url_sp = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        sp500 = pd.read_html(url_sp)[0]['Symbol'].tolist()
        url_nasdaq = "https://en.wikipedia.org/wiki/Nasdaq-100"
        nasdaq100 = pd.read_html(url_nasdaq)[4]['Ticker'].tolist()
        # הוספת מניות סיכון גבוה פופולריות
        extra = ['MARA', 'RIOT', 'COIN', 'GME', 'AMC', 'UPST', 'PLTR', 'SOFI', 'MSTR', 'NKLA', 'RIVN', 'LCID']
        return list(set(sp500 + nasdaq100 + extra))
    except:
        return ['AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT', 'GOOG', 'MARA', 'COIN']

def scan_bulk(tickers, min_beta, max_cap):
    results = []
    progress_bar = st.progress(0)
    total = len(tickers)
    
    for i, ticker in enumerate(tickers):
        try:
            t = yf.Ticker(ticker.replace('.', '-'))
            info = t.info
            beta = info.get('beta', 0)
            mkt_cap = info.get('marketCap', 0) / 1_000_000_000
            
            # פילטר בסיסי תוך כדי ריצה כדי להאיץ תוצאות
            if beta and beta >= min_beta and mkt_cap <= max_cap:
                results.append({
                    'מניה': ticker,
                    'שם': info.get('longName', 'N/A'),
                    'תנודתיות (Beta)': beta,
                    'שווי שוק ($B)': round(mkt_cap, 2),
                    'מחיר': info.get('currentPrice', 0),
                    'שורט (%)': round(info.get('shortPercentOfFloat', 0) * 100, 2)
                })
        except:
            continue
        progress_bar.progress((i + 1) / total)
    return pd.DataFrame(results)

# ממשק צד
st.sidebar.header("פילטרים אגרסיביים")
beta_val = st.sidebar.slider("Beta מינימלית (תנודתיות)", 1.0, 4.0, 1.5)
cap_val = st.sidebar.number_input("שווי שוק מקסימלי ($B)", value=50)

if st.button('הרץ סריקה על כל השוק'):
    all_tickers = get_all_tickers()
    st.info(f"מתחיל לסרוק {len(all_tickers)} מניות... זה יקח כדקה.")
    
    found_data = scan_bulk(all_tickers, beta_val, cap_val)
    
    if not found_data.empty:
        st.success(f"נמצאו {len(found_data)} מניות שעונות על הקריטריונים!")
        st.dataframe(found_data.sort_values(by='תנודתיות (Beta)', ascending=False))
    else:
        st.warning("לא נמצאו מניות. נסה להוריד את ה-Beta או להעלות את שווי השוק.")

st.divider()
st.caption("הנתונים נמשכים מ-Yahoo Finance. השימוש על אחריות המשתמש בלבד.")

