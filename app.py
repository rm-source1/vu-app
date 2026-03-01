import streamlit as st
import requests
import math

# --- 1. 設定情報 ---
KINTONE_SUBDOMAIN = "ga-tech"
KINTONE_APP_ID = "479"
# SecretsからAPIトークンを取得
KINTONE_API_TOKEN = st.secrets["KINTONE_API_TOKEN"]

# --- 2. ページ基本設定 ---
st.set_page_config(page_title="Value up 収支", layout="wide")

# デザインCSS
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    * { word-break: keep-all !important; font-family: "Helvetica Neue", Arial, sans-serif; }
    .main-header-title { font-size: 1.8rem; font-weight: 800; color: #0f172a; border-left: 6px solid #3b82f6; padding-left: 15px; margin-bottom: 1.5rem; }
    .section-title { font-size: 1.1rem; font-weight: 700; color: #1e293b; border-left: 3px solid #3b82f6; padding-left: 10px; margin-top: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. データ取得関数 ---
def fetch_kintone_data(ts_id):
    url = f"https://{KINTONE_SUBDOMAIN}.cybozu.com/k/v1/records.json"
    headers = {"X-Cybozu-API-Token": KINTONE_API_TOKEN}
    params = {
        "app": KINTONE_APP_ID,
        "query": f'TS_ID = "{ts_id}"'
    }
    try:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        if data.get("records"):
            return data["records"][0]
        return None
    except:
        return None

# --- 4. ID管理（URLパラメータ対応） ---
query_params = st.query_params
url_ts_id = query_params.get("ts_id", "")

# --- 5. サイドバー：物件検索 ---
with st.sidebar:
    st.markdown('<div style="font-weight:bold; margin-bottom:5px;">物件検索</div>', unsafe_allow_html=True)
    # URLにIDがあれば初期値に入れ、なければ空欄にする
    input_id = st.text_input("物件ID (TS_ID)", value=url_ts_id)
    
    k_data = None
    if input_id:
        k_data = fetch_kintone_data(input_id)
        if not k_data:
            st.error("物件が見つかりません")
    
    st.divider()
    st.markdown('<div style="font-weight:bold;">基本データ</div>', unsafe_allow_html=True)

    def get_val(field):
        if k_data and field in k_data:
            val = k_data[field]["value"]
            return float(val) if val else 0.0
        return 0.0

    # 各数値をキントーンから取得（IDがなければ0になる）
    p_price = st.number_input("仕入価格(万)", value=get_val("仕入価格"), step=10.0)
    m_fee = st.number_input("管理費(円)", value=get_val("管理費"), step=100.0)
    r_fee = st.number_input("修繕積立金(円)", value=get_val("修繕積立金"), step=100.0)
    c_cost = st.number_input("工事費想定(万)", value=get_val("工事費想定"), step=10.0)
    
    st.divider()
    y_base = st.number_input("利回り_仕入時(%)", value=get_val("利回り_仕入時"), step=0.1, format="%.2f")
    y_vu = st.number_input("利回り_価格設定(%)", value=get_val("利回り_価格設定"), step=0.1, format="%.2f")
    
    st.divider()
    l_year = st.number_input("ローン年数(年)", value=int(get_val("ローン年数")), step=1)
    l_rate = st.number_input("金利(%)", value=2.0, step=0.1)

# --- 6. メイン画面 ---
st.markdown('<div class="main-header-title">Value up 収支シミュレーション</div>', unsafe_allow_html=True)

if not input_id:
    st.info("左側のサイドバーに物件IDを入力してください。")
    st.stop()

st.markdown('<div class="section-title">賃料設定</div>', unsafe_allow_html=True)
col_a, col_b, col_c, col_d = st.columns(4)

r_base = col_a.number_input("仕入れ許容賃料(万)", value=get_val("仕入れ許容賃料"), step=0.1)
r_vu = col_b.number_input("VU評価賃料(万)", value=get_val("VU評価賃料"), step=0.1)
r_mai = col_c.number_input("マイソク賃料(万)", value=get_val("マイソク賃料"), step=0.1)
r_ram = col_d.number_input("RAM募集賃料(万)", value=get_val("RAM募集賃料"), step=0.1)

st.success(f"物件 ID: {input_id} のデータを読み込みました。")