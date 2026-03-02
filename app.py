def fetch_kintone_data(ts_id):
    clean_id = unicodedata.normalize('NFKC', str(ts_id)).strip()
    url = f"https://{KINTONE_SUBDOMAIN}.cybozu.com/k/v1/records.json"
    headers = {"X-Cybozu-API-Token": KINTONE_API_TOKEN}
    
    # --- クエリの強化 ---
    # 1. IDが一致する
    # 2. かつ「VU可否」が「重複」ではないレコードを指定
    query = f'(TS_ID = "{clean_id}"'
    if clean_id.isdigit():
        query += f' or TS_ID = {clean_id}'
    query += ') and VU可否 != "重複"'
    
    # 安全のため、最新のID順に並べて1件取得する
    params = {
        "app": KINTONE_APP_ID, 
        "query": f'{query} order by $id desc limit 1'
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params)
        data = resp.json()
        return data["records"][0] if data.get("records") else None
    except:
        return None