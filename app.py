import streamlit as st
import streamlit.components.v1 as components
import requests
import math

# --- 0. スマホの自動翻訳・文字化け防止スクリプト ---
components.html('<script>document.documentElement.lang = "ja";</script>', height=0)

# --- 1. 設定情報 ---
KINTONE_SUBDOMAIN = "ga-tech"
KINTONE_APP_ID = "479"
KINTONE_API_TOKEN = st.secrets["KINTONE_API_TOKEN"]

# --- 2. ページ基本設定 & デザインCSS ---
st.set_page_config(page_title="Value up 収支", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    * { word-break: keep-all !important; font-family: "Helvetica Neue", Arial, sans-serif; }
    
    .main-header-title { font-size: 1.8rem; font-weight: 800; color: #0f172a; border-left: 6px solid #3b82f6; padding-left: 15px; margin-bottom: 0.5rem; }
    .property-name-display { font-size: 1.2rem; font-weight: 700; color: #64748b; margin-bottom: 1.5rem; margin-left: 21px; }
    .section-title { font-size: 1.1rem; font-weight: 700; color: #1e293b; border-left: 3px solid #3b82f6; padding-left: 10px; margin-top: 1.2rem; margin-bottom: 0.8rem; }
    
    /* 桁区切り用の補助テキストスタイル */
    .comma-helper { font-size: 0.75rem; color: #3b82f6; font-weight: 600; margin-top: -15px; margin-bottom: 10px; text-align: right; }

    /* --- 特定項目の数字を青色に（太字） --- */
    div[data-testid="stNumberInput"]:has(input[aria-label*="工事費"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="VU評価"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="マイソク"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="RAM募集"]) input {
        color: #3b82f6 !important;
        font-weight: 700 !important;
    }

    /* --- ボタンの色制御（ピンク #FF00A0 統一） --- */
    div[data-testid="stNumberInput"] button:hover,
    div[data-testid="stNumberInput"] button:active,
    div[data-testid="stNumberInput"] button:focus {
        background-color: #FF00A0 !important;
        border-color: #FF00A0 !important;
        color: #000000 !important;
    }
    div[data-testid="stNumberInput"] button:hover svg,
    div[data-testid="stNumberInput"] button:active svg,
    div[data-testid="stNumberInput"] button:focus svg {
        fill: #000000 !important;
        stroke: #000000 !important;
    }

    /* カード系 */
    .metric-card { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; text-align: center; height: 110px; display: flex; flex-direction: column; justify-content: center; }
    .metric-label { font-size: 0.75rem; color: #64748b; margin-bottom: 4px; }
    .metric-value { font-size: 1.2rem; font-weight: 700; color: #0f172a; }
    .unit-small { font-size: 0.75rem; font-weight: normal; margin-left: 2px; }
    .rate-text { font-size: 0.85rem; font-weight: 600; margin-top: 2px; }
    .detail-card { background-color: #ffffff; padding: 12px; border-radius: 8px; border: 1px solid #f1f5f9; margin-top: 10px; }
    .detail-item { font-size: 0.85rem; color: #64748b; line-height: 1.6; }
    .detail-val-text { font-weight: 700; color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 関数定義 ---
def fetch_kintone_data(ts_id):
    url = f"https://{KINTONE_SUBDOMAIN}.cybozu.com/k/v1/records.json"
    headers = {"X-Cybozu-API-Token": KINTONE_API_TOKEN}
    params = {"app": KINTONE_APP_ID, "query": f'TS_ID = "{ts_id}"'}
    try:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        return data["records"][0] if data.get("records") else None
    except: return None

def get_sales_price(rent_man, mng_rep_total, yield_percent):
    net_rent_monthly = rent_man - (mng_rep_total / 10000)
    if yield_percent == 0: return 0
    return math.floor(((net_rent_monthly * 12) / (yield_percent / 100)) / 10) * 10

def get_monthly_payment(principal_man, year, rate):
    p, r, n = principal_man * 10000, (rate / 100) / 12, year * 12
    if r == 0: return p / n
    return int(p * (r * (1 + r) ** n) / ((1 + r) ** n - 1))

# --- 4. 物件検索 & データ取得 ---
query_params = st.query_params
url_ts_id = query_params.get("ts_id", "")

with st.sidebar:
    st.markdown('<div translate="no" style="font-weight:bold; margin-bottom:5px;">物件検索</div>', unsafe_allow_html=True)
    input_id = st.text_input("物件ID (TS_ID)", value=url_ts_id)
    k_data = fetch_kintone_data(input_id) if input_id else None
    
    if input_id and not k_data:
        st.error("物件が見つかりません")

    def get_val(field, default=0.0, divide=1):
        if k_data and field in k_data:
            val = k_data[field].get("value")
            try: return float(val) / divide if val else default
            except: return default
        return default

    st.divider()
    st.markdown('<div translate="no" style="font-weight:bold;">基本データ</div>', unsafe_allow_html=True)
    
    # --- 桁区切り補助付き入力欄 ---
    p_price = st.number_input("仕入価格(万)", value=int(get_val("仕入価格")), step=10, format="%d")
    st.markdown(f'<div class="comma-helper">¥ {p_price:,} 万</div>', unsafe_allow_html=True)

    m_fee = st.number_input("管理費(円)", value=int(get_val("管理費")), step=100, format="%d")
    st.markdown(f'<div class="comma-helper">¥ {m_fee:,} 円</div>', unsafe_allow_html=True)

    r_fee = st.number_input("修繕積立金(円)", value=int(get_val("修繕積立金")), step=100, format="%d")
    st.markdown(f'<div class="comma-helper">¥ {r_fee:,} 円</div>', unsafe_allow_html=True)

    c_cost = st.number_input("工事費想定(万)", value=int(get_val("工事費想定")), step=10, format="%d")
    st.markdown(f'<div class="comma-helper">¥ {c_cost:,} 万</div>', unsafe_allow_html=True)
    
    st.divider()
    y_base = st.number_input("利回り_仕入時(%)", value=get_val("利回り_仕入時"), step=0.1, format="%.2f")
    y_vu = st.number_input("利回り_価格設定(%)", value=get_val("利回り_価格設定"), step=0.1, format="%.2f")
    
    st.divider()
    l_year = st.number_input("ローン年数(年)", value=int(get_val("ローン年数", default=26)), step=1, format="%d")
    l_rate = st.number_input("金利(%)", value=2.0, step=0.1, format="%.1f")

# --- 5. メイン画面表示 ---
st.markdown('<div class="main-header-title" translate="no">Value up 収支シミュレーション</div>', unsafe_allow_html=True)

if not input_id:
    st.info("左側のサイドバーに物件IDを入力してください。")
    st.stop()

# 物件名表示
p_name = k_data["物件名"]["value"] if k_data and "物件名" in k_data else "物件名未設定"
st.markdown(f'<div class="property-name-display" translate="no">物件名：{p_name}</div>', unsafe_allow_html=True)

# 賃料入力
st.markdown('<div class="section-title" translate="no">賃料設定</div>', unsafe_allow_html=True)
cols = st.columns(4)
r_base = cols[0].number_input("仕入れ許容(万)", value=get_val("仕入れ許容賃料", divide=10000), step=0.1, format="%.2f")
r_vu = cols[1].number_input("VU評価(万)", value=get_val("VU評価賃料", divide=10000), step=0.1, format="%.2f")
r_mai = cols[2].number_input("マイソク(万)", value=get_val("マイソク賃料", divide=10000), step=0.1, format="%.2f")
r_ram = cols[3].number_input("RAM募集(万)", value=get_val("RAM募集賃料", divide=10000), step=0.1, format="%.2f")

# --- 6. 計算処理 ---
mng_rep_total = m_fee + r_fee
price_base = get_sales_price(r_base, mng_rep_total, y_base)
price_vu = get_sales_price(r_vu, mng_rep_total, y_vu)
p_fees = r_base * 3 
prof_a = price_base - p_price - p_fees
prof_b = price_vu - price_base - c_cost
total_p = prof_a + prof_b

rate_a = (prof_a / price_base * 100) if price_base != 0 else 0
total_r = (total_p / price_vu * 100) if price_vu != 0 else 0

# --- 7. 粗利分析表示 ---
st.markdown('<div class="section-title" translate="no">粗利分析</div>', unsafe_allow_html=True)
s1, s2, s3 = st.columns(3)
with s1:
    st.markdown(f"""<div class="metric-card" translate="no">
        <div class="metric-label">仕入粗利</div>
        <div class="metric-value">{prof_a:.1f}<span class="unit-small">万円</span></div>
        <div class="rate-text" style="color:#64748b;">{rate_a:.2f}<span class="unit-small">%</span></div>
    </div>""", unsafe_allow_html=True)
with s2:
    st.markdown(f"""<div class="metric-card" translate="no">
        <div class="metric-label">VU粗利</div>
        <div class="metric-value">{prof_b:.1f}<span class="unit-small">万円</span></div>
        <div class="rate-text" style="color:#64748b; font-size:0.7rem;">工事費 {int(c_cost):,}万 込</div>
    </div>""", unsafe_allow_html=True)
with s3:
    st.markdown(f"""<div class="metric-card" translate="no" style="border:2px solid #3b82f6; background-color:#f0f7ff;">
        <div class="metric-label" style="color:#3b82f6; font-weight:bold;">会社総粗利</div>
        <div class="metric-value" style="color:#3b82f6;">{total_p:.1f}<span class="unit-small">万円</span></div>
        <div class="rate-text" style="color:#3b82f6;">{total_r:.2f}%</div>
    </div>""", unsafe_allow_html=True)

# --- 8. 販売・CF詳細表示 ---
st.markdown('<div class="section-title" translate="no">販売・CF詳細</div>', unsafe_allow_html=True)
res_cols = st.columns(4)
patterns = [("仕入れ時", r_base, price_base), ("VU評価時", r_vu, price_vu), ("マイソク", r_mai, price_vu), ("RAM募集", r_ram, price_vu)]

for i, (name, rent, s_price) in enumerate(patterns):
    net_rent = (rent * 10000) - mng_rep_total
    pay = get_monthly_payment(s_price, l_year, l_rate)
    with res_cols[i]:
        st.markdown(f"""
        <div class="detail-card" translate="no">
            <div style="font-size:0.7rem;color:#94a3b8;font-weight:bold;margin-bottom:5px;">{name}</div>
            <div class="detail-item">販売: <span class="detail-val-text">{int(s_price):,}</span>万円</div>
            <div class="detail-item">CF: <span class="detail-val-text">{int(net_rent - pay):,}</span>円/月</div>
        </div>
        """, unsafe_allow_html=True)