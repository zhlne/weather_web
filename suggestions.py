# suggestions.py

def get_suggestions(temps, pops, hums):
    """
    根據溫度 (temps)、降雨機率 (pops)、相對濕度 (hums) 回傳建議清單
    - temps: list[int] 溫度 (°C)
    - pops:  list[int] 降雨機率 (%)
    - hums:  list[int] 相對濕度 (%)
    """
    suggestions = []

    # 高溫／低溫建議
    if temps:
        mx = max(temps)
        mn = min(temps)
        if mx >= 35:
            suggestions.append("今天炎熱，請加強防曬並多補充水分。")
        elif mx >= 30:
            suggestions.append("天氣偏熱，外出注意多喝水。")
        if mn < 22:
            suggestions.append("清晨／夜晚較涼，出門記得帶件薄外套。")

    # 降雨建議
    if pops:
        mxp = max(pops)
        if mxp >= 70:
            suggestions.append("降雨機率高，出門請攜帶雨具並注意路滑。")
        elif mxp >= 40:
            suggestions.append("有機會陣雨，外出建議帶把傘。")

    # 濕度建議
    if hums:
        mxh = max(hums)
        if mxh >= 85:
            suggestions.append("濕度高，悶熱不適，建議開啟空調或除濕。")
        elif mxh <= 50:
            suggestions.append("空氣較乾燥，建議多喝水並注意保濕。")

    return suggestions

