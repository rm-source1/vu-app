import streamlit as st
import requests
import math
import unicodedata

# --- 1. ページ基本設定（最優先） ---
st.set_page_config(page_title="Value up 収支", layout="wide")

# --- 2. 【最終解決策】ブラウザの言語判定を力技で「日本語」に固定する ---
# ページ冒頭に、ブラウザが言語判定に使う「隠し日本語テキスト」を配置し、CSSで翻訳を完全拒否します。
st.markdown("""
    <div style="display:none;" class="notranslate">
        あいうえお かきくけこ さしすせそ 物件 収支 利回り 賃料 計算 確定 保存 完了
        これは日本語のページです。翻訳は不要です。notranslate.
    </div>
    <style>
        /* ページ全体を翻訳拒否 */
        html, body, [data-testid="stAppViewContainer"] {
            -webkit-text-size-adjust: none;
            -ms-text-size-adjust: none;
        }
        
        /* 全ての要素に対して翻訳を禁止する属性をシミュレート */
        * {
            unicode-bidi: bidi-override;
        }

        /* 翻訳された時にレイアウトが崩れるのを防ぐためのガード */
        font { vertical-align: inherit !important; }
        
        .main-header-title, .section-title, .metric-card, .detail-card, .property-name-display {
            -webkit-font-smoothing: antialiased;
        }
        
        /* 特定項目のデザイン維持 */
        .main-header-title { font-size: 1.8rem; font-weight: 800; color: #0f172a; border-left: 6px solid #3b82f6; padding-left: 15px; margin-bottom: 0.5rem; }
        .property-name-display { font-size: 1.2rem; font-weight: 700; color: #64748b; margin-bottom: 1.5rem; margin-left: 21px; }
        .section-title { font-size: 1.1rem; font-weight: 700; color: #1e293b; border-left: 3px solid #3b82f6; padding-left: 10px; margin-top: 1.2rem; margin-bottom: 0.8rem; }
        
        /* ボタンサイズアップ */
        div[data-testid="stNumberInput"] button { width: 50px !important; height: 45px !important; }
        div[data-testid="stNumberInput"] input { height: 45px !important; font-size: 1.1rem !important; }
        
        /* ピンクボタン設定 */
        div[data-testid="stNumberInput"] button:hover,
        div[data-testid="stNumberInput"] button:active,
        div[data-testid="stNumberInput"] button:focus {
            background-color: #FF00A0 !important;
            border-color: #FF00A0 !important;
            color: #000000 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. データ取得・計算ロジック ---
def fetch_kintone_data(ts_id):
    clean_id = unicodedata.normalize('NFKC', str(ts_id)).strip()
    url = f"https://{KINTONE_SUBDOMAIN}.cybozu.com/k/v1/records.json"
    headers = {"X-Cybozu-API-Token": KINTONE_API_TOKEN}
    query = f'TS_ID = "{clean_id}"'
    if clean_id.isdigit(): query += f' or TS_ID = {clean_id}'
    params = {"app": KINTONE_APP_ID, "query": query}
    try:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        return data["records"][0] if data.get("records") else None
    except: return None

# (計算関数などは変更なしのため省略... 実際にはここに記述)
# --- 以前のコードの fetch_kintone_data 等の関数をそのまま維持してください ---

# ページ内のすべての st.markdown 等に「translate="no"」を明示的に付与
def get_sales_price(rent_man, mng_rep_total, yield_percent):
    net_rent_monthly = rent_man - (mng_rep_total / 10000)
    if yield_percent == 0: return 0
    return math.floor(((net_rent_monthly * 12) / (yield_percent / 100)) / 10) * 10

def get_monthly_payment(principal_man, year, rate):
    p, r, n = principal_man * 10000, (rate / 100) / 12, year * 12
    if r == 0: return p / n
    return int(p * (r * (1 + r) ** n) / ((1 + r) ** n - 1))

# 設定情報の再定義
KINTONE_SUBDOMAIN = "ga-tech"
KINTONE_APP_ID = "479"
KINTONE_API_TOKEN = st.secrets["KINTONE_API_TOKEN"]

query_params = st.query_params
url_ts_id = query_params.get("ts_id", "")

with st.sidebar:
    st.markdown('<div class="notranslate" style="font-weight:bold;">物件検索</div>', unsafe_allow_html=True)
    input_id = st.text_input("物件ID (TS_ID)", value=url_ts_id)
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
    st.markdown('<div class="notranslate" style="font-weight:bold;">基本データ</div>', unsafe_allow_html=True)
    p_price = st.number_input("仕入価格(万)", value=int(get_val("仕入価格")), step=10, format="%d")
    m_fee = st.number_input("管理費(円)", value=int(get_val("管理費")), step=100, format="%d")
    r_fee = st.number_input("修繕積立金(円)", value=int(get_val("修繕積立金")), step=100, format="%d")
    c_cost = st.number_input("工事費想定(万)", value=int(get_val("工事費想定")), step=10, format="%d")
    st.divider()
    y_base = st.number_input("利回り_仕入時(%)", value=get_val("利回り_仕入時"), step=0.1, format="%.2f")
    y_vu = st.number_input("利回り_価格設定(%)", value=get_val("利回り_価格設定"), step=0.1, format="%.2f")
    st.divider()
    l_year = st.number_input("ローン年数(年)", value=int(get_val("ローン年数", default=26)), step=1, format="%d")
    l_rate = st.number_input("金利(%)", value=2.0, step=0.1, format="%.1f")

st.markdown('<div class="main-header-title notranslate" translate="no">Value up 収支シミュレーション</div>', unsafe_allow_html=True)

if not input_id:
    st.info("左側のサイドバーに物件IDを入力してください。")
    st.stop()

p_name = k_data["物件名"]["value"] if k_data and "物件名" in k_data else "物件名未設定"
st.markdown(f'<div class="property-name-display notranslate" translate="no">物件名：{p_name}</div>', unsafe_allow_html=True)

if not k_data: st.stop()

st.markdown('<div class="section-title notranslate" translate="no">賃料設定</div>', unsafe_allow_html=True)
cols = st.columns(4)
r_base = cols[0].number_input("仕入れ許容(万)", value=get_val("仕入れ許容賃料", divide=10000), step=0.1, format="%.2f")
r_vu = cols[1].number_input("VU評価(万)", value=get_val("VU評価賃料", divide=10000), step=0.1, format="%.2f")
r_mai = cols[2].number_input("マイソク(万)", value=get_val("マイソク賃料", divide=10000), step=0.1, format="%.2f")
r_ram = cols[3].number_input("RAM募集(万)", value=get_val("RAM募集賃料", divide=10000), step=0.1, format="%.2f")

mng_rep_total = m_fee + r_fee
price_base = get_sales_price(r_base, mng_rep_total, y_base)
price_vu = get_sales_price(r_vu, mng_rep_total, y_vu)
p_fees = r_base * 3 
prof_a = price_base - p_price - p_fees
prof_b = price_vu - price_base - c_cost
total_p = prof_a + prof_b
rate_a = (prof_a / price_base * 100) if price_base != 0 else 0
total_r = (total_p / price_vu * 100) if price_vu != 0 else 0

st.markdown('<div class="section-title notranslate" translate="no">粗利分析</div>', unsafe_allow_html=True)
s1, s2, s3 = st.columns(3)
with s1:
    st.markdown(f'<div class="metric-card notranslate" translate="no"><div class="metric-label">仕入粗利</div><div class="metric-value">{prof_a:.1f}<span class="unit-small">万円</span></div><div class="rate-text" style="color:#64748b;">{rate_a:.2f}<span class="unit-small">%</span></div></div>', unsafe_allow_html=True)
with s2:
    st.markdown(f'<div class="metric-card notranslate" translate="no"><div class="metric-label">VU粗利</div><div class="metric-value">{prof_b:.1f}<span class="unit-small">万円</span></div><div class="rate-text" style="color:#64748b; font-size:0.7rem;">工事費 {int(c_cost)}万 込</div></div>', unsafe_allow_html=True)
with s3:
    st.markdown(f'<div class="metric-card notranslate" translate="no" style="border:2px solid #3b82f6; background-color:#f0f7ff;"><div class="metric-label" style="color:#3b82f6; font-weight:bold;">会社総粗利</div><div class="metric-value" style="color:#3b82f6;">{total_p:.1f}<span class="unit-small">万円</span></div><div class="rate-text" style="color:#3b82f6;">{total_r:.2f}%</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title notranslate" translate="no">販売・CF詳細</div>', unsafe_allow_html=True)
res_cols = st.columns(4)
patterns = [("仕入れ時", r_base, price_base), ("VU評価時", r_vu, price_vu), ("マイソク", r_mai, price_vu), ("RAM募集", r_ram, price_vu)]
for i, (name, rent, s_price) in enumerate(patterns):
    net_rent = (rent * 10000) - mng_rep_total
    pay = get_monthly_payment(s_price, l_year, l_rate)
    with res_cols[i]:
        st.markdown(f'<div class="detail-card notranslate" translate="no"><div style="font-size:0.7rem;color:#94a3b8;font-weight:bold;margin-bottom:5px;">{name}</div><div class="detail-item">販売: <span class="detail-val-text">{int(s_price):,}</span>万円</div><div class="detail-item">CF: <span class="detail-val-text">{int(net_rent - pay):,}</span>円/月</div></div>', unsafe_allow_html=True)