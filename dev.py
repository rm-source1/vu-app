import streamlit as st
import streamlit.components.v1 as components
import requests
import math
import unicodedata

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="Value up 収支", layout="wide", initial_sidebar_state="expanded")

# --- 2. 認証ロジック ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def normalize_code(s):
    if not s: return ""
    s = unicodedata.normalize('NFKC', str(s))
    return "".join(s.split()).lower()

target_password = normalize_code(st.secrets.get("APP_PASSWORD", "admin123"))
url_code = normalize_code(st.query_params.get("code", ""))

if url_code == target_password and target_password != "":
    st.session_state.authenticated = True

if not st.session_state.authenticated:
    with st.sidebar:
        st.markdown('<div class="notranslate" style="font-weight:bold; font-size:1.1rem;">アクセス認証</div>', unsafe_allow_html=True)
        input_password = st.text_input("アクセスコードを入力", type="password")
        if normalize_code(input_password) == target_password:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# --- 3. kintoneデータ連携関数 ---
def fetch_kintone_data(ts_id):
    clean_id = normalize_code(ts_id)
    url = f"https://ga-tech.cybozu.com/k/v1/records.json"
    headers = {"X-Cybozu-API-Token": st.secrets["KINTONE_API_TOKEN"]}
    query = f'TS_ID = "{clean_id}"'
    if clean_id.isdigit(): query += f' or TS_ID = {clean_id}'
    params = {"app": "479", "query": f"{query} order by $id desc limit 1"}
    try:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        return data["records"][0] if data.get("records") else None
    except: return None

def update_kintone_record(record_id, payload):
    url = f"https://ga-tech.cybozu.com/k/v1/record.json"
    headers = {
        "X-Cybozu-API-Token": st.secrets["KINTONE_API_TOKEN"],
        "Content-Type": "application/json"
    }
    data = {"app": "479", "id": record_id, "record": payload}
    try:
        resp = requests.put(url, json=data, headers=headers)
        return resp.status_code == 200
    except: return False

