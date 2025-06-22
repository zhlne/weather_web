import os
from dotenv import load_dotenv
from flask import Flask, render_template, request
import requests
from datetime import datetime
from suggestions import get_suggestions

# 載入 .env 檔案
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("CWA_API_KEY")
TOWN_FORECAST_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-093"

COUNTY_LOCATION_IDS = {
    "新北市": "F-D0047-069",
    "臺北市": "F-D0047-061",
    "桃園市": "F-D0047-005",
    "臺中市": "F-D0047-073",
    "高雄市": "F-D0047-065"
}

@app.route("/", methods=["GET"])
def index():
    county = request.args.get("county")
    data = None

    if county:
        try:
            location_id = COUNTY_LOCATION_IDS[county]
            resp = requests.get(TOWN_FORECAST_URL, params={
                "Authorization": API_KEY,
                "format": "JSON",
                "locationId": location_id
            })
            weather_data = resp.json()
            print("=== API 回傳資料 ===")
            print(weather_data)

            all_locations = weather_data['records']['Locations'][0]['Location']
            location_info = all_locations[0] if all_locations else None

            if not location_info:
                return f"❌ 找不到 {county} 對應的鄉鎮天氣資料"

            elements = {}
            for elem in location_info['WeatherElement']:
                name = elem['ElementName']
                if name not in ("溫度", "3小時降雨機率", "相對濕度"):
                    continue
                times = []
                for t in elem['Time'][:6]:
                    dt_raw = t.get('DataTime') or t.get('StartTime')
                    if not dt_raw or not t['ElementValue']:
                        continue
                    try:
                        dt_fmt = datetime.strptime(dt_raw, "%Y-%m-%dT%H:%M:%S%z")
                        formatted = dt_fmt.strftime("%m-%d %H:%M")
                    except:
                        formatted = dt_raw
                    value = list(t['ElementValue'][0].values())[0]
                    times.append({"time": formatted, "value": value})
                elements[name] = times

            temps = [int(e["value"]) for e in elements.get("溫度", [])]
            pops  = [int(e["value"]) for e in elements.get("3小時降雨機率", [])]
            hums  = [int(e["value"]) for e in elements.get("相對濕度", [])]
            suggestions = get_suggestions(temps, pops, hums)

            data = {
                "locationName": location_info['LocationName'],
                "elements": elements,
                "suggestions": suggestions
            }

        except Exception as e:
            return f"❌ 錯誤發生：{e}"

    return render_template(
        "index.html",
        counties=COUNTY_LOCATION_IDS,
        selected_county=county,
        weather=data
    )

if __name__ == "__main__":
    print("Flask App 啟動中...")
    app.run(debug=True)



