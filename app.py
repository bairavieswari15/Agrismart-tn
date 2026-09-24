"""
AgriSmart TN — FastAPI Backend
Exposes REST API endpoints consumed by the Streamlit frontend.
Run with: uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import os

from backend.data import TN_DISTRICTS, CROP_DB, CROP_EXCLUSION, HISTORICAL_YIELD, HIST_YEARS
from backend.services import (
    calc_profit, fmt_inr,
    get_live_weather, weather_desc,
    get_ai_response, get_ai_conclusion,
    get_ai_market_report, get_ai_crop_calendar,
    get_soil_info, get_irrigation_info,
    crop_suitability, build_ml_dataset,
    diagnose_pest_disease, generate_farm_pdf_report,
    match_government_schemes, get_crop_timeline,
    calc_mandi_transport_profit, get_district_weather_risk,
    calc_equipment_labor_cost, calc_seed_requirement, calc_crop_plan, rank_crops,
    calc_solar_pump_roi, predict_crop_yield_ml
)

app = FastAPI(
    title="AgriSmart TN API",
    description="Backend REST API for AgriSmart Tamil Nadu Smart Crop Advisor",
    version="1.0.0"
)

# Allow Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC MODELS (Request Bodies)
# ─────────────────────────────────────────────────────────────────────────────

class ProfitRequest(BaseModel):
    crop: str
    land_ha: float
    factor: float = 1.0

class AIAdvisorRequest(BaseModel):
    messages: List[dict]
    district: str
    land_ha: float
    farmer_name: str
    api_key: str = ""
    selected_crop: Optional[str] = None
    profile: Optional[dict] = None

class SeedPlannerRequest(BaseModel):
    crop: str
    acres: Optional[float] = None
    land_acres: Optional[float] = None

class CropPlanRequest(BaseModel):
    crop: str
    acres: Optional[float] = None
    land_acres: Optional[float] = None
    district: Optional[str] = "Thoothukudi"
    yield_factor: Optional[float] = 1.0

class SmartCropsRequest(BaseModel):
    district: str
    acres: Optional[float] = None
    land_acres: Optional[float] = None
    soil_type: Optional[str] = ""
    irrigation: Optional[str] = ""
    season: Optional[str] = "All"
    min_profit: Optional[float] = 0.0

class FarmerProfile(BaseModel):
    farmer_name: Optional[str] = "Farmer"
    name: Optional[str] = "Farmer"
    phone_email: Optional[str] = ""
    phone: Optional[str] = ""
    district: str = "Thoothukudi"
    land_acres: float = 1.0
    village: Optional[str] = ""
    soil_type: Optional[str] = ""
    irrigation: Optional[str] = ""
    current_crop: Optional[str] = None
    experience_years: Optional[int] = 0

class LoginRequest(BaseModel):
    phone_or_email: Optional[str] = ""
    phone: Optional[str] = ""

class AIConclusionRequest(BaseModel):
    district: str
    land_ha: float
    farmer_name: str
    crop: str
    api_key: str =""

class AIMarketRequest(BaseModel):
    district: str
    crop: str
    api_key: str =""

class AICropCalendarRequest(BaseModel):
    district: str
    crop: str
    api_key: str =""

class SoilRequest(BaseModel):
    district: str
    crop: str

class IrrigationRequest(BaseModel):
    district: str
    land_ha: float
    crop: str

class SuitabilityRequest(BaseModel):
    district: str

class PestScannerRequest(BaseModel):
    crop: str
    symptom: Optional[str] =""
    image_b64: Optional[str] =""
    api_key: Optional[str] =""

class PDFReportRequest(BaseModel):
    district: str
    farmer_name: str
    land_ha: float
    crop: str

class SchemeMatchRequest(BaseModel):
    farmer_type: Optional[str] ="Small/Marginal (<2 ha)"
    land_ha: Optional[float] = 1.0
    category: Optional[str] ="All"

class TimelineRequest(BaseModel):
    crop: str
    district: str

class MandiCompareRequest(BaseModel):
    crop: str
    district: str
    land_ha: float

class EquipmentCalcRequest(BaseModel):
    crop: str
    land_ha: float

class SolarPumpRequest(BaseModel):
    land_ha: float
    current_source: Optional[str] = "Diesel"
    well_depth_ft: Optional[int] = 150

class YieldPredictRequest(BaseModel):
    crop: str
    rainfall_mm: float
    avg_temp: float
    soil_ph: float
    nitrogen: Optional[float] = 80.0
    phosphorus: Optional[float] = 40.0
    potassium: Optional[float] = 40.0

class SensorTelemetryRequest(BaseModel):
    device_id: Optional[str] = "ESP32-FARM-01"
    district: Optional[str] = "Coimbatore"
    moisture: float
    temperature: float
    humidity: float



# ─────────────────────────────────────────────────────────────────────────────
# DISTRICT ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/districts", summary="Get all Tamil Nadu districts")
def get_districts():
    """Return list of all 38 TN districts with their agricultural profiles."""
    return {
        "districts": list(TN_DISTRICTS.keys()),
        "total": len(TN_DISTRICTS),
        "data": TN_DISTRICTS
    }


@app.get("/api/districts/{name}", summary="Get a specific district profile")
def get_district(name: str):
    """Return detailed profile for a single district."""
    if name not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{name}'not found.")
    return {"district": name,"data": TN_DISTRICTS[name]}


# ─────────────────────────────────────────────────────────────────────────────
# CROP ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/crops", summary="Get all crops in the database")
def get_crops():
    """Return the full crop database."""
    return {
        "crops": list(CROP_DB.keys()),
        "total": len(CROP_DB),
        "data": CROP_DB
    }


@app.get("/api/crops/{name}", summary="Get a specific crop profile")
def get_crop(name: str):
    """Return detailed profile for a single crop."""
    if name not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{name}'not found.")
    return {"crop": name,"data": CROP_DB[name]}


@app.get("/api/historical-yield", summary="Get historical yield records")
def get_historical_yield():
    """Return historical yield data and years for charting."""
    return {"years": HIST_YEARS,"data": HISTORICAL_YIELD}


# ─────────────────────────────────────────────────────────────────────────────
# WEATHER ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/weather/{district_name}", summary="Get live weather for a district")
def get_weather(district_name: str):
    """Fetch live weather data from Open-Meteo for the given district."""
    if district_name not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{district_name}'not found.")
    dd = TN_DISTRICTS[district_name]
    weather = get_live_weather(dd["lat"], dd["lon"], district_name)
    return {
        "district": district_name,
        "static": dd,
        "live": weather,
        "available": weather is not None
    }


@app.get("/api/weather-desc/{code}", summary="Decode WMO weather code")
def get_weather_desc(code: int):
    return {"code": code,"description": weather_desc(code)}


# ─────────────────────────────────────────────────────────────────────────────
# PROFIT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/profit", summary="Calculate profit, ROI, and break-even")
def calculate_profit(req: ProfitRequest):
    """Calculate detailed profit analysis for a crop on a given land area."""
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    if req.land_ha <= 0:
        raise HTTPException(status_code=400, detail="land_ha must be greater than 0.")
    result = calc_profit(req.crop, req.land_ha, req.factor)
    result["revenue_fmt"] = fmt_inr(result["revenue"])
    result["cost_fmt"] = fmt_inr(result["cost"])
    result["profit_fmt"] = fmt_inr(result["profit"])
    result["crop"] = req.crop
    result["land_ha"] = req.land_ha
    result["price_per_tonne"] = CROP_DB[req.crop]["price"]
    return result


# ─────────────────────────────────────────────────────────────────────────────
# AI ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/ai/advisor", summary="Chat with the AI crop advisor")
def ai_advisor(req: AIAdvisorRequest):
    """Get an AI response for a farmer's query."""
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{req.district}'not found.")
    dd = TN_DISTRICTS[req.district]
    reply = get_ai_response(
        req.messages, req.district, dd, req.land_ha,
        req.farmer_name, req.api_key, req.selected_crop
    )
    return {"reply": reply,"district": req.district}


