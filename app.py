import streamlit as st
import requests
import math
import unicodedata

# --- 1. ページ基本設定 ---
st.set_page_config(page_title="Value up 収支", layout="wide")

# --- 2. デザインCSS（スマホ特化型・サイドバーなし） ---
st.markdown("""
    <style>
    /* サイドバーを物理的に消去 */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    .st-emotion-cache-1vq4p4l { padding: 1rem 1rem !important; } /* メインエリアの余白調整 */

    /* 全体の背景とフォント */
    .stApp { background-color: #f8fafc; }
    * { 
        word-break: keep-all !important; 
        font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif !important; 
    }
    
    /* ヘッダー・タイトル */
    .main-header-title { font-size: 1.6rem; font-weight: 800; color: #0f172a; border-left: 6px solid #3b82f6; padding-left: 15px; margin-bottom: 1rem; }
    .property-name-display { font-size: 1.1rem; font-weight: 700; color: #475569; background: #f1f5f9; padding: 10px 15px; border-radius: 8px; margin-bottom: 1.5rem; }
    .section-title { font-size: 1.1rem; font-weight: 700; color: #1e293b; border-left: 3px solid #3b82f6; padding-left: 10px; margin-top: 1.5rem; margin-bottom: 0.8rem; }
    
    /* 数値入力欄（スマホで押しやすいサイズ） */
    div[data-testid="stNumberInput"] button { width: 45px !important; height: 40px !important; }
    div[data-testid="stNumberInput"] input { height: 40px !important; font-size: 1.05rem !important; }
    
    /* ピンクボタン（ホバー時） */
    div[data-testid="stNumberInput"] button:hover { background-color: #FF00A0 !important; border-color: #FF00A0 !important; }

    /* 分析カードのデザイン向上 */
    .metric-card { 
        background-color: #ffffff; 
        border: 1px solid #e2e8f0; 
        padding: 15px; 
        border-radius: 12px; 
        text-align: center; 
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin-bottom: 10px;
    }
    .metric-label { font-size: 0.8rem; color: #64748b; margin-bottom: 4px; font-weight: bold; }
    .metric-value { font-size: 1.4rem; font-weight: 800; color: #0f172a; }
    .rate-text { font-size: 0.95rem; font-weight: 700; color: #3b82f6; margin-top: 2px; }

    /* 収支詳細カード */
    .detail-card { background-color: #ffffff; padding: 12px; border-radius: 10px; border: 1px solid #f1f5f9; margin-top: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .detail-val-text { font-weight: 700; color: #1e293b; font-size: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 取得・計算ロジック ---
def fetch_kintone_data(ts_id):
    if not ts_id: return None
    clean_id = unicodedata.normalize('NFKC', str(ts_id)).strip()
    subdomain = st.secrets.get("KINTONE_SUBDOMAIN", "ga-tech")
    url = f"https://{subdomain}.cybozu.com/k/v1/records.json"
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
    if r == 0: return p / n if n != 0 else 0
    return int(p * (r * (1 + r) ** n) / ((1 + r) ** n - 1))

# --- 4. メイン画面（最上部に検索と設定を集約） ---
st.markdown('<div class="main-header-title">Value up 収支シミュレーター</div>', unsafe_allow_html=True)

# 検索窓を一番上に配置
query_params = st.query_params
url_ts_id = query_params.get("ts_id", "")
input_id = st.text_input("🔍 物件ID (TS_ID) を入力", value=url_ts_id, placeholder="例: 3500321")

k_data = fetch_kintone_data(input_id)

def get_val(field, default=0.0, divide=1):
    if k_data and field in k_data:
        val = k_data[field].get("value")
        if not val: return default
        try:
            clean_val = str(val).replace(',', '').replace('¥', '').replace('円', '').replace('万', '').strip()
            return float(clean_val) / divide
        except: return default
    return default

# 「物件基本設定」を折りたたみの中に隠す（画面を広く使うため）
with st.expander("⚙️ 物件の基本データ（仕入価格・利回りなど）を調整する"):
    c1, c2 = st.columns(2)
    p_price = c1.number_input("仕入価格(万)", value=int(get_val("仕入価格")), step=10)
    m_fee = c2.number_input("管理費(円)", value=int(get_val("管理費")), step=100)
    r_fee = c1.number_input("修繕積立金(円)", value=int(get_val("修繕積立金")), step=100)
    c_cost = c2.number_input("工事費想定(万)", value=int(get_val("工事費想定")), step=10)
    
    st.divider()
    y_base = c1.number_input("利回り_仕入時(%)", value=get_val("利回り_仕入時"), step=0.1)
    y_vu = c2.number_input("利回り_価格設定(%)", value=get_val("利回り_価格設定"), step=0.1)
    
    st.divider()
    l_year = c1.number_input("ローン年数(年)", value=int(get_val("ローン年数", default=26)), step=1)
    l_rate = c2.number_input("金利(%)", value=2.0, step=0.1)

# 物件が見つかった場合のみ計算結果を表示
if input_id:
    if not k_data:
        st.error("物件が見つかりませんでした。IDを確認してください。")
    else:
        p_name = k_data["物件名"]["value"] if "物件名" in k_data else "物件名未設定"
        st.markdown(f'<div class="property-name-display">物件名：{p_name}</div>', unsafe_allow_html=True)

        # 賃料設定（2列×2行でスマホで見やすく）
        st.markdown('<div class="section-title">賃料設定</div>', unsafe_allow_html=True)
        r_cols = st.columns(2)
        r_base = r_cols[0].number_input("仕入れ許容(万)", value=get_val("仕入れ許容賃料", divide=10000), step=0.1)
        r_vu = r_cols[1].number_input("VU評価(万)", value=get_val("VU評価賃料", divide=10000), step=0.1)
        r_mai = r_cols[0].number_input("マイソク(万)", value=get_val("マイソク賃料", divide=10000), step=0.1)
        r_ram = r_cols[1].number_input("RAM募集(万)", value=get_val("RAM募集賃料", divide=10000), step=0.1)

        # 計算
        mng_rep_total = m_fee + r_fee
        price_base = get_sales_price(r_base, mng_rep_total, y_base)
        price_vu = get_sales_price(r_vu, mng_rep_total, y_vu)
        p_fees = r_base * 3 
        prof_a = price_base - p_price - p_fees
        prof_b = price_vu - price_base - c_cost
        total_p = prof_a + prof_b
        rate_a = (prof_a / price_base * 100) if price_base != 0 else 0
        total_r = (total_p / price_vu * 100) if price_vu != 0 else 0

        # 粗利分析（スマホでは縦に並ぶように）
        st.markdown('<div class="section-title">粗利分析</div>', unsafe_allow_html=True)
        s1, s2, s3 = st.columns([1, 1, 1])
        with s1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">仕入粗利</div><div class="metric-value">{prof_a:.1f}<span style="font-size:0.8rem">万</span></div><div class="rate-text">{rate_a:.2f}%</div></div>', unsafe_allow_html=True)
        with s2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">VU粗利</div><div class="metric-value">{prof_b:.1f}<span style="font-size:0.8rem">万</span></div><div class="rate-text" style="color:#64748b; font-size:0.7rem;">工事費込</div></div>', unsafe_allow_html=True)
        with s3:
            st.markdown(f'<div class="metric-card" style="border:2px solid #3b82f6; background-color:#f0f7ff;"><div class="metric-label" style="color:#3b82f6;">会社総粗利</div><div class="metric-value" style="color:#3b82f6;">{total_p:.1f}<span style="font-size:0.8rem">万</span></div><div class="rate-text" style="color:#3b82f6;">{total_r:.2f}%</div></div>', unsafe_allow_html=True)

        # 販売・CF詳細（2列構成）
        st.markdown('<div class="section-title">販売・CF詳細</div>', unsafe_allow_html=True)
        res_cols = st.columns(2)
        patterns = [("仕入れ時", r_base, price_base), ("VU評価時", r_vu, price_vu), ("マイソク", r_mai, price_vu), ("RAM募集", r_ram, price_vu)]
        for i, (name, rent, s_price) in enumerate(patterns):
            net_rent = (rent * 10000) - mng_rep_total
            pay = get_monthly_payment(s_price, l_year, l_rate)
            with res_cols[i % 2]:
                st.markdown(f'<div class="detail-card"><div style="font-size:0.75rem;color:#64748b;font-weight:bold;">{name}</div><div class="detail-item">販売: <span class="detail-val-text">{int(s_price):,}</span>万</div><div class="detail-item">CF: <span class="detail-val-text">{int(net_rent - pay):,}</span>円/月</div></div>', unsafe_allow_html=True)
else:
    st.info("👆 上の入力欄に物件IDを入れてください。")