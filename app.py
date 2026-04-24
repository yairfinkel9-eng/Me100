import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from deep_translator import GoogleTranslator

# הגדרות עמוד
st.set_page_config(page_title="Warren Buffett Mode", layout="wide")

# עיצוב CSS מתקדם: רקע שטרות מאחורה, כותרת במרכז ועיצוב כפתורים
st.markdown(
    """
    <style>
    /* רקע שטרות מאחורי הכל */
    .stApp {
        background-image: url("https://www.transparenttextures.com/patterns/money.png");
        background-color: #0e1117;
        background-attachment: fixed;
    }
    
    /* כותרת מרכזית */
    .main-title {
        text-align: center;
        color: #2ecc71;
        font-size: 3rem;
        font-weight: bold;
        text-shadow: 3px 3px #000000;
        margin-top: 20px;
    }
    
    .sub-title {
        text-align: center;
        color: #f1c40f;
        font-size: 1.5rem;
        margin-bottom: 30px;
    }

    /* מרכז את הכפתור הראשי */
    div.stButton > button:first-child {
        display: block;
        margin: 0 auto;
        background-color: #27ae60;
        color: white;
        font-size: 1.2rem;
        padding: 10px 24px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# כותרת האפליקציה
st.markdown('<h1 class="main-title">רוצה להיות וורן באפט הבא?</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">תלחץ כאן למטה</p>', unsafe_allow_html=True)

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

# --- רשימת מניות לסריקה ---
def get_mega_list():
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'NFLX', 'PLTR',
        'MARA', 'COIN', 'RIOT', 'MSTR', 'RKLB', 'TSEM', 'BABA', 'SHOP', 'SQ', 'PYPL',
        'SMCI', 'ARM', 'MU', 'INTC', 'TSM', 'AVGO', 'QCOM', 'ASML', 'LRCX', 'AMAT',
        'PANW', 'CRWD', 'NET', 'SNOW', 'DDOG', 'ZS', 'OKTA', 'SOFI', 'GME', 'AMC',
        'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'BILI', 'PDD', 'BIDU', 'JPM', 'BAC'
    ]

# --- פונקציית סריקה ---
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

            if mkt_cap > f['max_cap']: continue
            if beta < f['min_beta']: continue
            if y_return < f['min_return']: continue
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
st.sidebar.header("⚙️ פילטרים")
num_to_check = st.sidebar.slider("כמות מניות לבדיקה", 5, 50, 15)
f_pe = st.sidebar.number_input("מכפיל רווח מקסימלי (0 = ללא פילטר)", value=0)
f_cap = st.sidebar.slider("שווי שוק מקסימלי ($B)", 10, 3000, 1000)
f_beta = st.sidebar.slider("Beta מינימלית (תנודתיות)", 0.0, 4.0, 1.2)
f_ret = st.sidebar.slider("תשואה שנתית מינימלית %", -50, 200, 10)

# --- כפתור הסריקה החדש ---
if st.button('כדי למצוא את המניות המושלמות בשבילך לחץ כאן'):
    tickers = get_mega_list()[:num_to_check]
    df_res = scan_stocks(tickers, {'max_pe': f_pe, 'max_cap': f_cap, 'min_beta': f_beta, 'min_return': f_ret})
    
    if not df_res.empty:
        st.success(f"מצאתי {len(df_res)} מניות שעשויות לעניין אותך!")
        for _, row in df_res.iterrows():
            with st.expander(f"🔍 {row['מניה']} | {row['מחיר']}$ | תשואה: {row['תשואה שנתית']}"):
                st.write(f"**מכפיל רווח:** {row['מכפיל רווח']} | **Beta:** {row['Beta']} | **שווי:** {row['שווי שוק ($B)']}B")
                st.info(row['תיאור'])
                
                c1, c2, c3 = st.columns([1,1,1])
                q = c1.number_input("כמות", min_value=1, value=1, key=f"q_{row['מניה']}")
                p = c2.number_input("מחיר קנייה", value=float(row['מחיר']), key=f"p_{row['מניה']}")
                if c3.button(f"✅ הוסף לתיק שלי", key=f"b_{row['מניה']}"):
                    new_data = pd.DataFrame([{"מניה": row['מניה'], "מחיר קנייה": p, "כמות": q, "תאריך": pd.Timestamp.now().strftime("%Y-%m-%d")}])
                    final_df = pd.concat([portfolio_df[['מניה', 'מחיר קנייה', 'כמות', 'תאריך']], new_data], ignore_index=True)
                    conn.update(spreadsheet=SHEET_URL, data=final_df)
                    st.toast("המניה נוספה לתיק!")
                    st.rerun()

# --- ניהול התיק ---
st.divider()
st.subheader("💰 מעקב תיק השקעות חי")

if not portfolio_df.empty:
    with st.spinner('מעדכן נתונים מהבורסה...'):
        current_prices = []
        for t in portfolio_df['מניה']:
            try: current_prices.append(yf.Ticker(t).info.get('currentPrice'))
            except: current_prices.append(None)
        
        portfolio_df['מחיר נוכחי'] = current_prices
        portfolio_df['רווח/הפסד %'] = ((portfolio_df['מחיר נוכחי'] - portfolio_df['מחיר קנייה']) / portfolio_df['מחיר קנייה']) * 100
        portfolio_df['שווי ($)'] = portfolio_df['מחיר נוכחי'] * portfolio_df['כמות']
        
        total_value = portfolio_df['שווי ($)'].sum()
        portfolio_df['% מהתיק'] = (portfolio_df['שווי ($)'] / total_value) * 100

    st.metric("שווי תיק כולל", f"${total_value:,.2f}")
    
    def style_p(val):
        color = '#27ae60' if val > 0 else '#e74c3c'
        return f'color: {color}; font-weight: bold'

    st.dataframe(portfolio_df.style.format({
        'מחיר קנייה': '{:.2f}$', 'מחיר נוכחי': '{:.2f}$',
        'רווח/הפסד %': '{:.2f}%', 'שווי ($)': '{:,.2f}$',
        '% מהתיק': '{:.1f}%'
    }).applymap(style_p, subset=['רווח/הפסד %']), use_container_width=True)
    
    if st.sidebar.button("🗑️ מחק את כל הנתונים"):
        conn.update(spreadsheet=SHEET_URL, data=pd.DataFrame(columns=['מניה', 'מחיר קנייה', 'כמות', 'תאריך']))
        st.rerun()