@app.post("/api/ai/conclusion", summary="Generate a full farm conclusion report")
def ai_conclusion(req: AIConclusionRequest):
    """Generate a comprehensive farm conclusion report for a selected crop."""
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{req.district}'not found.")
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    dd = TN_DISTRICTS[req.district]
    report = get_ai_conclusion(req.district, dd, req.land_ha, req.farmer_name, req.crop, req.api_key)
    return {"report": report,"district": req.district,"crop": req.crop}


@app.post("/api/ai/market", summary="Generate a market and selling report")
def ai_market(req: AIMarketRequest):
    """Generate a market price and selling strategy report for a crop."""
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{req.district}'not found.")
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    dd = TN_DISTRICTS[req.district]
    report = get_ai_market_report(req.district, dd, req.crop, req.api_key)
    return {"report": report,"district": req.district,"crop": req.crop}


@app.post("/api/ai/crop-calendar", summary="Generate a month-by-month crop calendar")
def ai_crop_calendar(req: AICropCalendarRequest):
    """Generate a detailed crop calendar for the given crop and district."""
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{req.district}'not found.")
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    dd = TN_DISTRICTS[req.district]
    calendar = get_ai_crop_calendar(req.district, dd, req.crop, req.api_key)
    return {"calendar": calendar,"district": req.district,"crop": req.crop}


