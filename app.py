import os
import joblib
import pandas as pd
import requests
from flask import Flask, render_template, request
from datetime import datetime
from dotenv import load_dotenv
from suggestions import get_suggestions #

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
    "高雄市": "F-D0047-065"
}

# 測站 ID 對照表 (用於 AI 預測模型)
COUNTY_STATION_IDS = {
    "新北市": "466881",
    "臺北市": "466920",
    "桃園市": "467050",
    "臺中市": "467490",
    "高雄市": "467440"
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
        resp = requests.get(OBSERVATION_URL, params={"Authorization": API_KEY, "StationId": station_id})
        obs = resp.json()["records"]["Station"][0]
        we = obs["WeatherElement"]
        
        # 建立特徵 DataFrame
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
            # 1. 抓取預報資料
            location_id = COUNTY_LOCATION_IDS[county]
            resp = requests.get(TOWN_FORECAST_URL, params={
                "Authorization": API_KEY, "format": "JSON", "locationId": location_id
            })
            weather_json = resp.json()
            location_info = weather_json['records']['Locations'][0]['Location'][0]

            elements = {}
            for elem in location_info['WeatherElement']:
                name = elem['ElementName']
                if name in ("溫度", "3小時降雨機率", "相對濕度"):
                    times = []
                    for t in elem['Time'][:6]:
                        dt_raw = t.get('DataTime') or t.get('StartTime')
                        val = list(t['ElementValue'][0].values())[0]
                        times.append({"time": dt_raw, "value": val})
                    elements[name] = times

            # 2. 取得建議與預測
            temps = [int(e["value"]) for e in elements.get("溫度", [])]
            pops  = [int(e["value"]) for e in elements.get("3小時降雨機率", [])]
            hums  = [int(e["value"]) for e in elements.get("相對濕度", [])]
            
            data = {
                "locationName": location_info['LocationName'],
                "elements": elements,
                "suggestions": get_suggestions(temps, pops, hums), #
                "ai_temp": get_ai_prediction(county) #
            }
        except Exception as e:
            return f"Error: {e}"

    return render_template("index.html", counties=COUNTY_LOCATION_IDS, selected_county=county, weather=data)

if __name__ == "__main__":
    app.run(debug=True)