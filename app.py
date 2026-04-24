import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# הגדרות עמוד ועיצוב CSS
st.set_page_config(page_title="Money Maker & Portfolio", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; }
    .main-title {
        text-align: center; color: #2ecc71; font-size: 3rem;
        font-weight: bold; text-shadow: 2px 2px #000000; margin-bottom: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="main-title">💰 סורק המיליונרים והתיק האישי 💰</h1>', unsafe_allow_html=True)

# --- הגדרות Google Sheets ---
# החלף את הקישור למטה בקישור לגיליון שלך (שיתוף ל-Editor - Anyone with the link)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1La-WwH7CE5UVV3dtSFTfhI1_FPQ3c8F99Y4ivsPsxkU/edit?usp=drivesdk"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    portfolio_df = conn.read(spreadsheet=SHEET_URL).dropna(how='all')
except:
    portfolio_df = pd.DataFrame(columns=['מניה', 'מחיר קנייה', 'כמות', 'תאריך'])

# --- פונקציות עזר ---
def get_mega_list():
    return list(set(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'NFLX', 'PLTR', 'MARA', 'COIN', 'RIOT', 'MSTR', 'RKLB', 'TSEM', 'BABA', 'SHOP', 'SQ', 'PYPL']))

def translate_sector(sector):
    translation = {'Technology': 'טכנולוגיה', 'Financial Services': 'פיננסים', 'Consumer Cyclical': 'צריכה'}
    return translation.get(sector, "כללי")

def scan_stocks(tickers, filters):
    results = []
    prog = st.progress(0)
    for i, ticker in enumerate(tickers):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            mkt_cap = info.get('marketCap', 0) / 1_000_000_000
            beta = info.get('beta', 0)
            y_return = info.get('52WeekChange', 0) * 100
            
            if beta >= filters['min_beta'] and y_return >= filters['min_return'] and mkt_cap <= filters['max_cap']:
                results.append({
                    'מניה': ticker, 'מחיר': price, 'Beta': round(beta, 2),
                    'תשואה שנתית': f"{round(y_return, 1)}%", 'שווי שוק ($B)': round(mkt_cap, 2),
                    'מגזר': translate_sector(info.get('sector')), 'תיאור': info.get('longBusinessSummary', '')
                })
        except: continue
        prog.progress((i + 1) / len(tickers))
    return pd.DataFrame(results)

# --- תפריט צד (Sidebar) ---
st.sidebar.header("⚙️ פילטרים")
f_cap = st.sidebar.slider("שווי שוק מקסימלי ($B)", 10, 500, 500)
f_beta = st.sidebar.slider("Beta מינימלית", 0.0, 4.0, 1.2)
f_return = st.sidebar.slider("תשואה שנתית מינימלית (%)", -50, 200, 5)

# --- חלק 1: סורק המניות ---
if st.button('🚀 הרץ סריקה'):
    mega_list = get_mega_list()
    df_results = scan_stocks(mega_list, {'min_beta': f_beta, 'min_return': f_return, 'max_cap': f_cap})
    
    if not df_results.empty:
        st.success(f"מצאתי {len(df_results)} מניות!")
        for _, row in df_results.iterrows():
            with st.expander(f"🔍 {row['מניה']} - מחיר: {row['מחיר']}$"):
                st.write(f"**מגזר:** {row['מגזר']} | **Beta:** {row['Beta']}")
                col_q, col_p, col_b = st.columns([1,1,1])
                q = col_q.number_input(f"כמות", min_value=1, key=f"q_{row['מניה']}")
                p = col_p.number_input(f"מחיר קנייה", value
