import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from deep_translator import GoogleTranslator

# הגדרות עמוד
st.set_page_config(page_title="Warren Buffett Mode", layout="wide")

# עיצוב CSS מתקדם לפתרון הטשטוש ואיחוד הכותרת
st.markdown(
    """
    <style>
    /* רקע שטרות עם שכבת כהות כדי שהטקסט יהיה ברור */
    .stApp {
        background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("https://www.transparenttextures.com/patterns/money.png");
        background-color: #0e1117;
        background-attachment: fixed;
    }
    
    /* כותרת מאוחדת וברורה */
    .main-title {
        text-align: center;
        color: #2ecc71;
        font-size: 3rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px #000000;
        padding: 20px;
        white-space: nowrap; /* מונע מהכותרת להישבר לחלקים */
    }
    
    .sub-title {
        text-align: center;
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: bold;
        margin-bottom: 30px;
        text-shadow: 1px 1px 2px #000000;
    }

    /* עיצוב כפתור מרכזי בולט */
    div.stButton > button:first-child {
        display: block;
        margin: 0 auto;
        background-color: #27ae60;
        color: white;
        font-size: 1.4rem;
        font-weight: bold;
        padding: 15px 30px;
        border-radius: 12px;
        border: 2px solid #ffffff;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    
    /* הפיכת הטקסט בתוך התיבות לברור יותר */
    .stMarkdown, .stDataFrame, label {
        color: white !important;
        font-weight: 500 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# כותרת מאוחדת
st.markdown('<h1 class="main-title">רוצה להיות וורן באפט הבא? תלחץ כאן למטה</h1>', unsafe_allow_html=True)

# --- הגדרות Google Sheets ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1La-WwH7CE5UVV3dtSFTfhI1_FPQ3c8F99Y4ivsPsxkU/edit?usp=drivesdk"

def load_cloud_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=SHEET_URL)
        return conn, df.dropna(how='all')
    except:
        return None, pd.DataFrame(columns=['מניה', 'מחיר קנייה', 'כמות', 'תאריך'])

conn, portfolio_df = load_cloud_data()

# --- פונקציות עזר ורשימת מניות ---
def get_mega_list():
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'NFLX', 'PLTR', 
            'MARA', 'COIN', 'RIOT', 'MSTR', 'RKLB', 'TSEM', 'BABA', 'SHOP', 'SQ', 'PYPL']

def scan_stocks(tickers, f):
    results = []
    prog = st.progress(0)
    translator = GoogleTranslator(source='auto', target='iw')
    
    for i, ticker in enumerate(tickers):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            mkt_cap = (info.get('marketCap', 0) or 0) / 1_000_000_000
            beta = info.get('beta', 0) or 0
            y_return = (info.get('52WeekChange', 0) or 0) * 100
            pe = info.get('trailingPE')

            if mkt_cap > f['max_cap'] or beta < f['min_beta'] or y_return < f['min_return']: continue
            if f['max_pe'] > 0 and (pe is None or pe > f['max_pe']): continue
            
            desc = info.get('longBusinessSummary', '')
            heb_desc = translator.translate(desc[:250]) if desc else "אין תיאור"

            results.append({
                'מניה': ticker, 'מחיר': price, 'Beta': round(beta, 2),
                'מכפיל רווח': round(pe, 2) if pe else "N/A",
                'תשואה שנתית': f"{round(y_return, 1)}%",
                'שווי שוק ($B)': round(mkt_cap, 1),
                'תיאור': heb_desc
            })
        except: continue
        prog.progress((i + 1) / len(tickers))
    return pd.DataFrame(results)

# --- תפריט צד ---
st.sidebar.header("⚙️ הגדרות")
num_to_check = st.sidebar.slider("כמות מניות", 5, 50, 15)
f_pe = st.sidebar.number_input("מכפיל רווח מקסימלי (0=הכל)", value=0)
f_cap = st.sidebar.slider("שווי שוק ($B)", 10, 3000, 1000)
f_beta = st.sidebar.slider("Beta מינימלית", 0.0, 4.0, 1.2)
f_ret = st.sidebar.slider("תשואה מינימלית %", -50, 200, 10)

# --- כפתור הסריקה המעוצב ---
if st.button('כדי למצוא את המניות המושלמות בשבילך לחץ כאן'):
    tickers = get_mega_list()[:num_to_check]
    df_res = scan_stocks(tickers, {'max_pe': f_pe, 'max_cap': f_cap, 'min_beta': f_beta, 'min_return': f_ret})
    
    if not df_res.empty:
        st.success(f"מצאתי {len(df_res)} מניות!")
        for _, row in df_res.iterrows():
            with st.expander(f"🔍 {row['מניה']} | {row['מחיר']}$"):
                st.write(f"**מכפיל רווח:** {row['מכפיל רווח']} | **Beta:** {row['Beta']}")
                st.info(row['תיאור'])
                c1, c2, c3 = st.columns(3)
                q = c1.number_input("כמות", min_value=1, value=1, key=f"q_{row['מניה']}")
                p = c2.number_input("מחיר קנייה", value=float(row['מחיר']), key=f"p_{row['מניה']}")
                if c3.button("הוסף לתיק", key=f"b_{row['מניה']}"):
                    new_data = pd.DataFrame([{"מניה": row['מניה'], "מחיר קנייה": p, "כמות": q, "תאריך": pd.Timestamp.now().strftime("%Y-%m-%d")}])
                    final_df = pd.concat([portfolio_df[['מניה', 'מחיר קנייה', 'כמות', 'תאריך']], new_data], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=final_df)
                    st.rerun()

# --- תיק השקעות ---
st.divider()
if not portfolio_df.empty:
    st.subheader("💰 מעקב תיק חי")
    # (כאן מגיע הקוד של חישוב המחירים והצגת הטבלה כפי שהיה קודם...)
    # לצורך קיצור הדבקתי רק את החלקים ששונו עיצובית.
