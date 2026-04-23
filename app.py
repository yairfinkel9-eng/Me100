import streamlit as st
import yfinance as yf
import pandas as pd
from deep_translator import GoogleTranslator

# הגדרת העמוד
st.set_page_config(page_title="Pro Analyst Scanner", layout="wide")

# כותרת ממורכזת
st.markdown("<h1 style='text-align: center;'>🚀 סורק מניות אסטרטגי עם ניתוח מכפילים</h1>", unsafe_allow_html=True)
st.markdown("---")

@st.cache_data
def get_tickers_by_market(market_choice):
    try:
        if market_choice == 'S&P 500':
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            table = pd.read_html(url)[0]
            return table['Symbol'].tolist()
        elif market_choice == 'Nasdaq 100':
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            tables = pd.read_html(url)
            for df in tables:
                if 'Ticker' in df.columns: return df['Ticker'].tolist()
            return ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN']
        elif market_choice == 'בורסת תל אביב':
            return ['LEUMI.TA', 'POLI.TA', 'NICE.TA', 'ICL.TA', 'TEVA.TA', 'ELAL.TA', 'ESLT.TA', 'DSCT.TA']
        elif market_choice == 'Russell 2000 (מדגם)':
            return ['MSTR', 'SMCI', 'CELH', 'RKLB', 'SOFI', 'MARA', 'RIOT', 'UPST'] * 5
        return ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'META']
    except:
        return ['AAPL', 'MSFT', 'NVDA']

def get_sector_hebrew(sector):
    sectors = {
        'Technology': 'טכנולוגיה ושבבים', 'Communication Services': 'שירותי תקשורת',
        'Consumer Cyclical': 'צריכה', 'Financial Services': 'פיננסים',
        'Healthcare': 'בריאות', 'Energy': 'אנרגיה', 'Industrials': 'תעשייה'
    }
    return sectors.get(sector, "כללי")

def scan_stocks(tickers, f):
    results = []
    prog_bar = st.progress(0)
    status_text = st.empty()
    translator = GoogleTranslator(source='auto', target='iw')
    
    for i, t_name in enumerate(tickers):
        status_text.text(f"סורק: {t_name}")
        try:
            t_name_yf = t_name.replace('.', '-') if not t_name.endswith('.TA') else t_name
            stock = yf.Ticker(t_name_yf)
            info = stock.info
            
            # שליפת נתונים בסיסיים
            price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            mkt_cap = info.get('marketCap', 0) / 1_000_000_000
            y_return = (info.get('52WeekChange', 0) or 0) * 100
            vol = info.get('averageVolume', 0)
            beta = info.get('beta', 1.0) or 1.0
            
            # --- נתונים חדשים: מכפילים ---
            pe_ratio = info.get('trailingPE') # מכפיל רווח
            ps_ratio = info.get('priceToSalesTrailing12Months') # מכפיל מכירות
            debt_to_equity = info.get('debtToEquity', 0) or 0
            
            # חישוב תשואה שנתית ממוצעת מאז הנפקה
            hist = stock.history(period="max")
            avg_annual_return = 0
            if not hist.empty:
                ipo_ret = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                years = (hist.index[-1] - hist.index[0]).days / 365.25
                avg_annual_return = ipo_ret / years if years > 0 else 0

            # לוגיקת סינון (Filtering)
            # בודקים אם המכפילים קיימים לפני שחוסמים, כדי לא לפספס חברות ללא נתון
            if pe_ratio and f['pe_max'] != 0 and pe_ratio > f['pe_max']: continue
            if ps_ratio and f['ps_max'] != 0 and ps_ratio > f['ps_max']: continue
            if mkt_cap < f['cap_min'] or mkt_cap > f['cap_max']: continue
            if y_return < f['ret_min']: continue
            if vol < f['vol_min']: continue
            if beta > f['beta_max']: continue

            # תרגום
            try:
                heb_desc = translator.translate(info.get('longBusinessSummary', '')[:800])
            except:
                heb_desc = "אין תיאור זמין."

            # ציון לצורך הקצאה (תשואה/סיכון)
            score = max(y_return, 1) / max(beta, 0.5)

            results.append({
                'מניה': t_name,
                'מחיר': round(price, 2),
                'שווי שוק ($B)': round(mkt_cap, 1),
                'מכפיל רווח': round(pe_ratio, 2) if pe_ratio else "N/A",
                'מכפיל מכירות': round(ps_ratio, 2) if ps_ratio else "N/A",
                'תשואה שנתית %': round(y_return, 1),
                'תשואה ממוצעת %': round(avg_annual_return, 1),
                'Beta': round(beta, 2),
                'מגזר': get_sector_hebrew(info.get('sector')),
                'תיאור': heb_desc,
                'score': score
            })
        except: pass
        prog_bar.progress((i + 1) / len(tickers))
    
    status_text.empty()
    df = pd.DataFrame(results)
    if not df.empty:
        df['הקצאה מומלצת %'] = ((df['score'] / df['score'].sum()) * 100).round(1)
    return df

