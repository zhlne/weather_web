import os
import joblib
import pandas as pd
import requests
from flask import Flask, render_template, request
from datetime import datetime
from dotenv import load_dotenv
from suggestions import get_suggestions
import urllib3

# 關閉 SSL 安全警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

app = Flask(__name__)

# API 設定
API_KEY = os.getenv("CWA_API_KEY")
TOWN_FORECAST_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-093"
OBSERVATION_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"

# 縣市代碼對照表
COUNTY_LOCATION_IDS = {
    "新北市": "F-D0047-069",
    "臺北市": "F-D0047-061",
    "桃園市": "F-D0047-005",
    "臺中市": "F-D0047-073",
}

# 測站 ID 對照表 (用於 AI 預測模型)
COUNTY_STATION_IDS = {
    "新北市": "466881",
    "臺北市": "466920",
    "桃園市": "467050",
    "臺中市": "467490"
}

# 載入預測模型
try:
    saved_data = joblib.load("weather_model.pkl")
    predictor = saved_data["model"]
    feature_cols = saved_data["common_cols"]
except:
    predictor = None

def get_ai_prediction(county):
    """抓取即時數據並預測下一小時氣溫"""
    if not predictor or county not in COUNTY_STATION_IDS:
        return None
    try:
        station_id = COUNTY_STATION_IDS[county]
        # 修正點 1：加上 verify=False
        resp = requests.get(OBSERVATION_URL, params={"Authorization": API_KEY, "StationId": station_id}, verify=False)
        obs = resp.json()["records"]["Station"][0]
        we = obs["WeatherElement"]
        
        features = pd.DataFrame([{
            "AirPressure": float(we["AirPressure"]),
            "AirTemperature": float(we["AirTemperature"]),
            "RelativeHumidity": float(we["RelativeHumidity"]),
            "WindSpeed": float(we["WindSpeed"]),
            "Precipitation": float(we["Now"]["Precipitation"])
        }])[feature_cols]
        
        pred = predictor.predict(features)[0]
        return round(pred, 1)
    except:
        return None

@app.route("/", methods=["GET"])
def index():
    county = request.args.get("county")
    data = None

    if county:
        try:
            location_id = COUNTY_LOCATION_IDS[county]
            # 修正點 2：加上 verify=False
            resp = requests.get(TOWN_FORECAST_URL, params={
                "Authorization": API_KEY, "format": "JSON", "locationId": location_id
            }, verify=False)
            weather_json = resp.json()

            records = weather_json.get('records', {})
            locations_block = records.get('Locations') or records.get('locations')
            if not locations_block:
                return f"❌ 無法取得 {county} 的資料塊"
                
            location_list = locations_block[0].get('Location') or locations_block[0].get('location')
            if not location_list:
                return f"❌ 找不到 {county} 的鄉鎮資訊"
            
            location_info = location_list[0]

            elements = {}
            for elem in location_info.get('WeatherElement', []):
                name = elem['ElementName']
                if name in ("溫度", "3小時降雨機率", "6小時降雨機率", "12小時降雨機率", "相對濕度"):
                    times = []
                    for t in elem['Time'][:6]:
                        dt_raw = t.get('DataTime') or t.get('StartTime')
                        raw_val = list(t['ElementValue'][0].values())[0]
                        try:
                            val = float(raw_val) if raw_val and raw_val != "-" else 0.0
                        except ValueError:
                            val = 0.0
                        times.append({"time": dt_raw, "value": val})
                    
                    if "降雨機率" in name:
                        elements["降雨機率"] = times
                    else:
                        elements[name] = times

            temps = [e["value"] for e in elements.get("溫度", [])]
            pops  = [e["value"] for e in elements.get("降雨機率", [])]
            hums  = [e["value"] for e in elements.get("相對濕度", [])]
            
            data = {
                "locationName": location_info['LocationName'],
                "elements": elements,
                "suggestions": get_suggestions(temps, pops, hums),
                "ai_temp": get_ai_prediction(county)
            }
        except Exception as e:
            return f"❌ 系統錯誤：{str(e)}"

    return render_template("index.html", counties=COUNTY_LOCATION_IDS, selected_county=county, weather=data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)