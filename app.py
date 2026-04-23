import streamlit as st
import yfinance as yf
import pandas as pd

# הגדרות תצוגה
st.set_page_config(page_title="High Risk Stock Scanner", layout="wide")

st.title("🔥 סורק מניות בסיכון גבוה")
st.write("מאתר מניות קטנות, תנודתיות ובעלות פוטנציאל לזינוק אגרסיבי.")

# רשימה של מניות עם פוטנציאל תנודתיות גבוה (ביוטק, קריפטו, צמיחה)
growth_list = [
    'PLTR', 'SNOW', 'RIVN', 'LCID', 'U', 'AFRM', 'SOFI', 'MARA', 'RIOT', 'COIN',
    'UPST', 'AI', 'IONQ', 'QS', 'DKNG', 'PATH', 'GME', 'AMC', 'PLUG', 'NKLA',
    'DNA', 'CHPT', 'ROKU', 'TDOC', 'SQ', 'PYPL', 'HOOD', 'CLOV', 'SAVA', 'MSTR'
]

@st.cache_data(ttl=1800) # שומר נתונים לחצי שעה כדי שהאתר ירוץ מהר
def scan_high_risk(symbols):
    results = []
    for s in symbols:
        try:
            t = yf.Ticker(s)
            info = t.info
            
            # שליפת נתונים קריטיים
            beta = info.get('beta', 0) # תנודתיות (מעל 1.5 זה גבוה)
            mkt_cap = info.get('marketCap', 0) / 1_000_000_000 # שווי שוק במיליארדים
            short_ratio = info.get('shortPercentOfFloat', 0) * 100 # אחוז שורט
            price = info.get('currentPrice', 0)
            
            results.append({
                'מניה': s,
                'שם': info.get('longName', 'N/A'),
                'מחיר': price,
                'תנודתיות (Beta)': beta,
                'שווי שוק ($B)': round(mkt_cap, 2),
                'אחוז שורט (%)': round(short_ratio, 2)
            })
        except:
            continue
    return pd.DataFrame(results)

# סרגל צד לפילטרים - תוכל לשנות אותם באתר עצמו
st.sidebar.header("הגדרות צייד")
min_beta = st.sidebar.slider("תנודתיות מינימלית (Beta)", 1.0, 4.0, 1.5)
max_cap = st.sidebar.number_input("שווי שוק מקסימלי (במיליארד $)", value=10)
min_short = st.sidebar.slider("אחוז שורט מינימלי", 0, 50, 5)

if st.button('הרץ סריקה עכשיו'):
    with st.spinner('מחפש הזדמנויות...'):
        data = scan_high_risk(growth_list)
        
        # סינון לפי מה שבחרת בסליידרים
        filtered = data[
            (data['תנודתיות (Beta)'] >= min_beta) & 
            (data['שווי שוק ($B)'] <= max_cap) &
            (data['אחוז שורט (%)'] >= min_short)
        ]
        
        if not filtered.empty:
            st.success(f"נמצאו {len(filtered)} מניות שמתאימות לסיכון שלך!")
            st.dataframe(filtered.sort_values(by='תנודתיות (Beta)', ascending=False))
        else:
            st.warning("לא נמצאו מניות. נסה להוריד מעט את ה-Beta או את אחוז השורט.")

st.divider()
st.info("טיפ: מניות עם Beta גבוהה ושווי שוק נמוך נוטות לזנק חזק, אבל הן גם מסוכנות מאוד.")
