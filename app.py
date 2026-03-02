import streamlit as st
import streamlit.components.v1 as components
import requests
import math
import unicodedata

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="Value up 収支", layout="wide", initial_sidebar_state="expanded")

# --- 2. 認証ロジック（正規化・不可視文字除去・大文字小文字無視） ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 文字列を極限までクリーンにする関数
def normalize_code(s):
    if not s: return ""
    # NFKC正規化（全角英数字を半角に、特殊文字を標準的なものに変換）
    s = unicodedata.normalize('NFKC', str(s))
    # 小文字化、空白・改行・不可視文字の完全除去
    return "".join(s.split()).lower()

# SecretsとURLからコードを取得してクリーンアップ
target_password = normalize_code(st.secrets.get("APP_PASSWORD", "admin123"))
url_code = normalize_code(st.query_params.get("code", ""))

# 自動ログイン判定（厳格な比較）
if url_code == target_password and target_password != "":
    st.session_state.authenticated = True

# 未認証時のみサイドバーにUIと診断情報を表示
if not st.session_state.authenticated:
    with st.sidebar:
        st.markdown('<div class="notranslate" style="font-weight:bold; font-size:1.1rem;">アクセス認証</div>', unsafe_allow_html=True)
        
        # --- 徹底診断ボード ---
        with st.expander("🔍 認証が通らない場合の診断"):
            st.write(f"・URLコード: `[{url_code}]` ({len(url_code)}文字)")
            st.write(f"・設定正解: `[{target_password}]` ({len(target_password)}文字)")
            st.write(f"・一致判定: **{'一致' if url_code == target_password else '不一致'}**")
            st.warning("上記が『一致』なのに画面が止まる場合は、ブラウザの再読み込みを試してください。")
        
        input_password = st.text_input("アクセスコードを入力", type="password")
        if normalize_code(input_password) == target_password:
            st.session_state.authenticated = True
            st.rerun()
        elif input_password:
            st.error("コードが正しくありません")
        st.info("このアプリの閲覧にはアクセスコードが必要です。")
    st.stop()

# --- 3. 【核】翻訳バグ・アイコン文字化け対策 ---
components.html("""
    <script>
        const nukeTranslation = () => {
            const topDoc = window.top.document;
            if (topDoc.documentElement.lang !== 'ja') { topDoc.documentElement.lang = 'ja'; }
            if (!topDoc.querySelector('meta[name="google"]')) {
                const meta = topDoc.createElement('meta');
                meta.name = 'google'; meta.content = 'notranslate';
                topDoc.head.appendChild(meta);
            }
            const sidebarBtn = topDoc.querySelector('button[data-testid="stSidebarCollapseButton"]');
            if (sidebarBtn) {
                sidebarBtn.classList.add('notranslate');
                sidebarBtn.setAttribute('translate', 'no');
            }
        };
        const observer = new MutationObserver(nukeTranslation);
        observer.observe(window.top.document.body, { childList: true, subtree: true });
        nukeTranslation();
    </script>
""", height=0)

