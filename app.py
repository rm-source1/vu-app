import streamlit as st
import math

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

# --- 2. プロ仕様デザインCSS（翻訳防止属性を追加） ---
st.set_page_config(page_title="Value up 収支", layout="wide")

st.markdown("""
    <style>
    /* サイト全体を翻訳対象から外す設定（強力なヒント） */
    .main, [data-testid="stSidebar"] {
        unicode-bidi: isolate;
    }
    
    .main { background-color: #f8fafc; }
    * { word-break: keep-all !important; font-family: "Helvetica Neue", Arial, sans-serif; }
    
    .main .block-container {
        padding-top: 2.5rem !important; 
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    .main-header-title {
        font-size: 1.8rem !important;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 1.5rem;
        border-left: 6px solid #3b82f6;
        padding-left: 15px;
    }

    .section-title {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-top: 1.2rem !important;
        margin-bottom: 0.8rem !important;
        border-left: 3px solid #3b82f6;
        padding-left: 10px;
    }
    
    .sidebar-title {
        font-size: 1.0rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }

    .sb-label {
        font-size: 0.75rem;
        color: #475569;
        display: flex;
        align-items: center;
        height: 31px;
    }

    /* 粗利カード */
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

    /* 数字の青色強調 */
    div[data-testid="stNumberInput"]:has(input[aria-label*="工事費"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="VU評価時"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="マイソク"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="RAM募集"]) input {
        color: #3b82f6 !important;
        font-weight: 700 !important;
    }

    /* ホバー時のピンク背景 */
    div[data-testid="stNumberInput"] button:hover {
        background-color: #FF00A0 !important;
        color: #000000 !important;
    }
    div[data-testid="stNumberInput"] button:hover svg {
        fill: #000000 !important;
        stroke: #000000 !important;
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
    # translate="no" を入れて翻訳を強制拒否
    st.markdown('<div class="sidebar-title" translate="no">基本データ</div>', unsafe_allow_html=True)
    
    def sb_input(label, val, step, key, format=None, is_sim=False):
        c1, c2 = st.columns([1, 1])
        color = "#3b82f6" if is_sim else "#475569"
        weight = "700" if is_sim else "400"
        # ここに翻訳拒否タグを挿入
        c1.markdown(f'<div class="sb-label" translate="no" style="color:{color}; font-weight:{weight};">{label}</div>', unsafe_allow_html=True)
        return c2.number_input(label, value=val, step=step, key=key, format=format, label_visibility="collapsed")

    p_price = sb_input("仕入価格(万)", 930, 10, "p_p")
    m_fee = sb_input("管理費(円)", 4500, 100, "m_f")
    r_fee = sb_input("修繕費(円)", 2000, 100, "r_f")
    c_cost = sb_input("工事費(万)", 100, 10, "c_c", is_sim=True) 
    
    st.divider()
    st.markdown('<div class="sidebar-title" translate="no">利回り設定</div>', unsafe_allow_html=True)
    y_base = sb_input("仕入時(%)", 4.6, 0.1, "y_b", format="%.2f")
    y_vu = sb_input("VU評価(%)", 4.6, 0.1, "y_v", format="%.2f")
    
    st.divider()
    st.markdown('<div class="sidebar-title" translate="no">ローン条件</div>', unsafe_allow_html=True)
    l_year = sb_input("年数(年)", 26, 1, "l_y")
    l_rate = sb_input("金利(%)", 2.0, 0.1, "l_r", format="%.1f")

# --- 4. 計算ロジック ---
mng_rep_total = m_fee + r_fee
pattern_names = ["仕入れ時", "VU評価時", "マイソク", "RAM募集"]
default_rents = [5.1, 6.1, 6.1, 7.0]

st.markdown('<div class="main-header-title" translate="no">Value up 収支シミュレーション</div>', unsafe_allow_html=True)

# --- 5. 賃料設定 ---
st.markdown('<div class="section-title" translate="no">賃料設定</div>', unsafe_allow_html=True)
input_cols = st.columns(4)
rents = {}

for i, name in enumerate(pattern_names):
    with input_cols[i]:
        color = "#3b82f6" if i > 0 else "#334155"
        # 翻訳拒否タグ
        st.markdown(f'<div translate="no" style="font-size: 0.85rem; font-weight: 700; color: {color}; margin-bottom: 4px;">{name}(万)</div>', unsafe_allow_html=True)
        rents[name] = st.number_input(f"{name}(万)", value=default_rents[i], key=f"r{i}", step=0.1, format="%.2f", label_visibility="collapsed")

# 利益計算
price_base = get_sales_price(rents["仕入れ時"], mng_rep_total, y_base)
price_vu = get_sales_price(rents["VU評価時"], mng_rep_total, y_vu)
p_fees = rents["仕入れ時"] * 3
prof_a = price_base - p_price - p_fees
prof_b = price_vu - price_base - c_cost
total_p = prof_a + prof_b
total_r = (total_p / price_vu * 100) if price_vu != 0 else 0
rate_a = (prof_a / price_base * 100) if price_base != 0 else 0

# --- 6. 粗利分析 ---
st.markdown('<div class="section-title" translate="no">粗利分析</div>', unsafe_allow_html=True)
s_col1, s_col2, s_col3 = st.columns(3)

with s_col1:
    st.markdown(f"""<div class="metric-card" translate="no">
        <div class="metric-label">仕入粗利</div>
        <div class="metric-value">{prof_a:.1f}<span class="unit-small">万円</span></div>
        <div class="rate-text" style="color:#0f172a;">{rate_a:.2f}<span class="unit-small">%</span></div>
    </div>""", unsafe_allow_html=True)

with s_col2:
    st.markdown(f"""<div class="metric-card" translate="no">
        <div class="metric-label">VU粗利</div>
        <div class="metric-value">{prof_b:.1f}<span class="unit-small">万円</span></div>
        <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
            工事費 {c_cost:,}<span class="unit-small">万円</span>
        </div>
    </div>""", unsafe_allow_html=True)

with s_col3:
    st.markdown(f"""<div class="metric-card" translate="no" style="border: 2px solid #3b82f6; background-color: #f0f7ff;">
        <div class="metric-label" style="color:#3b82f6; font-weight:bold;">会社総粗利</div>
        <div class="metric-value" style="color:#3b82f6;">{total_p:.1f}<span class="unit-small" style="color:#3b82f6;">万円</span></div>
        <div class="rate-text" style="color:#3b82f6; font-weight:600;">{total_r:.2f}<span class="unit-small">%</span></div>
    </div>""", unsafe_allow_html=True)

# --- 7. 販売・CF詳細 ---
st.markdown('<div class="section-title" translate="no">販売・CF詳細</div>', unsafe_allow_html=True)
res_cols = st.columns(4)

for i, name in enumerate(pattern_names):
    s_price = price_base if name == "仕入れ時" else price_vu
    net_rent = (rents[name] * 10000) - mng_rep_total
    actual_y = (net_rent * 12) / (s_price * 10000) * 100 if s_price != 0 else 0
    pay = get_monthly_payment(s_price, l_year, l_rate)
    cf = int(net_rent - pay)
    
    with res_cols[i]:
        st.markdown(f"""
        <div class="detail-card" translate="no">
            <div style="font-size: 0.7rem; color: #94a3b8; font-weight: bold; margin-bottom: 8px; text-transform: uppercase;">{name}</div>
            <div class="detail-item">販売: <span class="detail-val-text">{s_price:,}</span><span class="unit-small">万円</span></div>
            <div class="detail-item">実利: <span class="detail-val-text">{actual_y:.2f}</span><span class="unit-small">%</span></div>
            <div class="detail-item">CF: <span class="detail-val-text">{cf:,}</span><span class="unit-small">円/月</span></div>
        </div>
        """, unsafe_allow_html=True)