import streamlit.components.v1 as components
import streamlit as st
import math

# --- 0. スマホの自動翻訳・文字化け防止タグ ---
components.html('<script>document.documentElement.lang = "ja";</script>', height=0)

# --- 1. 計算用関数の定義 ---
def get_sales_price(rent_man, mng_rep_total, yield_percent):
    net_rent_monthly = rent_man - (mng_rep_total / 10000)
    if yield_percent == 0: return 0
    raw_price = (net_rent_monthly * 12) / (yield_percent / 100)
    return math.floor(raw_price / 10) * 10

def get_monthly_payment(principal_man, year, rate):
    p = principal_man * 10000
    r = (rate / 100) / 12
    n = year * 12
    if r == 0: return p / n
    payment = p * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return int(payment)

# --- 2. プロ仕様デザインCSS（最終版） ---
st.set_page_config(page_title="Value up 収支", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    * { word-break: keep-all !important; font-family: "Helvetica Neue", Arial, sans-serif; }
    
    .main .block-container {
        padding-top: 2.5rem !important; 
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2.5rem !important;
    }

    .main-header-title {
        font-size: 1.8rem !important;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 1.5rem;
        border-left: 6px solid #3b82f6;
        padding-left: 15px;
        line-height: 1.1;
    }

    .section-title {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-top: 1.2rem !important;
        margin-bottom: 0.8rem !important;
        border-left: 3px solid #3b82f6;
        padding-left: 10px;
        line-height: 1.2;
    }
    
    .sidebar-title {
        font-size: 1.0rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-bottom: 0.5rem !important;
    }
    hr { margin: 0.8rem 0 !important; }

    .sb-label {
        font-size: 0.75rem;
        color: #475569;
        display: flex;
        align-items: center;
        height: 31px;
    }

    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 12px 15px;
        border-radius: 8px;
        text-align: center;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-label { font-size: 0.75rem; color: #64748b; margin-bottom: 4px; }
    .metric-value { font-size: 1.2rem; font-weight: 700; color: #0f172a; }
    .unit-small { font-size: 0.75rem; font-weight: normal; color: inherit; margin-left: 2px; }
    .rate-text { font-size: 0.85rem; font-weight: 600; margin-top: 2px; }

    /* --- シミュレーション項目の数字を青に --- */
    div[data-testid="stNumberInput"]:has(input[aria-label*="工事費"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="VU評価時"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="マイソク"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="RAM募集"]) input {
        color: #3b82f6 !important;
        font-weight: 700 !important;
    }

    /* --- +-ボタンのマウスオーバー設定 --- */
    div[data-testid="stNumberInput"] button:hover {
        background-color: #FF00A0 !important;
        color: #000000 !important;
    }
    div[data-testid="stNumberInput"] button:hover svg {
        fill: #000000 !important;
        stroke: #000000 !important;
        color: #000000 !important;
    }

    .detail-card {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #f1f5f9;
        margin-top: 10px;
    }
    .detail-item { font-size: 0.85rem; color: #64748b; line-height: 1.6; }
    .detail-val-text { font-weight: 700; color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. サイドバー入力 ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">基本データ</div>', unsafe_allow_html=True)
    
    def sb_input(label, val, step, key, format=None, is_sim=False):
        c1, c2 = st.columns([1, 1])
        color = "#3b82f6" if is_sim else "#475569"
        weight = "700" if is