# --- 4. デザインCSS（青色強調・アイコン保護） ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    font { vertical-align: inherit !important; } 
    span[data-testid="stSidebarCollapseIcon"] {
        font-size: 0 !important; color: transparent !important;
        position: relative !important; display: block !important;
        width: 24px !important; height: 24px !important;
    }
    span[data-testid="stSidebarCollapseIcon"]::before {
        content: ""; position: absolute; top: 0; left: 0; width: 24px; height: 24px;
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2364748b"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>');
        background-repeat: no-repeat; background-size: contain; visibility: visible !important;
    }
    .main-header-title { font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 0.2rem; }
    .property-name-display { font-size: 1.2rem; font-weight: 700; color: #64748b; margin-bottom: 2rem; }
    .section-title { font-size: 1.2rem; font-weight: 800; color: #1e293b; border-left: 5px solid #3b82f6; padding-left: 12px; margin-top: 2rem; margin-bottom: 1rem; }
    div[data-testid="stNumberInput"]:has(input[aria-label*="工事費"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="VU評価"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="マイソク"]) input,
    div[data-testid="stNumberInput"]:has(input[aria-label*="RAM募集"]) input {
        color: #3b82f6 !important; font-weight: 800 !important;
    }
    div[data-testid="stNumberInput"] button { width: 50px !important; height: 45px !important; }
    div[data-testid="stNumberInput"] button:hover { background-color: #FF00A0 !important; color: white !important; }
    .metric-card { 
        background-color: #ffffff; border: 1px solid #e2e8f0; padding: 20px; 
        border-radius: 10px; text-align: center; height: 140px; 
        display: flex; flex-direction: column; justify-content: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value { font-size: 1.6rem; font-weight: 800; color: #0f172a; }
    .total-profit-card { border: 2.5px solid #3b82f6 !important; background-color: #f0f7ff !important; }
    .total-profit-card .metric-label, .total-profit-card .metric-value, .total-profit-card .rate-text { color: #3b82f6 !important; }
    .detail-card { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #f1f5f9; margin-top: 10px; }
    .detail-val-text { font-weight: 800; color: #1e293b; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# --- 5. ロジック・表示 ---
def fetch_kintone_data(ts_id):
    clean_id = normalize_code(ts_id)
    url = f"https://ga-tech.cybozu.com/k/v1/records.json"
    headers = {"X-Cybozu-API-Token": st.secrets["KINTONE_API_TOKEN"]}
    query = f'TS_ID = "{clean_id}"'
    if clean_id.isdigit(): query += f' or TS_ID = {clean_id}'
    params = {"app": "479", "query": query}
    try:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        return data["records"][0] if data.get("records") else None
    except: return None

def get_sales_price(rent_man, mng_rep_total, yield_percent):
    net_rent_monthly = rent_man - (mng_rep_total / 10000)
    if not yield_percent: return 0
    return math.floor(((net_rent_monthly * 12) / (yield_percent / 100)) / 10) * 10

def get_monthly_payment(principal_man, year, rate):
    p, r, n = principal_man * 10000, (rate / 100) / 12, year * 12
    if r == 0: return p / (n if n != 0 else 1)
    return int(p * (r * (1 + r) ** n) / ((1 + r) ** n - 1))

with st.sidebar:
    st.markdown('<div class="notranslate" style="font-weight:bold; font-size:1.1rem;">物件検索</div>', unsafe_allow_html=True)
    input_id = st.text_input("物件ID (TS_ID)", value=st.query_params.get("ts_id", ""))
    k_data = fetch_kintone_data(input_id) if input_id else None
    
    def get_val(field, default=0.0, divide=1):
        if k_data and field in k_data:
            val = k_data[field].get("value")
            if not val: return default
            try: return float(str(val).replace(',', '').strip()) / divide
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
    l_year = st.number_input("ローン年数(年)", value=int(get_val("ローン年数", default=26)), step=1)
    l_rate = st.number_input("金利(%)", value=2.0, step=0.1)

st.markdown('<div class="main-header-title notranslate">Value up 収支シミュレーション</div>', unsafe_allow_html=True)
if input_id and k_data:
    p_name = k_data["物件名"]["value"] if "物件名" in k_data else "物件名未設定"
    st.markdown(f'<div class="property-name-display notranslate">物件名：{p_name}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title notranslate">賃料設定</div>', unsafe_allow_html=True)
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

    st.markdown('<div class="section-title notranslate">粗利分析</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    with s1: st.markdown(f'<div class="metric-card notranslate"><div class="metric-label">仕入粗利</div><div class="metric-value">{prof_a:.1f}万</div><div style="color:#64748b; font-weight:600;">{rate_a:.2f}%</div></div>', unsafe_allow_html=True)
    with s2: st.markdown(f'<div class="metric-card notranslate"><div class="metric-label">VU粗利</div><div class="metric-value">{prof_b:.1f}万</div><div style="color:#64748b; font-size:0.75rem;">工事費 {int(c_cost)}万円</div></div>', unsafe_allow_html=True)
    with s3: st.markdown(f'<div class="metric-card total-profit-card notranslate"><div class="metric-label">会社総粗利</div><div class="metric-value">{total_p:.1f}万</div><div class="rate-text" style="font-weight:600;">{total_r:.2f}%</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title notranslate">販売・CF詳細</div>', unsafe_allow_html=True)
    res_cols = st.columns(4)
    patterns = [("仕入れ時", r_base, price_base), ("VU評価時", r_vu, price_vu), ("マイソク", r_mai, price_vu), ("RAM募集", r_ram, price_vu)]
    for i, (name, rent, s_price) in enumerate(patterns):
        net_rent = (rent * 10000) - mng_rep_total
        pay = get_monthly_payment(s_price, l_year, l_rate)
        with res_cols[i]:
            st.markdown(f'<div class="detail-card notranslate"><div style="font-size:0.75rem;color:#94a3b8;font-weight:800;margin-bottom:6px;">{name}</div><div class="detail-item">販売: <span class="detail-val-text">{int(s_price):,}</span>万</div><div class="detail-item">CF: <span class="detail-val-text">{int(net_rent - pay):,}</span>円/月</div></div>', unsafe_allow_html=True)