# --- 4. デザインCSS（確定後の黒字化を含む） ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    font { vertical-align: inherit !important; } 
    span[data-testid="stSidebarCollapseIcon"] { font-size: 0 !important; color: transparent !important; position: relative !important; display: block !important; width: 24px !important; height: 24px !important; }
    span[data-testid="stSidebarCollapseIcon"]::before { content: ""; position: absolute; top: 0; left: 0; width: 24px; height: 24px; background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2364748b"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>'); background-repeat: no-repeat; background-size: contain; visibility: visible !important; }
    .main-header-title { font-size: 2rem; font-weight: 800; color: #0f172a; margin-bottom: 0.2rem; }
    .property-name-display { font-size: 1.4rem; font-weight: 700; color: #1e293b; line-height: 2.2; } /* 物件名の高さを調整 */
    .section-title { font-size: 1.2rem; font-weight: 800; color: #1e293b; border-left: 5px solid #3b82f6; padding-left: 12px; margin-top: 1.5rem; margin-bottom: 1rem; }
    
    /* 入力フォームの基本色（青） */
    div[data-testid="stNumberInput"] input { color: #3b82f6 !important; font-weight: 800 !important; }
    
    /* 確定（disabled）後の文字色を黒に強制上書き */
    div[data-testid="stNumberInput"] input:disabled {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        opacity: 1 !important;
    }

    .metric-card { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 20px; border-radius: 10px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .metric-value { font-size: 1.6rem; font-weight: 800; color: #0f172a; }
    .total-profit-card { border: 2.5px solid #3b82f6 !important; background-color: #f0f7ff !important; }
    .total-profit-card .metric-label, .total-profit-card .metric-value, .total-profit-card .rate-text { color: #3b82f6 !important; }
    .detail-card { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #f1f5f9; margin-top: 10px; }
    .detail-val-text { font-weight: 800; color: #1e293b; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

# --- 5. サイドバー（データ取得） ---
with st.sidebar:
    st.markdown('<div class="notranslate" style="font-weight:bold; font-size:1.1rem;">物件検索</div>', unsafe_allow_html=True)
    input_id = st.text_input("物件ID (TS_ID)", value=st.query_params.get("ts_id", ""))
    k_data = fetch_kintone_data(input_id) if input_id else None

    is_fixed = False
    if k_data and "条件確定" in k_data:
        is_fixed = "確認済" in k_data["条件確定"].get("value", [])

    def get_val(field, default=0.0, divide=1):
        if k_data and field in k_data:
            val = k_data[field].get("value")
            if not val: return default
            try: return float(str(val).replace(',', '').strip()) / divide
            except: return default
        return default

    st.divider()
    lock_label = " (🔒 確定済)" if is_fixed else ""
    st.markdown(f'<div class="notranslate" style="font-weight:bold; font-size:1.1rem;">基本データ{lock_label}</div>', unsafe_allow_html=True)
    p_price = st.number_input("仕入価格(万)", value=int(get_val("仕入価格")), step=10, disabled=is_fixed)
    m_fee = st.number_input("管理費(円)", value=int(get_val("管理費")), step=100, disabled=is_fixed)
    r_fee = st.number_input("修繕積立金(円)", value=int(get_val("修繕積立金")), step=100, disabled=is_fixed)
    c_cost = st.number_input("工事費想定(万)", value=int(get_val("工事費想定")), step=10, disabled=is_fixed)
    st.divider()
    y_base = st.number_input("利回り_仕入時(%)", value=get_val("利回り_仕入時"), step=0.1, disabled=is_fixed)
    y_vu = st.number_input("利回り_価格設定(%)", value=get_val("利回り_価格設定"), step=0.1, disabled=is_fixed)
    l_year = st.number_input("ローン年数(年)", value=int(get_val("ローン年数", default=26)), step=1, disabled=is_fixed)
    l_rate = st.number_input("金利(%)", value=get_val("金利", default=2.0), step=0.1, disabled=is_fixed)

# --- 6. メイン表示エリア ---
st.markdown('<div class="main-header-title notranslate">Value up 収支シミュレーション</div>', unsafe_allow_html=True)

if input_id and k_data:
    p_name = k_data["物件名"]["value"] if "物件名" in k_data else "物件名未設定"
    
    # ★ポイント1: 変数の定義を「ボタン」より先に持ってくる（NameError回避）
    st.markdown('<div class="section-title notranslate">賃料設定</div>', unsafe_allow_html=True)
    rent_cols = st.columns(4)
    r_base = rent_cols[0].number_input("仕入れ許容(万)", value=get_val("仕入れ許容賃料", divide=10000), step=0.1, disabled=is_fixed)
    r_vu = rent_cols[1].number_input("VU評価(万)", value=get_val("VU評価賃料", divide=10000), step=0.1, disabled=is_fixed)
    r_mai = rent_cols[2].number_input("マイソク(万)", value=get_val("マイソク賃料", divide=10000), step=0.1, disabled=is_fixed)
    r_ram = rent_cols[3].number_input("RAM募集(万)", value=get_val("RAM募集賃料", divide=10000), step=0.1, disabled=is_fixed)

    # ★ポイント2: 物件名とボタンを横並びにする
    st.divider()
    title_col, action_col = st.columns([7, 3])
    with title_col:
        st.markdown(f'<div class="property-name-display notranslate">物件名：{p_name}</div>', unsafe_allow_html=True)
    with action_col:
        if is_fixed:
            st.button("✅ 条件確定済み", disabled=True, use_container_width=True)
        else:
            if st.button("🚀 条件を確定して保存", type="primary", use_container_width=True):
                payload = {
                    "VU評価賃料": {"value": r_vu * 10000},
                    "マイソク賃料": {"value": r_mai * 10000},
                    "RAM募集賃料": {"value": r_ram * 10000},
                    "工事費想定": {"value": c_cost},
                    "利回り_仕入時": {"value": y_base},
                    "利回り_価格設定": {"value": y_vu},
                    "ローン年数": {"value": l_year},
                    "金利": {"value": l_rate},
                    "条件確定": {"value": ["確認済"]},
                    "VU可否": {"value": "パス準備"}
                }
                if update_kintone_record(k_data["$id"]["value"], payload):
                    st.success("保存完了！")
                    st.rerun()
                else:
                    st.error("保存失敗。")

    # --- 計算ロジックと結果表示 ---
    mng_total = m_fee + r_fee
    p_base = math.floor((((r_base - (mng_total/10000))*12)/(y_base/100))/10)*10 if y_base else 0
    p_vu = math.floor((((r_vu - (mng_total/10000))*12)/(y_vu/100))/10)*10 if y_vu else 0
    prof_a = p_base - p_price - (r_base * 3)
    prof_b = p_vu - p_base - c_cost
    total_p = prof_a + prof_b
    total_r = (total_p / p_vu * 100) if p_vu else 0

    st.markdown('<div class="section-title notranslate">粗利分析</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    with s1: st.markdown(f'<div class="metric-card"><div class="metric-label">仕入粗利</div><div class="metric-value">{prof_a:.1f}万</div></div>', unsafe_allow_html=True)
    with s2: st.markdown(f'<div class="metric-card"><div class="metric-label">VU粗利</div><div class="metric-value">{prof_b:.1f}万</div><div style="font-size:0.75rem;">工事費 {int(c_cost)}万</div></div>', unsafe_allow_html=True)
    with s3: st.markdown(f'<div class="metric-card total-profit-card"><div class="metric-label">会社総粗利</div><div class="metric-value">{total_p:.1f}万</div><div class="rate-text" style="font-weight:600; color:#3b82f6;">{total_r:.2f}%</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title notranslate">販売・CF詳細</div>', unsafe_allow_html=True)
    res = st.columns(4)
    patterns = [("仕入れ時", r_base, p_base), ("VU評価時", r_vu, p_vu), ("マイソク", r_mai, p_vu), ("RAM募集", r_ram, p_vu)]
    for i, (name, rent, sales) in enumerate(patterns):
        net_rent = (rent * 10000) - mng_total
        pay = int((sales*10000)*((l_rate/100/12)*(1+l_rate/100/12)**(l_year*12))/((1+l_rate/100/12)**(l_year*12)-1)) if l_rate and l_year else 0
        yld = (net_rent * 12) / (sales * 10000) * 100 if sales else 0
        with res[i]:
            st.markdown(f'<div class="detail-card"><b>{name}</b><br>販売: {int(sales):,}万<br>利回り: {yld:.2f}%<br>CF: {int(net_rent - pay):,}円/月</div>', unsafe_allow_html=True)