import joblib

# 假設您的模型變數名稱為 model，欄位清單為 common_cols
# 這些變數來自於 weather_temp_predictor.ipynb
model_data = {
    "model": model, 
    "common_cols": ["AirPressure", "AirTemperature", "RelativeHumidity", "WindSpeed", "Precipitation"]
}

joblib.dump(model_data, "weather_model.pkl")
print("模型已成功匯出為 weather_model.pkl")