# ─────────────────────────────────────────────────────────────────────────────
# SOIL & IRRIGATION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/soil", summary="Get soil and fertilizer information")
def get_soil(req: SoilRequest):
    """Return detailed soil profile and NPK fertilizer recommendations."""
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{req.district}'not found.")
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    dd = TN_DISTRICTS[req.district]
    return {"district": req.district,"crop": req.crop,"data": get_soil_info(dd, req.crop)}


@app.post("/api/irrigation", summary="Get irrigation plan for a crop")
def get_irrigation(req: IrrigationRequest):
    """Return detailed irrigation schedule, method, costs and schemes."""
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{req.district}'not found.")
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    dd = TN_DISTRICTS[req.district]
    return {"district": req.district,"crop": req.crop,"data": get_irrigation_info(dd, req.land_ha, req.crop)}


# ─────────────────────────────────────────────────────────────────────────────
# ML / ANALYTICS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/ml/suitability", summary="Get crop suitability scores for a district")
def get_suitability(req: SuitabilityRequest):
    """Return crop suitability scores (0–100) for all crops in a district."""
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{req.district}'not found.")
    dd = TN_DISTRICTS[req.district]
    rain = dd["rainfall_mm"]
    temp = dd["avg_temp"]
    ph = dd["soil_ph"]
    hum = dd["humidity"]

    scores = []
    for crop in CROP_DB:
        score = crop_suitability(crop, rain, temp, ph, hum)
        profit_data = calc_profit(crop, 1.0)
        scores.append({
            "crop": crop,
            "emoji": CROP_DB[crop]["emoji"],
            "suitability_score": score,
            "profit_per_ha": profit_data["profit"],
            "roi": profit_data["roi"],
            "water_need": CROP_DB[crop]["water"],
            "season": CROP_DB[crop]["season"],
        })
    scores.sort(key=lambda x: x["suitability_score"], reverse=True)
    return {"district": req.district,"scores": scores}


@app.get("/api/ml/dataset", summary="Get the full ML training dataset")
def get_ml_dataset(as_records: bool = Query(default=True)):
    """Generate and return the synthetic ML training dataset."""
    df = build_ml_dataset()
    if as_records:
        return {"records": df.to_dict(orient="records"),"shape": list(df.shape)}
    return {"columns": df.columns.tolist(),"shape": list(df.shape)}


@app.get("/api/district-compare", summary="Compare two districts")
def compare_districts(district1: str = Query(...), district2: str = Query(...)):
    """Compare agricultural profiles of two Tamil Nadu districts."""
    for d in [district1, district2]:
        if d not in TN_DISTRICTS:
            raise HTTPException(status_code=404, detail=f"District'{d}'not found.")
    return {
        "district1": {"name": district1,"data": TN_DISTRICTS[district1]},
        "district2": {"name": district2,"data": TN_DISTRICTS[district2]},
    }


@app.get("/api/top-crops", summary="Get top crops for a district by profit")
def top_crops(district: str = Query(...), top_n: int = Query(default=5)):
    """Return top N crops ranked by profit for a given district."""
    if district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{district}'not found.")
    dd = TN_DISTRICTS[district]
    results = []
    for crop in dd["main_crops"]:
        if crop in CROP_DB:
            p = calc_profit(crop, 1.0)
            results.append({
                "crop": crop,
                "emoji": CROP_DB[crop]["emoji"],
                "profit_per_ha": p["profit"],
                "revenue_per_ha": p["revenue"],
                "roi": p["roi"],
                "break_even": p["break_even"],
                "water_need": CROP_DB[crop]["water"],
                "season": CROP_DB[crop]["season"],
            })
    results.sort(key=lambda x: x["profit_per_ha"], reverse=True)
    return {"district": district,"top_crops": results[:top_n]}