# --- ממשק משתמש סיידבר ---
st.sidebar.header("🌍 שוק יעד")
market = st.sidebar.selectbox("בחר שוק לסריקה", ['S&P 500', 'Nasdaq 100', 'בורסת תל אביב', 'Russell 2000 (מדגם)'])

st.sidebar.header("⚙️ פילטרים פיננסיים")
f_cap_min = st.sidebar.number_input("שווי שוק מינימלי ($B)", value=0)
f_cap_max = st.sidebar.number_input("שווי שוק מקסימלי ($B)", value=4000)
f_pe = st.sidebar.slider("מכפיל רווח מקסימלי (0 = ללא הגבלה)", 0, 100, 40)
f_ps = st.sidebar.slider("מכפיל מכירות מקסימלי (0 = ללא הגבלה)", 0, 50, 10)
f_ret = st.sidebar.slider("תשואה שנתית מינימלית %", -50, 100, 5)
f_beta = st.sidebar.slider("Beta מקסימלית (תנודתיות)", 0.0, 3.0, 1.5)
f_vol = st.sidebar.number_input("מחזור מסחר מינימלי (ממוצע)", value=500000)

limit = st.sidebar.slider("כמות מניות לסריקה", 10, 500, 40)

if st.button("🚀 הרץ סריקה חכמה"):
    tickers = get_tickers_by_market(market)[:limit]
    filters = {
        'pe_max': f_pe, 'ps_max': f_ps, 'cap_min': f_cap_min, 
        'cap_max': f_cap_max, 'ret_min': f_ret, 'beta_max': f_beta, 'vol_min': f_vol
    }
    
    df = scan_stocks(tickers, filters)
    
    if not df.empty:
        st.success(f"נמצאו {len(df)} מניות מתאימות!")
        st.dataframe(df.drop(columns=['תיאור', 'score']), use_container_width=True)
        
        for _, row in df.iterrows():
            with st.expander(f"🔍 ניתוח מניית {row['מניה']} ({row['הקצאה מומלצת %']}% מהתיק)"):
                st.write(f"### למה המניה כאן?")
                st.write(f"המניה נבחרה כי היא מציגה שילוב של **תשואה שנתית חזקה ({row['תשואה שנתית %']}%)** יחד עם תמחור נוח. ")
                
                # הסבר על מכפילים
                pe_text = f"מכפיל הרווח שלה עומד על {row['מכפיל רווח']}" if row['מכפיל רווח'] != "N/A" else "החברה עדיין לא מציגה רווח נקי (צמיחה)"
                st.write(f"* **תמחור:** {pe_text}. מכפיל המכירות הוא {row['מכפיל מכירות']}, מה שמעיד על היחס בין שווי השוק להכנסות.")
                st.write(f"* **סיכון:** ה-Beta היא {row['Beta']}, מה שאומר שהיא {'תנודתית יותר' if row['Beta'] > 1 else 'פחות תנודתית'} מהשוק.")
                st.write(f"* **פוטנציאל:** מאז הקמתה, היא הניבה ממוצע של {row['תשואה ממוצעת %']}% בכל שנה.")
                
                st.write("---")
                st.write(f"**תיאור פעילות:**")
                st.info(row['תיאור'])
    else:
        st.warning("לא נמצאו מניות. נסה להקל על הפילטרים (למשל להעלות מכפיל רווח או להוריד תשואה נדרשת).")
