import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# הגדרות עמוד - מותאם לטלפון ולמחשב
st.set_page_config(page_title="My Portfolio Advisor", layout="wide")

st.markdown("<h1 style='text-align: center;'>💰 ניהול תיק השקעות חכם</h1>", unsafe_allow_html=True)

# קישור לגוגל שייטס (חובה להשתמש בחשבון פרטי כדי שיהיו הרשאות Editor לכולם)
SHEET_URL = "כאן_שמים_את_הקישור_מהחשבון_הפרטי"

# --- פונקציה לשליפת מחיר חי מהבורסה ---
def get_live_price(ticker):
    try:
        stock = yf.Ticker(ticker.replace('.', '-'))
        return stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
    except:
        return None

# --- חיבור וטעינה מהענן ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    existing_data = conn.read(spreadsheet=SHEET_URL)
    portfolio_df = existing_data.dropna(how='all')
except Exception as e:
    portfolio_df = pd.DataFrame(columns=['מניה', 'מחיר קנייה', 'כמות', 'תאריך'])

# --- חישובי תיק ---
if not portfolio_df.empty:
    with st.spinner('מעדכן נתונים חיים מהבורסה...'):
        # 1. שליפת מחיר עדכני לכל מניה
        portfolio_df['מחיר נוכחי'] = portfolio_df['מניה'].apply(get_live_price)
        
        # 2. חישוב רווח/הפסד באחוזים
        portfolio_df['רווח/הפסד %'] = ((portfolio_df['מחיר נוכחי'] - portfolio_df['מחיר קנייה']) / portfolio_df['מחיר קנייה']) * 100
        
        # 3. חישוב שווי הפוזיציה (בכסף)
        portfolio_df['שווי בתיק ($)'] = portfolio_df['מחיר נוכחי'] * portfolio_df['כמות']
        
        # 4. חישוב אחוז מהתיק הכולל
        total_value = portfolio_df['שווי בתיק ($)'].sum()
        portfolio_df['% מהתיק'] = (portfolio_df['שווי בתיק ($)'] / total_value) * 100

    # תצוגת מדדים ראשיים (Metrics)
    m1, m2 = st.columns(2)
    m1.metric("שווי תיק כולל", f"${total_value:,.2f}")
    
    avg_profit = portfolio_df['רווח/הפסד %'].mean()
    m2.metric("רווח/הפסד ממוצע", f"{avg_profit:.2f}%", delta=f"{avg_profit:.2f}%")

    st.subheader("📋 פירוט האחזקות שלך")
    
    # פונקציית עיצוב לצבעי רווח/הפסד
    def style_profit(val):
        color = '#27ae60' if val > 0 else '#e74c3c' # ירוק או אדום
        return f'color: {color}; font-weight: bold'

    # הצגת הטבלה עם העיצובים
    st.dataframe(portfolio_df.style.format({
        'מחיר קנייה': '{:.2f}$',
        'מחיר נוכחי': '{:.2f}$',
        'רווח/הפסד %': '{:.2f}%',
        'שווי בתיק ($)': '{:,.2f}$',
        '% מהתיק': '{:.1f}%'
    }).applymap(style_profit, subset=['רווח/הפסד %']), use_container_width=True)

# --- הוספת מניה חדשה ---
st.divider()
st.subheader("➕ הוספת מניה שקנית")
with st.container():
    c1, c2, c3 = st.columns(3)
    new_t = c1.text_input("סימול מניה (Ticker)", placeholder="למשל: NVDA")
    new_p = c2.number_input("מחיר קנייה (ב-$)", min_value=0.0, step=0.1)
    new_q = c3.number_input("כמות מניות", min_value=0.1, step=1.0)

    if st.button("💾 שמור בתיק וסנכרן לענן"):
        if new_t and new_p > 0 and new_q > 0:
            new_data = pd.DataFrame([{
                "מניה": new_t.upper(),
                "מחיר קנייה": new_p,
                "כמות": new_q,
                "תאריך": pd.Timestamp.now().strftime("%Y-%m-%d")
            }])
            
            # איחוד הנתונים ושמירה רק של עמודות הבסיס לענן
            combined_df = pd.concat([portfolio_df[['מניה', 'מחיר קנייה', 'כמות', 'תאריך']], new_data], ignore_index=True)
            
            try:
                conn.update(spreadsheet=SHEET_URL, data=combined_df)
                st.success(f"המניה {new_t.upper()} נוספה בהצלחה!")
                st.rerun() # רענון הדף לעדכון הטבלה
            except:
                st.error("שגיאה בסנכרון. וודא שהקישור לגליון תקין ושיש הרשאות עריכה.")
        else:
            st.warning("נא למלא את כל השדות בצורה תקינה.")

# כפתור מחיקה לניהול התיק
if not portfolio_df.empty:
    if st.sidebar.button("🗑️ מחק את כל התיק"):
        empty_df = pd.DataFrame(columns=['מניה', 'מחיר קנייה', 'כמות', 'תאריך'])
        conn.update(spreadsheet=SHEET_URL, data=empty_df)
        st.sidebar.success("התיק נמחק!")
        st.rerun()