# ─────────────────────────────────────────────────────────────────────────────
# 8 NEW MODULE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/pest-scanner", summary="Diagnose crop pest or disease")
def api_pest_scanner(req: PestScannerRequest):
    """Diagnose pest/disease based on crop, symptom description, or leaf photo."""
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    res = diagnose_pest_disease(req.crop, req.symptom or"", req.image_b64 or"", req.api_key or"")
    return {"status":"success","data": res}


@app.post("/api/pdf/farm-report", summary="Generate downloadable PDF farm advisory report")
def api_pdf_report(req: PDFReportRequest):
    """Generate downloadable formal PDF report for bank loan applications."""
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{req.district}'not found.")
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    dd = TN_DISTRICTS[req.district]
    pdf_bytes = generate_farm_pdf_report(req.district, dd, req.farmer_name, req.land_ha, req.crop)
    filename = f"AgriSmart_Farm_Report_{req.district}_{req.crop}.pdf"
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


@app.post("/api/schemes/match", summary="Get matching government schemes")
def api_scheme_match(req: SchemeMatchRequest):
    """Find matching central and Tamil Nadu agricultural schemes."""
    schemes = match_government_schemes(req.farmer_type or"Small/Marginal (<2 ha)", req.land_ha or 1.0, req.category or"All")
    return {"status":"success","total": len(schemes),"schemes": schemes}


@app.post("/api/crop-timeline", summary="Get crop lifecycle Gantt timeline")
def api_crop_timeline(req: TimelineRequest):
    """Generate structured crop timeline stages for Gantt chart visualizer."""
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    stages = get_crop_timeline(req.crop, req.district)
    return {"status":"success","crop": req.crop,"stages": stages}


@app.post("/api/mandi-compare", summary="Compare net profit across major TN Mandis")
def api_mandi_compare(req: MandiCompareRequest):
    """Compare market prices & transport costs across major TN Mandis."""
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{req.district}'not found.")
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    mandis = calc_mandi_transport_profit(req.crop, req.district, req.land_ha)
    return {"status":"success","district": req.district,"crop": req.crop,"mandis": mandis}


@app.get("/api/weather-risk/{district}", summary="Get district extreme weather risk assessment")
def api_weather_risk(district: str):
    """Get climate risk scoring (cyclone, flood, drought, heat) for a district."""
    if district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District'{district}'not found.")
    risk_data = get_district_weather_risk(district)
    return {"status":"success","risk": risk_data}


@app.post("/api/equipment-calculator", summary="Calculate equipment rental & labor requirements")
def api_equipment_calc(req: EquipmentCalcRequest):
    """Calculate tractor, harvester, drone spraying, and labor requirements."""
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop'{req.crop}'not found.")
    calc_res = calc_equipment_labor_cost(req.crop, req.land_ha)
    return {"status":"success","data": calc_res}


@app.post("/api/solar-pump", summary="Calculate Solar Pump & PM-KUSUM Subsidy ROI")
def api_solar_pump(req: SolarPumpRequest):
    """Calculate solar pump size, PM-KUSUM subsidy, savings and payback period."""
    if req.land_ha <= 0:
        raise HTTPException(status_code=400, detail="land_ha must be greater than 0.")
    res = calc_solar_pump_roi(req.land_ha, req.current_source or "Diesel", req.well_depth_ft or 150)
    return {"status": "success", "data": res}


@app.post("/api/ml/predict-yield", summary="Predict crop yield using scikit-learn Machine Learning")
def api_ml_predict_yield(req: YieldPredictRequest):
    """Predict yield per hectare/acre using trained Random Forest ML model."""
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop '{req.crop}' not found.")
    res = predict_crop_yield_ml(
        req.crop, req.rainfall_mm, req.avg_temp, req.soil_ph,
        req.nitrogen or 80.0, req.phosphorus or 40.0, req.potassium or 40.0
    )
    return {"status": "success", "data": res}


# ─────────────────────────────────────────────────────────────────────────────
# PRECISION PLANNING & PROFILE ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

PROFILE_FILE = "backend/profiles.json"

@app.post("/api/profile/save", summary="Create or update a farmer profile")
def api_profile_save(profile: FarmerProfile):
    profiles = {}
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            try:
                profiles = json.load(f)
            except:
                pass
    key = profile.phone_email or profile.phone or "default"
    p_dict = profile.dict()
    profiles[key] = p_dict
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4)
    return {"status": "success", "message": "Profile saved", "profile": p_dict}

