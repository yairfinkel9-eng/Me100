
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Pro Stock Analyst", layout="wide")

st.title("🔬 סורק מניות חכם עם ניתוח סיבות")

@st.cache_data(ttl=3600)
def get_tickers():
    tickers = []
    try:
        url_sp = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tickers += pd.read_html(url_sp)[0]['Symbol'].tolist()
        url_nas = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tickers += pd.read_html(url_nas)[4]['Ticker'].tolist()
    except:
        pass
    backup = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'AMZN', 'META', 'PLTR', 'MARA', 'COIN', 'MSTR']
    return list(set(tickers + backup))

def get_performance_since_ipo(t):
    try:
        hist = t.history(period="max")
        if not hist.empty:
            ipo_price = hist['Close'].iloc[0]
            current_price = hist['Close'].iloc[-1]
            return ((current_price - ipo_price) / ipo_price) * 100
    except:
        return 0
    return 0

def scan_with_logic(tickers, filters):
    results = []
    prog = st.progress(0)
    for i, ticker in enumerate(tickers):
        try:
            t = yf.Ticker(ticker.replace('.', '-'))
            info = t.info
            
            # שליפת נתונים
            beta = info.get('beta', 0)
            mkt_cap = info.get('marketCap', 0) / 1_000_000_000
            yearly_change = info.get('52WeekChange', 0) * 100
            price = info.get('currentPrice', 0)
            
            # בדיקת פילטרים
            if beta < filters['min_beta'] or mkt_cap > filters['max_cap'] or yearly_change < filters['min_return']:
                continue
            
            # חישוב תשואה מאז הנפקה (רק למי שעבר פילטר כדי לחסוך זמן)
            total_return = get_performance_since_ipo(t)
            
            results.append({
                'מניה': ticker,
                'שם': info.get('longName', 'N/A'),
                'מחיר': price,
                'Beta': round(beta, 2),
                'תשואה שנתית': f"{round(yearly_change, 2)}%",
                'תשואה מאז הנפקה': f"{int(total_return):,}%",
                'שווי שוק ($B)': round(mkt_cap, 2),
                'תיאור': info.get('longBusinessSummary', 'אין תיאור זמין.')
            })
        except:
            continue
        prog.progress((i + 1) / len(tickers))
    return pd.DataFrame(results)

# --- ממשק צד ---
st.sidebar.header("🔍 הגדרות סריקה")
f_beta = st.sidebar.slider("Beta מינימלית", 0.0, 4.0, 1.2)
f_return = st.sidebar.slider("תשואה שנתית מינימלית (%)", -50, 200, 10)
f_cap = st.sidebar.number_input("שווי שוק מקסימלי ($B)", value=1000)

if st.button('🚀 הרץ סריקה וניתוח'):
    tickers = get_tickers()
    st.info(f"סורק {len(tickers)} מניות... הניתוח לוקח רגע...")
    df = scan_with_logic(tickers, {'min_beta': f_beta, 'min_return': f_return, 'max_cap': f_cap})
    
    if not df.empty:
        st.success(f"נמצאו {len(df)} מניות מתאימות!")
        
        # הצגת הטבלה ללא עמודת התיאור הארוכה
        display_df = df.drop(columns=['תיאור'])
        st.dataframe(display_df, use_container_width=True)
        
        st.subheader("🧐 ניתוח מעמיק למניות שנמצאו:")
        for index, row in df.iterrows():
            with st.expander(f"למה המערכת בחרה את {row['מניה']}? (לחץ כאן)"):
                st.write(f"**שם החברה:** {row['שם']}")
                st.write(f"**ניתוח טכני קצר:** המניה נבחרה כי היא מציגה תנודתיות גבוהה (Beta של {row['Beta']}), מה שמעיד על פוטנציאל לרווח מהיר בתנודות שוק. בנוסף, היא עלתה ב-{row['תשואה שנתית']} בשנה האחרונה, מה שמראה על מומנטום חיובי.")
                st.write(f"**היסטוריה:** מאז הקמתה, המניה הניבה תשואה מדהימה של {row['תשואה מאז הנפקה']}.")
                st.write(f"**על החברה:** {row['תיאור'][:500]}...") # מציג רק 500 תווים ראשונים
    else:
        st.warning("לא נמצאו מניות. נסה להוריד את ה-Beta או התשואה השנתית.")

st.sidebar.markdown("---")
st.sidebar.caption("המידע מבוסס על Yahoo Finance. אין לראות בכך המלצה להשקעה.")

