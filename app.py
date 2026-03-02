import streamlit as st
import streamlit.components.v1 as components
import requests
import math
import unicodedata

# --- 1. ページ基本設定 ---
st.set_page_config(
    page_title="Value up 収支", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. 【翻訳バグ・矢印復活パッチ】最上層(window.top)への命令 ---
components.html("""
    <script>
        const topDoc = window.top.document;
        
        // 1. ページ全体を日本語に設定
        topDoc.documentElement.lang = 'ja';
        
        // 2. Google翻訳拒否メタタグを注入
        if (!topDoc.querySelector('meta[name="google"]')) {
            const meta = topDoc.createElement('meta');
            meta.name = "google";
            meta.content = "notranslate";
            topDoc.head.appendChild(meta);
        }
        
        // 3. アイコン文字化け(keyboard_...)を物理的に消し、SVGで矢印を描画
        const style = topDoc.createElement('style');
        style.innerHTML = `
            span[data-testid="stSidebarCollapseIcon"] {
                font-size: 0 !important;
                color: transparent !important;
            }
            span[data-testid="stSidebarCollapseIcon"]::after {
                content: "";
                display: block;
                width: 24px; height: 24px;
                background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="gray"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>');
                background-size: contain;
                visibility: visible;
            }
        `;
        topDoc.head.appendChild(style);
    </script>
""", height=0)

# --- 3. デザインCSS（青色強調・カードデザインの完全復元） ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    font { vertical-align: inherit !important; } 
    
    * { 
        word-break: keep-all !important; 
        font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif !important; 
    }

    .main-header-title { font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 0.2rem; }
    .property-name-display { font-size: 1.2rem; font-weight: 700; color: #64748b; margin-bottom: 2rem; }
    .section-title { font-size: 1.2rem; font-weight: 800; color: #1e293b; border-left: 5px solid #3b82f6; padding-left: 12px; margin-top: 2rem; margin-bottom: 1rem; }

    /* 工事費・評価賃料・マイソク・RAM募集の数字を「青色」に */
    div[data-testid="stNumberInput"]:has(input[aria-label*="工事費"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="VU評価"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="マイソク"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="RAM募集"]) input {
        color: #3b82f6 !important;
        font-weight: 800 !important;
    }

    /* ボタンサイズ（スマホ対応） */
    div[data-testid="stNumberInput"] button { width: 50px !important; height: 45px !important; }
    div[data-testid="stNumberInput"] button:hover { background-color: #FF00A0 !important; color: white !important; }

    /* 粗利分析カード */
    .metric-card { 
        background-color: #ffffff; border: 1px solid #e2e8f0; 
        padding: 20px; border-radius: 10px; text-align: center; 
        height: 140px; display: flex; flex-direction: column; justify-content: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value { font-size: 1.6rem; font-weight: 800; color: #0f172a; }
    
    /* 会社総粗利（青枠ハイライト） */
    .total-profit-card { border: 2.5px solid #3b82f6 !important; background-color: #f0f7ff !important; }
    .total-profit-card .metric-label, .total-profit-card .metric-value { color: #3b82f6 !important; }

    .detail-card { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #f1f5f9; margin-top: 10px; }
    .detail-val-text { font-weight: 800; color: #1e293b; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# --- 4. kintoneデータ取得（シンプル版：最新を1件取得） ---
def fetch_kintone_data(ts_id):
    clean_id = unicodedata.normalize('NFKC', str(ts_id)).strip()
    url = f"https://ga-tech.cybozu.com/k/v1/records.json"
    headers = {"X-Cybozu-API-Token": st.secrets["KINTONE_API_TOKEN"]}
    
    query = f'(TS_ID = "{clean_id}"'
    if clean_id.isdigit():
        query += f' or TS_ID = {clean_id}'
    query += ')'
    
    # 重複があっても一番新しい（IDが大きい）レコードを優先します
    params = {
        "app": "479",
        "query": f'{query} order by $id desc limit 1'
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        return data["records"][0] if data.get("records") else None
    except:
        return None

def get_sales_price(rent_man, mng_rep_total, yield_percent):
    net_rent_monthly = rent_man - (mng_rep_total / 10000)
    if not yield_percent: return 0
    return math.floor(((net_rent_monthly * 12) / (yield_percent / 100)) / 10) * 10

def get_monthly_payment(principal_man, year, rate):
    p, r, n = principal_man * 10000, (rate / 100) / 12, year * 12
    if r == 0: return p / (n if n != 0 else 1)
    return int(p * (r * (1 + r) ** n) / ((1 + r) ** n - 1))

# --- 5. サイドバー ---
with st.sidebar:
    st.markdown('<div class="notranslate" style="font-weight:bold; font-size:1.1rem;">物件検索</div>', unsafe_allow_html=True)
    input_id = st.text_input("物件ID (TS_ID)", value=st.query_params.get("ts_id", ""))
    k_data = fetch_kintone_data(input_id) if input_id else None
    
    def get_val(field, default=0.0, divide=1):
        if k_data and field in k_data:
            val = k_data[field].get("value")
            if not val: return default
            try:
                clean_val = str(val).replace(',', '').replace('¥', '').replace('円', '').replace('万', '').strip()
                return float(clean_val) / divide
            except: return default
        return default

    st.divider()
    st.markdown('<div class="notranslate" style="font-weight:bold; font-size:1.1rem;">基本データ</div>', unsafe_allow_html=True)
    p_price = st.number_input("仕入価格(万)", value=int(get_val("仕入価格")), step=10)
    m_fee = st.number_input("管理費(円)", value=int(get_val("管理費")), step=100)
    r_fee = st.number_input("修繕積立金(円)", value=int(get_val("修繕積立金")), step=100)
    c_cost = st.number_input("工事費想定(万)", value=int(get_val("工事費想定")), step=10)
    st.divider()
    y_base = st.number_input("利回り_仕入時(%)", value=get_val("利回り_仕入時"), step=0.1)
    y_vu = st.number_input("利回り_価格設定(%)", value=get_val("利回り_価格設定"), step=0.1)
    st.divider()
    l_year = st.number_input("ローン年数(年)", value=int(get_val("ローン年数", default=26)), step=1)
    l_rate = st.number_input("金利(%)", value=2.0, step=0.1)

# --- 6. メイン画面 ---
st.markdown('<div class="main-header-title">Value up 収支シミュレーション</div>', unsafe_allow_html=True)

if not input_id:
    st.info("左側のサイドバーに物件IDを入力してください。")
    st.stop()

if not k_data:
    st.error("物件が見つかりません。")
    st.stop()

p_name = k_data["物件名"]["value"] if "物件名" in k_data else "物件名未設定"
st.markdown(f'<div class="property-name-display">物件名：{p_name}</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">賃料設定</div>', unsafe_allow_html=True)
cols = st.columns(4)
r_base = cols[0].number_input("仕入れ許容(万)", value=get_val("仕入れ許容賃料", divide=10000), step=0.1)
r_vu = cols[1].number_input("VU評価(万)", value=get_val("VU評価賃料", divide=10000), step=0.1)
r_mai = cols[2].number_input("マイソク(万)", value=get_val("マイソク賃料", divide=10000), step=0.1)
r_ram = cols[3].number_input("RAM募集(万)", value=get_val("RAM募集賃料", divide=10000), step=0.1)

mng_rep_total = m_fee + r_fee
price_base = get_sales_price(r_base, mng_rep_total, y_base)
price_vu = get_sales_price(r_vu, mng_rep_total, y_vu)
prof_a = price_base - p_price - (r_base * 3)
prof_b = price_vu - price_base - c_cost
total_p = prof_a + prof_b
rate_a = (prof_a / price_base * 100) if price_base != 0 else 0
total_r = (total_p / price_vu * 100) if price_vu != 0 else 0

st.markdown('<div class="section-title">粗利分析</div>', unsafe_allow_html=True)
s1, s2, s3 = st.columns(3)
with s1: st.markdown(f'<div class="metric-card"><div class="metric-label">仕入粗利</div><div class="metric-value">{prof_a:.1f}万</div><div style="color:#64748b; font-weight:600;">{rate_a:.2f}%</div></div>', unsafe_allow_html=True)
with s2: st.markdown(f'<div class="metric-card"><div class="metric-label">VU粗利</div><div class="metric-value">{prof_b:.1f}万</div><div style="color:#64748b; font-size:0.75rem;">工事費込</div></div>', unsafe_allow_html=True)
with s3: st.markdown(f'<div class="metric-card total-profit-card"><div class="metric-label">会社総粗利</div><div class="metric-value">{total_p:.1f}万</div><div style="font-weight:600;">{total_r:.2f}%</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">販売・CF詳細</div>', unsafe_allow_html=True)
res_cols = st.columns(4)
patterns = [("仕入れ時", r_base, price_base), ("VU評価時", r_vu, price_vu), ("マイソク", r_mai, price_vu), ("RAM募集", r_ram, price_vu)]
for i, (name, rent, s_price) in enumerate(patterns):
    net_rent = (rent * 10000) - mng_rep_total
    pay = get_monthly_payment(s_price, l_year, l_rate)
    with res_cols[i]:
        st.markdown(f'<div class="detail-card"><div style="font-size:0.75rem;color:#94a3b8;font-weight:800;margin-bottom:6px;">{name}</div><div class="detail-item">販売: <span class="detail-val-text">{int(s_price):,}</span>万</div><div class="detail-item">CF: <span class="detail-val-text">{int(net_rent - pay):,}</span>円/月</div></div>', unsafe_allow_html=True)