@app.post("/api/profile/login", summary="Login to existing profile")
def api_profile_login(req: LoginRequest):
    key = req.phone_or_email or req.phone or ""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            try:
                profiles = json.load(f)
                if key in profiles:
                    return {"status": "success", "profile": profiles[key]}
            except:
                pass
    raise HTTPException(status_code=404, detail="Profile not found. Please register.")

@app.post("/api/seed-planner", summary="Calculate seed requirement and plant population")
def api_seed_planner(req: SeedPlannerRequest):
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop '{req.crop}' not found.")
    acres = req.land_acres or req.acres or 1.0
    res = calc_seed_requirement(req.crop, acres)
    return {"status": "success", "seed_plan": res, "data": res}

@app.post("/api/crop-plan", summary="Generate a comprehensive cultivation plan")
def api_crop_plan(req: CropPlanRequest):
    if req.crop not in CROP_DB:
        raise HTTPException(status_code=404, detail=f"Crop '{req.crop}' not found.")
    acres = req.land_acres or req.acres or 1.0
    res = calc_crop_plan(req.crop, acres, req.district, req.yield_factor)
    return {"status": "success", "plan": res, "data": res}

@app.post("/api/smart-crops", summary="Rank suitable crops based on farm profile")
def api_smart_crops(req: SmartCropsRequest):
    if req.district not in TN_DISTRICTS:
        raise HTTPException(status_code=404, detail=f"District '{req.district}' not found.")
    acres = req.land_acres or req.acres or 1.0
    res = rank_crops(req.district, acres, req.soil_type, req.irrigation, req.season, req.min_profit)
    return {"status": "success", "recommended_crops": res, "data": res}


# ─────────────────────────────────────────────────────────────────────────────
# IOT SENSOR HARDWARE INTEGRATION ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/sensor/telemetry", summary="Receive IoT hardware telemetry reading")
def api_sensor_telemetry(req: SensorTelemetryRequest):
    import datetime, uuid
    from db_store import save_sensor_log

    alert_level = "NORMAL"
    status_msg = "Optimal crop growth conditions."

    if req.moisture < 30.0:
        alert_level = "LOW_MOISTURE"
        status_msg = f"ALERT: Soil moisture critically low ({req.moisture:.1f}% < 30%). Immediate irrigation needed!"
    elif req.temperature > 35.0 or req.humidity < 40.0:
        alert_level = "HIGH_TEMP"
        status_msg = f"ALERT: Heat stress condition detected (Temp: {req.temperature:.1f}°C, Humid: {req.humidity:.1f}%)."

    log_entry = {
        "id": f"SNS-{uuid.uuid4().hex[:6].upper()}",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device_id": req.device_id or "ESP32-FARM-01",
        "district": req.district or "Coimbatore",
        "moisture": round(req.moisture, 1),
        "temperature": round(req.temperature, 1),
        "humidity": round(req.humidity, 1),
        "alert_level": alert_level,
        "status_msg": status_msg
    }

    save_sensor_log(log_entry)
    return {
        "status": "success",
        "message": "Telemetry received and logged",
        "telemetry": log_entry
    }


@app.get("/api/sensor/history", summary="Get IoT sensor reading history")
def api_sensor_history():
    from db_store import load_sensor_logs
    logs = load_sensor_logs()
    return {"status": "success", "count": len(logs), "logs": logs}


@app.get("/api/sensor-data", summary="Get latest live IoT sensor data")
def get_sensor_data():
    import datetime
    from db_store import load_sensor_logs
    logs = load_sensor_logs()
    if logs:
        latest = logs[0]
        return {
            "soil_moisture": float(latest.get("moisture", 68.0)),
            "humidity": float(latest.get("humidity", 72.0)),
            "temperature": float(latest.get("temperature", 29.0)),
            "device_status": "connected",
            "timestamp": latest.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
            "device_id": latest.get("device_id", "FARM-001")
        }
    return {
        "soil_moisture": 68.0,
        "humidity": 72.0,
        "temperature": 29.0,
        "device_status": "connected",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "device_id": "FARM-001"
    }



# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────



@app.get("/", summary="Health check")
def root():
    return {
        "status":"AgriSmart TN Backend is running",
        "version":"1.0.0",
        "districts": len(TN_DISTRICTS),
        "crops": len(CROP_DB),
        "docs":"/docs"
    }

@app.get("/api/health")
def health():
    return {"status":"ok","service":"AgriSmart TN Backend"}
