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
SHEET_URL = "https://docs.google.com/spreadsheets/d/1La-WwH7CE5UVV3dtSFTfhI1_FPQ3c8F99Y4ivsPsxkU/edit?usp=drivesdk"

# פונקציה לחיבור וטעינה
def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=SHEET_URL)
        return conn, df.dropna(how='all')
    except Exception as e:
        st.error(f"שגיאת חיבור לגליון: {e}")
        return None, pd.DataFrame(columns=['מניה', 'מחיר קנייה', 'כמות', 'תאריך'])

conn, portfolio_df = load_data()

# --- פונקציות עזר ---
def get_mega_list():
    # רשימה מורחבת של מניות מובילות
    return list(set(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'NFLX', 'PLTR', 'MARA', 'COIN', 'RIOT', 'MSTR', 'RKLB', 'TSEM', 'BABA', 'SHOP', 'SQ', 'PYPL', 'RIVN', 'AMD', 'INTC']))

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
            mkt_cap = (info.get('marketCap', 0) or 0) / 1_000_000_000
            beta = info.get('beta', 0) or 0
            y_return = (info.get('52WeekChange', 0) or 0) * 100
            
            if beta >= filters['min_beta'] and y_return >= filters['min_return'] and mkt_cap <= filters['max_cap']:
                results.append({
                    'מניה': ticker, 'מחיר': price, 'Beta': round(beta, 2),
                    'תשואה שנתית': f"{round(y_return, 1)}%", 'שווי שוק ($B)': round(mkt_cap, 2),
                    'מגזר': translate_sector(info.get('sector', '')), 'תיאור': info.get('longBusinessSummary', '')
                })
        except: continue
        prog.progress((i + 1) / len(tickers))
    return pd.DataFrame(results)

# --- תפריט צד (Sidebar) ---
st.sidebar.header("⚙️ פילטרים לסריקה")
f_cap = st.sidebar.slider("שווי שוק מקסימלי ($B)", 10, 3000, 1000)
f_beta = st.sidebar.slider("Beta מינימלית", 0.0, 4.0, 1.0)
f_return = st.sidebar.slider("תשואה שנתית מינימלית (%)", -50, 200, 5)

# --- חלק 1: סורק המניות ---
if st.button('🚀 הרץ סריקה מורחבת'):
    mega_list = get_mega_list()
    df_results = scan_stocks(mega_list, {'min_beta': f_beta, 'min_return': f_return, 'max_cap': f_cap})
    
    if not df_results.empty:
        st.success(f"מצאתי {len(df_results)} מניות מתאימות!")
        for _, row in df_results.iterrows():
            with st.expander(f"🔍 {row['מניה']} - מחיר נוכחי: {row['מחיר']}$"):
                st.write(f"**מגזר:** {row['מגזר']} | **Beta:** {row['Beta']}")
                st.caption(row['תיאור'][:300] + "...")
                
                col_q, col_p, col_b = st.columns([1,1,1])
                q = col_q.number_input(f"כמות", min_value=1, value=1, key=f"q_{row['מניה']}")
                p = col_p.number_input(f"מחיר קנייה", value=float(row['מחיר']), key=f"p_{row['מניה']}")
                
                if col_b.button(f"✅ קניתי {row['מניה']}", key=f"btn_{row['מניה']}"):
                    new_entry = pd.DataFrame([{"מניה": row['מניה'], "מחיר קנייה": p, "כמות": q, "תאריך": pd.Timestamp.now().strftime("%Y-%m-%d")}])
                    updated_p = pd.concat([portfolio_df[['מניה', 'מחיר קנייה', 'כמות', 'תאריך']], new_entry], ignore_index=True)
                    if conn:
                        conn.update(spreadsheet=SHEET_URL, data=updated_p)
                        st.toast(f"המניה {row['מניה']} נשמרה בתיק!")
                        st.rerun()

# --- חלק 2: הצגת התיק האישי ---
st.divider()
st.subheader("💰 התיק שלי (מעקב רווחים חי)")

if not portfolio_df.empty:
    with st.spinner('מעדכן נתונים מהבורסה...'):
        prices = []
        for t in portfolio_df['מניה']:
            try:
                s = yf.Ticker(t)
                prices.append(s.info.get('currentPrice') or s.info.get('regularMarketPrice'))
            except: prices.append(None)
        
        portfolio_df['מחיר נוכחי'] = prices
        portfolio_df['רווח/הפסד %'] = ((portfolio_df['מחיר נוכחי'] - portfolio_df['מחיר קנייה']) / portfolio_df['מחיר קנייה']) * 100
        portfolio_df['שווי ($)'] = portfolio_df['מחיר נוכחי'] * portfolio_df['כמות']
        
        total_val = portfolio_df['שווי ($)'].sum()
        portfolio_df['% מהתיק'] = (portfolio_df['שווי ($)'] / total_val) * 100
        
        st.metric("שווי תיק כולל", f"${total_val:,.2f}")
        
        # עיצוב טבלה
        def color_profit(val):
            color = '#27ae60' if val > 0 else '#e74c3c'
            return f'color: {color}; font-weight: bold'

        st.dataframe(portfolio_df.style.format({
            'מחיר קנייה': '{:.2f}$', 'מחיר נוכחי': '{:.2f}$',
            'רווח/הפסד %': '{:.2f}%', 'שווי ($)': '{:,.2f}$',
            '% מהתיק': '{:.1f}%'
        }).applymap(color_profit, subset=['רווח/הפסד %']), use_container_width=True)
    
    if st.sidebar.button("🗑️ מחק תיק"):
        if conn:
            conn.update(spreadsheet=SHEET_URL, data=pd.DataFrame(columns=['מניה', 'מחיר קנייה', 'כמות', 'תאריך']))
            st.rerun()
else:
    st.info("התיק שלך ריק כרגע.")
