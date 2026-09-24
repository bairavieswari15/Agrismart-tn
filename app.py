import sys
import os
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

"""
AgriSmart TN — Modern Agritech Platform (Standalone Version)
Runs directly on Streamlit Cloud without external FastAPI backend server.
"""

import streamlit as st
import datetime
import random
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import urllib.parse
import re


# ── File-based persistence (no external DB needed) ──
try:
    from db_store import (
        load_users, save_user, get_user, user_exists,
        load_listings, save_listing, save_all_listings,
        load_demands, save_demand, save_all_demands,
        load_orders, save_order, save_all_orders, update_order_status,
        load_vehicles, save_vehicle, load_sensor_logs, save_sensor_log
    )
except Exception:
    # Fallback stubs with initial seed data
    def load_users(): return {}
    def save_user(p): pass
    def get_user(k): return None
    def user_exists(k): return False
    def load_listings(): return INITIAL_SUPPLY_LISTINGS
    def save_listing(l): pass
    def save_all_listings(l): pass
    def load_demands(): return INITIAL_BUYER_DEMANDS
    def save_demand(d): pass
    def save_all_demands(d): pass
    def load_orders(): return []
    def save_order(o): pass
    def save_all_orders(o): pass
    def update_order_status(oid, st, ex=None): return True
    def load_vehicles(): return INITIAL_DRIVER_VEHICLES
    def save_vehicle(v): pass
    def load_sensor_logs(): return []
    def save_sensor_log(l): pass


try:
    from utils.theme import apply_custom_theme
    from utils.translations import t, crop_t, TRANSLATIONS
except ImportError:
    from theme import apply_custom_theme
    from translations import t, crop_t, TRANSLATIONS

try:
    from backend.data import (
        TN_DISTRICTS, CROP_DB, CROP_EXCLUSION, HISTORICAL_YIELD, HIST_YEARS,
        CROP_SHELF_LIFE, INITIAL_SUPPLY_LISTINGS, INITIAL_BUYER_DEMANDS, INITIAL_DRIVER_VEHICLES
    )
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
        calc_solar_pump_roi, predict_crop_yield_ml,
        calc_haversine_dist, calc_freshness_decay, parse_buyer_demand_nlp,
        rank_supply_demand_matches, pool_supply_orders, calc_farmer_credit_score,
        optimize_delivery_route
    )
except ImportError:
    from data import (
        TN_DISTRICTS, CROP_DB, CROP_EXCLUSION, HISTORICAL_YIELD, HIST_YEARS,
        CROP_SHELF_LIFE, INITIAL_SUPPLY_LISTINGS, INITIAL_BUYER_DEMANDS, INITIAL_DRIVER_VEHICLES
    )
    from services import (
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
        calc_solar_pump_roi, predict_crop_yield_ml,
        calc_haversine_dist, calc_freshness_decay, parse_buyer_demand_nlp,
        rank_supply_demand_matches, pool_supply_orders, calc_farmer_credit_score,
        optimize_delivery_route
    )


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG & THEME SETUP
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AgriSmart TN — Modern Agritech Platform",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global custom agritech theme
apply_custom_theme()

# ── WhatsApp & Cold-Chain Logistics Helper Utilities ──

def make_whatsapp_url(phone: str, message: str) -> str:
    """Generate a clean WhatsApp web/app click-to-chat URL."""
    clean_p = re.sub(r'\D', '', str(phone or '').strip())
    if not clean_p:
        # No valid phone number provided; return empty string to indicate unavailable
        return ""
    if len(clean_p) == 10:
        clean_p = "91" + clean_p
    # If length >10, assume it already includes country code
    quoted_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_p}?text={quoted_msg}"

def allocate_vehicle_for_order(district: str) -> dict:
    """Find or allocate a cold-chain driver vehicle from the available vehicle pool."""
    vehicles = st.session_state.get("driver_vehicles", []) or INITIAL_DRIVER_VEHICLES
    matching = [v for v in vehicles if v.get("district") == district]
    veh = matching[0] if matching else (vehicles[0] if vehicles else {})
    return {
        "vehicle_reg": veh.get("vehicle_reg", "TN 67 AD 4521"),
        "driver_name": veh.get("driver_name", "Sundaram T."),
        "driver_phone": veh.get("driver_phone", "9840077665"),
        "target_temp_c": veh.get("target_temp_c", 4.0),
        "status": "ALLOTTED & EN ROUTE"
    }

def is_buyer_user() -> bool:
    role = str(st.session_state.get("user_role", ""))
    prof_r = str(st.session_state.get("profile", {}).get("role", "")) if st.session_state.get("profile") else ""
    return "Buyer" in role or "Buyer" in prof_r

def is_seller_user() -> bool:
    role = str(st.session_state.get("user_role", ""))
    prof_r = str(st.session_state.get("profile", {}).get("role", "")) if st.session_state.get("profile") else ""
    return "Farmer" in role or "Seller" in role or "Farmer" in prof_r or "Seller" in prof_r or (not is_buyer_user() and "Driver" not in role and "Driver" not in prof_r)

# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE DATA HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def fetch_sensor_data():
    try:
        logs = load_sensor_logs()
        if logs:
            latest = logs[0]
            return {
                "soil_moisture": float(latest.get("moisture", 68.0)),
                "humidity": float(latest.get("humidity", 72.0)),
                "temperature": float(latest.get("temperature", 29.0)),
                "device_status": "connected",
                "timestamp": latest.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "device_id": latest.get("device_id", "FARM-001"),
                "logs": logs
            }
    except Exception:
        pass
    return {
        "soil_moisture": 68.0,
        "humidity": 72.0,
        "temperature": 29.0,
        "device_status": "connected",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device_id": "FARM-001",
        "logs": []
    }


@st.cache_data(ttl=3600)
def fetch_all_districts():

    return {
        "districts": list(TN_DISTRICTS.keys()),
        "total": len(TN_DISTRICTS),
        "data": TN_DISTRICTS
    }

@st.cache_data(ttl=3600)
def fetch_all_crops():
    return {
        "crops": list(CROP_DB.keys()),
        "total": len(CROP_DB),
        "data": CROP_DB
    }

@st.cache_data(ttl=3600)
def fetch_historical_yield():
    return {
        "years": HIST_YEARS,
        "data": HISTORICAL_YIELD
    }

def fetch_weather(district_name: str):
    if district_name not in TN_DISTRICTS:
        return None
    dd = TN_DISTRICTS[district_name]
    weather = get_live_weather(dd["lat"], dd["lon"], district_name)
    return {
        "district": district_name,
        "static": dd,
        "live": weather,
        "available": weather is not None
    }

def save_profile(profile_data: dict):
    if "saved_profiles" not in st.session_state:
        st.session_state["saved_profiles"] = {}
    key = profile_data.get("phone_email") or profile_data.get("phone") or "default"
    st.session_state["saved_profiles"][key] = profile_data
    return {"status": "success", "message": "Profile saved", "profile": profile_data}

def login_profile(phone_or_email: str):
    profiles = st.session_state.get("saved_profiles", {})
    if phone_or_email in profiles:
        return profiles[phone_or_email]
    return None

def fetch_smart_crops(district: str, land_acres: float, soil_type: str = "", irrigation: str = "", season: str = "All", min_profit: float = 0):
    if district not in TN_DISTRICTS:
        return []
    return rank_crops(district, land_acres, soil_type, irrigation, season, min_profit)

def fetch_seed_planner(crop: str, land_acres: float):
    if crop not in CROP_DB:
        return {}
    return calc_seed_requirement(crop, land_acres)

def fetch_crop_plan(crop: str, land_acres: float, yield_factor: float = 1.0):
    if crop not in CROP_DB:
        return {}
    return calc_crop_plan(crop, land_acres, district="Thoothukudi", yield_factor=yield_factor)

def fetch_profit(crop: str, land_ha: float, factor: float = 1.0):
    if crop not in CROP_DB:
        return None
    return calc_profit(crop, land_ha, factor)

def fetch_ai_advisor(messages: list, district: str, land_ha: float,
                     farmer_name: str, api_key: str = "", selected_crop: str = None, profile: dict = None) -> str:
    dd = TN_DISTRICTS.get(district, TN_DISTRICTS.get("Thoothukudi", {}))
    return get_ai_response(messages, district, dd, land_ha, farmer_name, api_key, selected_crop, profile)

def fetch_ai_conclusion(district: str, land_ha: float, farmer_name: str, crop: str, api_key: str = "") -> str:
    dd = TN_DISTRICTS.get(district, TN_DISTRICTS.get("Thoothukudi", {}))
    return get_ai_conclusion(district, dd, land_ha, farmer_name, crop, api_key)

def fetch_soil_info(district: str, crop: str):
    if district not in TN_DISTRICTS or crop not in CROP_DB:
        return {}
    return get_soil_info(TN_DISTRICTS[district], crop)

def fetch_irrigation_info(district: str, land_ha: float, crop: str):
    if district not in TN_DISTRICTS or crop not in CROP_DB:
        return {}
    return get_irrigation_info(TN_DISTRICTS[district], land_ha, crop)

def fetch_pest_scanner(crop: str, symptom: str = "", image_b64: str = "", api_key: str = ""):
    return diagnose_pest_disease(crop, symptom, image_b64, api_key)

def fetch_pdf_report(district: str, farmer_name: str, land_ha: float, crop: str):
    dd = TN_DISTRICTS.get(district, TN_DISTRICTS.get("Thoothukudi", {}))
    return generate_farm_pdf_report(district, dd, farmer_name, land_ha, crop)

def fetch_schemes(farmer_type: str = "Small/Marginal (<2 ha)", land_ha: float = 1.0, category: str = "All"):
    return match_government_schemes(farmer_type, land_ha, category)

def fetch_crop_timeline(crop: str, district: str):
    return get_crop_timeline(crop, district)

def fetch_mandi_compare(crop: str, district: str, land_ha: float):
    return calc_mandi_transport_profit(crop, district, land_ha)

def fetch_weather_risk(district: str):
    return get_district_weather_risk(district)

def fetch_equipment_calc(crop: str, land_ha: float):
    return calc_equipment_labor_cost(crop, land_ha)

def fetch_solar_pump(land_ha: float, current_source: str = "Diesel", well_depth_ft: int = 150):
    return calc_solar_pump_roi(land_ha, current_source, well_depth_ft)

def fetch_ml_yield(crop: str, rainfall_mm: float, avg_temp: float, soil_ph: float, nitrogen: float = 80, phosphorus: float = 40, potassium: float = 40):
    return predict_crop_yield_ml(crop, rainfall_mm, avg_temp, soil_ph, nitrogen, phosphorus, potassium)

# ─────────────────────────────────────────────────────────────────────────────
# LOAD BACKEND DATA
# ─────────────────────────────────────────────────────────────────────────────

all_data = fetch_all_districts()
crops_data = fetch_all_crops()
hist_data = fetch_historical_yield()

TN_DISTRICTS_DATA = all_data["data"] if all_data else TN_DISTRICTS
CROP_DB_DATA = crops_data["data"] if crops_data else CROP_DB
dist_list = sorted(TN_DISTRICTS_DATA.keys())
HIST_YEARS_DATA = hist_data["years"] if hist_data else HIST_YEARS
HISTORICAL_YIELD_DATA = hist_data["data"] if hist_data else HISTORICAL_YIELD

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────

defaults = {
    "profile": {
        "farmer_name": "Ramasamy K.",
        "phone_email": "9840012345",
        "role": "Farmer / Seller",
        "district": "Thoothukudi",
        "land_acres": 3.0,
        "soil_type": "Red Loamy",
        "irrigation": "Canal / River Water",
        "current_crop": "Paddy"
    },
    "user_role": "Farmer / Seller",
    "selected_crop": "Paddy",
    "active_nav": "Dashboard",
    "messages": [],
    "api_key": "",
    "conclusion_text": None,
    "weather_data": None,
    "weather_district": "Thoothukudi",
    "soil_report": None,
    "irrigation_report": None,
    "market_report": None,
    "lang": "English",
    # ── Load persisted data from JSON files on first run ──
    # These are SHARED across all users and survive restarts
    "supply_listings": load_listings(),
    "buyer_demands": load_demands(),
    "driver_vehicles": load_vehicles() or INITIAL_DRIVER_VEHICLES,
    "placed_orders": load_orders(),
    "_db_initialized": True
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Always sync from disk on each page load (picks up other users' changes) ──
# This makes data posted by one user visible to another on refresh.
if "_db_initialized" in st.session_state:
    disk_listings = load_listings()
    if disk_listings:
        st.session_state.supply_listings = disk_listings
    disk_demands = load_demands()
    if disk_demands:
        st.session_state.buyer_demands = disk_demands
    disk_orders = load_orders()
    if disk_orders:
        st.session_state.placed_orders = disk_orders

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOGIN / FARMER PROFILE SCREEN
# ─────────────────────────────────────────────────────────────────────────────

def render_login_view():
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0 1rem 0;">
        <div style="display:inline-block; background:#dcfce7; color:#15803d; font-weight:700; font-size:0.8rem; padding:4px 12px; border-radius:20px; letter-spacing:1px; margin-bottom:8px;">STAKEHOLDER ONBOARDING</div>
        <h1 style="color: #0f172a; font-size: 2.3rem; margin: 4px 0;">HarvestLine Agritech Portal Sign In & Registration</h1>
        <p style="color: #475569; font-size: 1.05rem; max-width: 650px; margin: 0 auto 1.5rem auto;">
            Join Tamil Nadu's Unified Agritech Platform for Direct Produce Linking, Buyer Demand Matching & Cold-Chain Delivery Logistics.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_centered, col_side = st.columns([3, 1])
    
    with col_centered:
        tab_login, tab_register, tab_demo = st.tabs([
            "Sign In to Account", "Create New Account", "Quick 1-Click Demo"
        ])
        
        # TAB 1: SIGN IN (EXISTING USER)
        with tab_login:
            st.markdown("### Portal Sign In")
            st.caption("Enter your Username / Registered Mobile Number and Password to access your portal.")
            
            with st.form("login_form"):
                log_role = st.selectbox("Select Account Role", [
                    "Farmer / Seller", "Buyer / Wholesaler", "Driver / Cold-Chain Logistics"
                ], index=0)
                log_user = st.text_input("Username or Registered Mobile Number", placeholder="e.g. 9840012345", key="login_user_id")
                log_pass = st.text_input("Account Password", type="password", placeholder="Enter your password", key="login_password")
                
                st.markdown("---")
                login_sub = st.form_submit_button("Sign In to Portal ->", type="primary", use_container_width=True)
                
                if login_sub:
                    u_clean = log_user.strip()
                    if not u_clean:
                        st.error("Please enter your Username or Registered Mobile Number.")
                    else:
                        existing = get_user(u_clean)
                        # Fallback for demo accounts or newly registered users
                        if not existing and u_clean in ["9840012345", "9840099887", "9840077665"]:
                            if log_role == "Farmer / Seller":
                                existing = {"phone_email": "9840012345", "farmer_name": "Ramasamy K.", "role": "Farmer / Seller", "district": "Thoothukudi", "land_acres": 3.0, "soil_type": "Red Loamy", "irrigation": "Canal / River Water"}
                            elif log_role == "Buyer / Wholesaler":
                                existing = {"phone_email": "9840099887", "farmer_name": "Annapoorna Restaurant Group", "role": "Buyer / Wholesaler", "buyer_type": "Restaurant / Hotel", "district": "Sivakasi"}
                            else:
                                existing = {"phone_email": "9840077665", "farmer_name": "Sundaram T.", "role": "Driver / Cold-Chain Logistics", "vehicle_reg": "TN 67 AD 4521", "district": "Sivakasi"}

                        if existing:
                            st.session_state.profile = existing
                            st.session_state.user_role = log_role
                            st.session_state.active_nav = "Dashboard"
                            st.success(f"Welcome back, {existing.get('farmer_name', 'User')}! Logged in as {log_role}.")
                            st.balloons()
                            st.rerun()
                        else:
                            # Auto-create if first time login with details
                            new_p = {
                                "phone_email": u_clean,
                                "farmer_name": u_clean.capitalize(),
                                "role": log_role,
                                "district": "Thoothukudi" if log_role == "Farmer / Seller" else "Sivakasi",
                                "land_acres": 3.0 if log_role == "Farmer / Seller" else 0.0,
                                "soil_type": "Red Loamy" if log_role == "Farmer / Seller" else "N/A",
                                "buyer_type": "Wholesaler" if log_role == "Buyer / Wholesaler" else "N/A"
                            }
                            save_user(new_p)
                            st.session_state.profile = new_p
                            st.session_state.user_role = log_role
                            st.session_state.active_nav = "Dashboard"
                            st.success(f"Welcome, {new_p['farmer_name']}! Account initialized.")
                            st.rerun()

        # TAB 2: REGISTER (NEW USER)
        with tab_register:
            st.markdown("### Create Portal Account")
            st.caption("Fill in your details below to register on the HarvestLine Agritech Platform.")
            
            reg_role = st.selectbox("Select Stakeholder Category *", [
                "Farmer / Seller", "Buyer / Wholesaler", "Driver / Cold-Chain Logistics"
            ], index=0, key="reg_role_select")
            
            with st.form("register_form"):
                rf1, rf2 = st.columns(2)
                with rf1:
                    reg_name = st.text_input("Full Name / Official Name *", placeholder="e.g. Ramasamy K. or Annapoorna Group")
                    reg_phone = st.text_input("Login Username / Mobile Number *", placeholder="98400XXXXX")
                    reg_pass = st.text_input("Account Password *", type="password", placeholder="Min 6 characters")
                with rf2:
                    reg_dist = st.selectbox("Operating District *", dist_list if dist_list else ["Thoothukudi"], index=0)
                    
                    if reg_role == "Farmer / Seller":
                        reg_land = st.number_input("Total Farm Land Area (Acres)", min_value=0.25, max_value=500.0, value=3.0, step=0.5)
                        reg_soil = st.selectbox("Soil Type", ["Red Loamy", "Black Cotton", "Alluvial Soil", "Coastal Alluvial", "Sandy Clay"])
                    elif reg_role == "Buyer / Wholesaler":
                        reg_btype = st.selectbox("Buyer Category", ["Restaurant / Hotel", "Supermarket Retailer", "Mandi Wholesaler", "Food Processing Unit", "Exporter"])
                    else:
                        reg_veh = st.text_input("Vehicle Reg No.", placeholder="TN XX YY ZZZZ")

                st.markdown("---")
                reg_sub = st.form_submit_button("Complete Portal Registration ->", type="primary", use_container_width=True)

                if reg_sub:
                    phone_c = reg_phone.strip()
                    name_c  = reg_name.strip()
                    if not phone_c or not name_c:
                        st.error("Please fill in your Name and Mobile Number / Username.")
                    else:
                        p_data = {
                            "role": reg_role,
                            "farmer_name": name_c,
                            "phone_email": phone_c,
                            "password": reg_pass.strip() or "123456",
                            "district": reg_dist,
                            "land_acres": reg_land if reg_role == "Farmer / Seller" else 0.0,
                            "soil_type": reg_soil if reg_role == "Farmer / Seller" else "N/A",
                            "buyer_type": reg_btype if reg_role == "Buyer / Wholesaler" else "N/A",
                            "vehicle_reg": reg_veh if reg_role == "Driver / Cold-Chain Logistics" else "N/A"
                        }
                        save_user(p_data)     #  Save user to Supabase
                        save_profile(p_data)  # cache
                        st.session_state.profile = p_data
                        st.session_state.user_role = reg_role
                        st.session_state.active_nav = "Dashboard"
                        st.success(f" Registration Complete! Welcome **{name_c}** ({reg_role}).")
                        st.balloons()
                        st.rerun()

        # TAB 3: QUICK 1-CLICK DEMO
        with tab_demo:
            st.markdown("### 1-Click Instant Demo Portals")
            st.caption("Click any role below to launch the system with pre-loaded mock data.")
            
            d_c1, d_c2, d_c3 = st.columns(3)
            with d_c1:
                st.markdown("** Farmer Portal Demo**")
                st.caption("Ramasamy K. • 3.0 Acres in Thoothukudi")
                if st.button("Launch Farmer Portal", use_container_width=True, type="primary"):
                    p_data = {
                        "role": "Farmer / Seller",
                        "farmer_name": "Ramasamy K.",
                        "phone_email": "9840012345",
                        "district": "Thoothukudi",
                        "land_acres": 3.0,
                        "soil_type": "Red Loamy",
                        "irrigation": "Canal / River Water",
                        "current_crop": "Paddy"
                    }
                    st.session_state.profile = p_data
                    st.session_state.user_role = "Farmer / Seller"
                    st.session_state.selected_crop = "Paddy"
                    st.session_state.active_nav = "Dashboard"
                    st.rerun()

            with d_c2:
                st.markdown("** Buyer Portal Demo**")
                st.caption("Annapoorna Group • Buyer in Sivakasi")
                if st.button("Launch Buyer Portal", use_container_width=True, type="primary"):
                    b_data = {
                        "role": "Buyer / Wholesaler",
                        "farmer_name": "Annapoorna Restaurant Group",
                        "phone_email": "9840099887",
                        "buyer_type": "Restaurant / Hotel",
                        "district": "Sivakasi",
                        "land_acres": 0.0,
                        "soil_type": "N/A",
                        "irrigation": "N/A",
                        "current_crop": "Tomato"
                    }
                    st.session_state.profile = b_data
                    st.session_state.user_role = "Buyer / Wholesaler"
                    st.session_state.active_nav = "Dashboard"
                    st.rerun()

            with d_c3:
                st.markdown("** Driver Portal Demo**")
                st.caption("Sundaram T. • Cold-Chain Truck TN67")
                if st.button("Launch Driver Portal", use_container_width=True, type="primary"):
                    d_data = {
                        "role": "Driver / Cold-Chain Logistics",
                        "farmer_name": "Sundaram T.",
                        "phone_email": "9840077665",
                        "vehicle_reg": "TN 67 AD 4521",
                        "district": "Sivakasi",
                        "land_acres": 0.0,
                        "soil_type": "N/A",
                        "irrigation": "N/A",
                        "current_crop": "Tomato"
                    }
                    st.session_state.profile = d_data
                    st.session_state.user_role = "Driver / Cold-Chain Logistics"
                    st.session_state.active_nav = "Delivery Route Optimizer"
                    st.rerun()


    with col_side:
        st.subheader("Unified System Capabilities")
        st.markdown("""
        -  **Farmer Portal**: Crop suitability, yield ML, pest diagnostics, freshness monitor, and credit trust score (300-850).
        -  **Buyer Portal**: NLP text parser for demand, ranked Haversine matching, and multi-vendor supply pooling.
        -  **Driver Portal**: Nearest-neighbor route optimizer and live cold-chain refrigeration telemetry (°C).
        """)


# ─────────────────────────────────────────────────────────────────────────────
# 2. MAIN APPLICATION WORKSPACE
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if st.session_state.profile is None:
        render_login_view()
        return

    else:
        # Load active farmer profile context
        prof = st.session_state.profile
        if prof.get("role"):
            st.session_state.user_role = prof.get("role")
        farmer_name = prof.get("farmer_name", "Farmer")
        district = prof.get("district", "Thoothukudi")
        raw_land = prof.get("land_acres")
        land_acres = float(raw_land) if (raw_land is not None and float(raw_land) > 0) else 3.0
        land_ha = land_acres * 0.404686
        soil_type = prof.get("soil_type", "Red Loamy")
        irrigation = prof.get("irrigation", "Canal / River Water")
        dist_info = TN_DISTRICTS.get(district, {})

    # ─────────────────────────────────────────────────────────────────────────────
    # SIDEBAR NAVIGATION & PROFILE SUMMARY
    # ─────────────────────────────────────────────────────────────────────────────

    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <div>
                <h3 style="margin: 0; color: #059669;">AgriSmart TN</h3>
                <small style="color: #64748b;">Harvestline Unified Platform</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Role is fixed upon login. Click 'Logout / Switch Account' below to switch.


        # Language Switcher
        sel_lang = st.radio("Language / மொழி", ["English", "தமிழ்"], index=0 if st.session_state.lang == "English" else 1, horizontal=True)
        if sel_lang != st.session_state.lang:
            st.session_state.lang = sel_lang
            st.rerun()
        cur_lang = st.session_state.lang

        # Profile Card
        prof_card_html = f"""<div style="background: rgba(16, 185, 129, 0.08); padding: 14px; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2); margin-bottom: 15px;"><div style="font-weight: 700; color: #065f46; font-size: 1.05rem;"> {farmer_name}</div><div style="font-size: 0.85rem; color: #047857; margin-top: 4px; line-height: 1.4;"><b>Role:</b> {st.session_state.user_role}<br><b>Location:</b> {district}<br>{"<b>Land:</b> " + str(land_acres) + " Acres" if st.session_state.user_role == "Farmer / Seller" else ""}</div></div>"""
        st.markdown(prof_card_html, unsafe_allow_html=True)


        if st.button("Logout / Switch Account", use_container_width=True):
            st.session_state.profile = None
            st.rerun()

        # ── ROLE-AWARE SIDEBAR NAVIGATION (SELLER vs BUYER PoV) ──
        is_buyer = "Buyer" in str(st.session_state.get("user_role", "")) or (prof and "Buyer" in str(prof.get("role", "")))
        if is_buyer:
            st.markdown("<div class='sidebar-nav-header'> BUYER PROCUREMENT & ORDERS</div>", unsafe_allow_html=True)
            b_cnt = len([o for o in st.session_state.placed_orders if o.get("buyer_name") == farmer_name or (prof and prof.get("phone_email") and o.get("buyer_phone") == prof.get("phone_email"))])
            b_label = f"Manage My Orders ({b_cnt})" if b_cnt > 0 else "Manage My Orders & Tracking"
            buyer_g1 = [
                ("Dashboard", "Procurement Dashboard"),
                ("Manage My Orders", b_label),
                ("Marketplace & Live Produce", "Browse Fresh Produce Marketplace"),
                ("AI Demand NLP Parser", "Post Buyer Demand (AI NLP)"),
                ("Ranked Supply Matches", "Ranked Farmer Supply Matches"),
                ("Multi-Farmer Supply Pooling", "Multi-Farmer Order Aggregation"),
                ("Marketplace & Live Map", "Live Produce Geographic Map")
            ]
            for internal_nav, display_label in buyer_g1:
                is_active = (st.session_state.active_nav == internal_nav)
                label = f"• {display_label}" if is_active else display_label
                if st.button(label, key=f"b_nav1_{internal_nav}", use_container_width=True):
                    st.session_state.active_nav = internal_nav
                    st.rerun()

            st.markdown("<div class='sidebar-nav-header'> CROP SUPPLY & CAPACITY ANALYTICS</div>", unsafe_allow_html=True)
            buyer_g2 = [
                ("Farm Sensor Monitoring", "Farm Sensor Monitoring"),
                ("Smart Crop Finder", "Crop Harvest Availability Calendar"),
                ("Seed & Input Planner", "Farmer Production Capacity Planner"),
                ("Acre-based Profit & Cost", "Farm-Gate Price & Cost Analysis"),
                ("ML Crop Yield Predictor", "ML Crop Harvest Supply Predictor"),
                ("Solar Pump & PM-KUSUM ROI", "Farm Infrastructure & Energy Audit"),
                ("Farm Summary & PDF Export", "Procurement Advisory PDF Export")
            ]
            for internal_nav, display_label in buyer_g2:
                is_active = (st.session_state.active_nav == internal_nav)
                label = f"• {display_label}" if is_active else display_label
                if st.button(label, key=f"b_nav2_{internal_nav}", use_container_width=True):
                    st.session_state.active_nav = internal_nav
                    st.rerun()

            st.markdown("<div class='sidebar-nav-header'> LOGISTICS & ADVISORY</div>", unsafe_allow_html=True)
            buyer_g3 = [
                ("Delivery Route Optimizer", "Cold-Chain Logistics Optimizer"),
                ("Refrigeration Cold-Chain Monitor", "Refrigerated Transit Telemetry"),
                ("Freshness & Spoilage Monitor", "Produce Quality & Shelf-Life Tracker"),
                ("AI Crop Advisor Chat", "Agri Procurement AI Assistant"),
                ("Live Weather & Climate Risk", "Supply Disruption & Climate Risk"),
                ("Pest AI Diagnostics", "Crop Quality & Health Inspector"),
                ("Govt Schemes & Subsidies", "Agri Procurement Govt Schemes"),
                ("Mandi Price Tracker", "Mandi Price Benchmarking Engine"),
                ("Alternative Credit Trust Profile", "Farmer Verification & Trust Rating"),
                ("Direct In-App Chat", "Direct Farmer Negotiation Chat")
            ]
            for internal_nav, display_label in buyer_g3:
                is_active = (st.session_state.active_nav == internal_nav)
                label = f"• {display_label}" if is_active else display_label
                if st.button(label, key=f"b_nav3_{internal_nav}", use_container_width=True):
                    st.session_state.active_nav = internal_nav
                    st.rerun()
        else:
            #  FARMER / SELLER PORTAL (Full feature set enabled!)
            st.markdown("<div class='sidebar-nav-header'> SELLER MARKETPLACE & PRODUCE</div>", unsafe_allow_html=True)
            s_pend_cnt = len([
                o for o in st.session_state.placed_orders
                if (o.get("seller_name") == farmer_name or (prof and prof.get("phone_email") and o.get("seller_phone") == prof.get("phone_email")))
                and "PENDING" in str(o.get("status", "")).upper()
            ])
            s_rec_label = f"Received Orders ({s_pend_cnt} ⏳)" if s_pend_cnt > 0 else "Received Orders & Fulfillment"
            seller_g1 = [
                ("Dashboard", "Dashboard"),
                ("Seller Received Orders", s_rec_label),
                ("Farm Sensor Monitoring", "Farm Sensor Monitoring"),
                ("Marketplace & Live Produce", "Marketplace & Live Produce"),
                ("Post Fresh Produce", "Post Fresh Produce"),
                ("Seller Supply Pooling", "Seller Supply Pooling"),
                ("Freshness & Spoilage Monitor", "Freshness & Spoilage Monitor"),
                ("Alternative Credit Trust Profile", "Alternative Credit Trust Profile"),
                ("Marketplace & Live Map", "Marketplace & Live Map")
            ]

            for internal_nav, display_label in seller_g1:
                is_active = (st.session_state.active_nav == internal_nav)
                label = f"• {display_label}" if is_active else display_label
                if st.button(label, key=f"s_nav1_{internal_nav}", use_container_width=True):
                    st.session_state.active_nav = internal_nav
                    st.rerun()

            st.markdown("<div class='sidebar-nav-header'> CROP PLANNING & AGRONOMIC AI</div>", unsafe_allow_html=True)
            seller_g2 = [
                "Smart Crop Finder", "Seed & Input Planner", "Acre-based Profit & Cost",
                "ML Crop Yield Predictor", "Solar Pump & PM-KUSUM ROI", "AI Crop Advisor Chat",
                "Live Weather & Climate Risk", "Pest AI Diagnostics", "Govt Schemes & Subsidies",
                "Mandi Price Tracker", "Farm Summary & PDF Export"
            ]
            for item in seller_g2:
                is_active = (st.session_state.active_nav == item)
                label = f"• {item}" if is_active else item
                if st.button(label, key=f"s_nav2_{item}", use_container_width=True):
                    st.session_state.active_nav = item
                    st.rerun()

            st.markdown("<div class='sidebar-nav-header'> LOGISTICS & DIRECT NEGOTIATION</div>", unsafe_allow_html=True)
            seller_g3 = [
                "Delivery Route Optimizer", "Refrigeration Cold-Chain Monitor", "Direct In-App Chat"
            ]
            for item in seller_g3:
                is_active = (st.session_state.active_nav == item)
                label = f"• {item}" if is_active else item
                if st.button(label, key=f"s_nav3_{item}", use_container_width=True):
                    st.session_state.active_nav = item
                    st.rerun()

        st.markdown("---")
        st.subheader("Access Key (Optional)")
        typed_key = st.text_input(
            "Online API Key", value=st.session_state.api_key,
            type="password", placeholder="Leave blank for offline mode",
            key="api_key_widget"
        )
        if typed_key:
            st.session_state.api_key = typed_key

    # ─────────────────────────────────────────────────────────────────────────────
    # PAGE ROUTING & VIEW IMPLEMENTATIONS
    # ─────────────────────────────────────────────────────────────────────────────

    nav = st.session_state.active_nav

    # TOP METRIC BAR
    top_c1, top_c2, top_c3, top_c4, top_c5 = st.columns(5)
    with top_c1: st.metric("Active Role", st.session_state.user_role)
    with top_c2: st.metric("District", district)
    with top_c3: st.metric("Selected Crop", st.session_state.selected_crop or "Tomato")
    with top_c4: st.metric("Land / Entity", f"{land_acres} Acres" if land_acres > 0 else prof.get("buyer_type","Logistics"))
    with top_c5: st.metric("District Temp", f"{dist_info.get('avg_temp', 29)}°C")
    st.markdown("---")


    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE DASHBOARD VIEW (SELLER & BUYER SUPPORTED)
    # ─────────────────────────────────────────────────────────────────────────────
    if nav == "Dashboard":
        is_buyer_dash = "Buyer" in str(st.session_state.get("user_role", "")) or (prof and "Buyer" in str(prof.get("role", "")))
        if is_buyer_dash:
            # ── BUYER DASHBOARD (MATCHING HARVESTLINE DESIGN) ──
            b_type = prof.get("buyer_type", "Restaurant / Hotel")
            st.markdown(f"## Welcome back, {farmer_name} ")
            st.caption(f"Buyer Profile: {b_type} | Operating Location: {district} | Status: Verified Buyer")

            # Top 5 Stat Cards (tailored for Buyer!)
            my_demands = [d for d in st.session_state.buyer_demands if d.get("posted_by_phone") == prof.get("phone_email", "") or d.get("buyer_name") == farmer_name]
            my_orders = [o for o in st.session_state.placed_orders if o.get("buyer_name") == farmer_name or o.get("buyer_phone") == prof.get("phone_email", "")]
            all_sellers = set(s.get("farmer_name") for s in st.session_state.supply_listings if s.get("status") == "ACTIVE")
            flash_deals = [s for s in st.session_state.supply_listings if calc_freshness_decay(s.get("crop", "Tomato"), s.get("harvest_hours_ago", 12)).get("suggested_flash_discount_pct", 0) > 0]
            total_spend = sum(float(o.get("total_amount", 0)) for o in my_orders)

            st1, st2, st3, st4, st5 = st.columns(5)
            with st1:
                st.metric("Active Demands ", len(my_demands) if my_demands else 3)
            with st2:
                st.metric("Placed Orders ", len(my_orders) if my_orders else 14)
            with st3:
                st.metric("Matched Sellers ", len(all_sellers) if all_sellers else 28)
            with st4:
                st.metric("Flash Deals ", f"{len(flash_deals)} deals" if flash_deals else "6 deals")
            with st5:
                st.metric("Procurement Spend ", fmt_inr(total_spend) if total_spend > 0 else "₹42,500")

            st.markdown("---")

            # Main Layout: 2 Columns (Left: 2/3, Right: 1/3)
            dash_left, dash_right = st.columns([2, 1])

            with dash_left:
                # CARD 1: Tell us what you need (AI Demand Entry)
                st.markdown("""
                <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #cbd5e1; margin-bottom: 20px;">
                    <h4 style="margin: 0; color: #0f172a;"> Tell us what you need</h4>
                    <p style="color: #64748b; font-size: 0.9rem; margin-top: 4px;">Type or speak your produce requirement, and AI will list it and match nearby farmers instantly.</p>
                </div>
                """, unsafe_allow_html=True)

                ai_demand_text = st.text_area(
                    "Demand Description",
                    placeholder=f"e.g., Need 500 kg tomatoes at ₹30 per kg, available today in {district}. Can pick up within 20 km.",
                    height=90,
                    key="b_dash_ai_demand_input"
                )

                if st.button("Analyze & Post Buyer Demand Live", type="primary", use_container_width=True, key="btn_b_dash_analyze"):
                    if not ai_demand_text or not ai_demand_text.strip():
                        st.warning("⚠️ Please enter a demand description before publishing.")
                    else:
                        parsed_d = parse_buyer_demand_nlp(ai_demand_text, district)
                        crop_d = parsed_d.get("crop", "Tomato")
                        qty_d = float(parsed_d.get("quantity_kg", 500))
                        price_d = float(parsed_d.get("max_price_per_kg", 30))

                        new_dem_id = f"DEM-{len(st.session_state.buyer_demands) + 201}"
                        new_demand = {
                            "id": new_dem_id,
                            "buyer_name": farmer_name,
                            "buyer_phone": prof.get("phone_email", ""),
                            "buyer_type": b_type,
                            "raw_text": ai_demand_text,
                            "crop": crop_d,
                            "quantity_kg": qty_d,
                            "max_price_per_kg": price_d,
                            "district": district,
                            "min_freshness_pct": 70,
                            "status": "OPEN",
                            "posted_by_phone": prof.get("phone_email", "")
                        }
                        st.session_state.buyer_demands.append(new_demand)
                        save_demand(new_demand)    #  Save to Supabase demands table

                        st.success(f" **{farmer_name}** — Demand Request **{new_dem_id}** ({qty_d:.0f} kg {crop_d}) published live! Go to **Ranked Supply Matches** to view matching sellers.")
                        st.balloons()
                        st.rerun()

                # CARD 2: Freshness & Flash Sale Deals Alert
                st.markdown("""
                <div style="background: #f0fdf4; border-radius: 12px; padding: 18px; border: 1px solid #86efac; margin-top: 20px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin: 0; color: #166534;"> Live Flash Sales & High-Freshness Deals Alert</h4>
                        <span style="background: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 0.8rem;">Flash Sale - 20% Off</span>
                    </div>
                    <p style="color: #166534; margin-top: 8px; font-weight: 500;">
                        <b>400 kg Fresh Tomatoes (92% Freshness)</b> available near Sivakasi at ₹20/kg (Regular ₹25/kg).
                    </p>
                </div>
                """, unsafe_allow_html=True)

                fl_col1, fl_col2, fl_col3 = st.columns(3)
                with fl_col1:
                    if st.button("Order Flash Deal Now", use_container_width=True, type="primary"):
                        st.session_state.active_nav = "Marketplace & Live Produce"
                        st.rerun()
                with fl_col2:
                    if st.button("Chat with Seller", use_container_width=True):
                        st.session_state.active_nav = "Direct In-App Chat"
                        st.rerun()
                with fl_col3:
                    if st.button("View All Deals", use_container_width=True):
                        st.session_state.active_nav = "Marketplace & Live Produce"
                        st.rerun()

            with dash_right:
                # RIGHT CARD 1: Local Supply Insight
                st.markdown(f"""
                <div style="background: #faf5ff; border-radius: 12px; padding: 16px; border: 1px solid #e9d5ff; margin-bottom: 20px;">
                    <h4 style="margin: 0; color: #7e22ce;"> Local Supply Insight</h4>
                    <p style="color: #6b21a8; font-size: 0.88rem; margin-top: 8px; line-height: 1.4;">
                        There are <b>6 farmers</b> offering fresh Tomato & Paddy harvests within a 20km radius of {district}.
                        Total available inventory: <b>2,400 kg</b>.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View Ranked Seller Matches ->", use_container_width=True):
                    st.session_state.active_nav = "Ranked Supply Matches"
                    st.rerun()

                # RIGHT CARD 2: Your Placed Orders
                my_b_orders = [o for o in st.session_state.placed_orders 
                               if o.get("buyer_name") == farmer_name or 
                                  (prof.get("phone_email") and o.get("buyer_phone") == prof.get("phone_email")) or
                                  o.get("buyer_phone") == farmer_name]
                pending_b_cnt = len([o for o in my_b_orders if "PENDING" in str(o.get("status", "")).upper()])
                confirmed_b_cnt = len([o for o in my_b_orders if "CONFIRMED" in str(o.get("status", "")).upper() or "DISPATCH" in str(o.get("status", "")).upper() or "DELIVERED" in str(o.get("status", "")).upper()])
                pooled_b_cnt = len([o for o in my_b_orders if o.get("is_pooled")])

                st.markdown(f"""
                <div style="background: white; border-radius: 12px; padding: 16px; border: 1px solid #cbd5e1; margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin: 0; color: #0f172a;">📦 Your Placed Orders</h4>
                        <span style="background: #e0f2fe; color: #0284c7; padding: 3px 8px; border-radius: 10px; font-weight: 700; font-size: 0.78rem;">{len(my_b_orders)} Total</span>
                    </div>
                    <div style="margin-top: 8px; display:flex; gap: 6px; font-size: 0.78rem;">
                        <span style="background: #fef3c7; color: #b45309; padding: 2px 6px; border-radius: 6px; font-weight: 600;">{pending_b_cnt} Pending</span>
                        <span style="background: #dcfce7; color: #15803d; padding: 2px 6px; border-radius: 6px; font-weight: 600;">{confirmed_b_cnt} Confirmed</span>
                        <span style="background: #ede9fe; color: #6d28d9; padding: 2px 6px; border-radius: 6px; font-weight: 600;">{pooled_b_cnt} Pooled</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if my_b_orders:
                    for o_item in my_b_orders[-3:]:
                        o_id = o_item.get("id", "ORD")
                        o_crop = o_item.get("crop", "Produce")
                        o_qty = float(o_item.get("quantity_kg", 0))
                        o_amt = float(o_item.get("total_amount", 0) or (o_qty * float(o_item.get("price_per_kg", 0))))
                        o_stat = str(o_item.get("status", "PENDING SELLER CONFIRMATION"))
                        is_p = o_item.get("is_pooled", False)
                        
                        stat_color = "#d97706" if "PENDING" in o_stat else ("#15803d" if "CONFIRMED" in o_stat else "#0284c7")
                        stat_bg = "#fef3c7" if "PENDING" in o_stat else ("#dcfce7" if "CONFIRMED" in o_stat else "#e0f2fe")
                        pool_tag = '<span style="background:#ede9fe; color:#6d28d9; padding:1px 5px; border-radius:4px; font-size:0.7rem; font-weight:bold; margin-left:4px;">POOLED</span>' if is_p else ''

                        st.markdown(f"""
                        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; margin-bottom: 6px; font-size: 0.85rem;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div><b>#{o_id}</b> — {o_crop}{pool_tag}<br><small style="color:#64748b;">{o_qty:.0f} kg • ₹{o_amt:,.0f} • Seller: {o_item.get('seller_name', 'Farmer')}</small></div>
                                <span style="background:{stat_bg}; color:{stat_color}; padding:2px 8px; border-radius:8px; font-weight:bold; font-size:0.72rem;">{"Pending" if "PENDING" in o_stat else ("Confirmed" if "CONFIRMED" in o_stat else o_stat[:12])}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No orders placed yet. Browse marketplace to procure fresh produce.")

                if st.button("📋 Manage My Orders & Live Tracking ->", use_container_width=True, type="primary", key="btn_dash_manage_b_orders"):
                    st.session_state.active_nav = "Manage My Orders"
                    st.rerun()
        else:
            # ── SELLER DASHBOARD (MATCHING HARVESTLINE DESIGN) ──
            st.markdown(f"## Welcome back, {farmer_name} ")
            st.caption(f"Location: {district} | Land: {land_acres} Acres | Soil: {soil_type} | Irrigation: {irrigation}")

            # Top 5 Stat Cards (as in screenshot!)
            my_listings = [s for s in st.session_state.supply_listings if s.get("posted_by_phone") == prof.get("phone_email", "") or s.get("farmer_name") == farmer_name]
            my_orders = [o for o in st.session_state.placed_orders 
                         if o.get("seller_name") == farmer_name or 
                            (prof.get("phone_email") and o.get("seller_phone") == prof.get("phone_email")) or
                            (not o.get("seller_phone") and o.get("seller_name") == farmer_name)]
            my_pending_orders = [o for o in my_orders if "PENDING" in str(o.get("status", "")).upper()]
            my_pooled_orders = [o for o in my_orders if o.get("is_pooled")]
            open_demands = st.session_state.buyer_demands or []
            at_risk = [s for s in my_listings if calc_freshness_decay(s.get("crop", "Tomato"), s.get("harvest_hours_ago", 12)).get("remaining_freshness_pct", 100) < 70]
            total_sales = sum(float(o.get("total_amount", 0) or (float(o.get("quantity_kg", 0)) * float(o.get("price_per_kg", 0)))) for o in my_orders if "CONFIRMED" in str(o.get("status", "")).upper())

            st1, st2, st3, st4, st5 = st.columns(5)
            with st1:
                st.metric("Active Listings ", len(my_listings) if my_listings else len(st.session_state.supply_listings))
            with st2:
                st.metric("Pending Orders ", f"{len(my_pending_orders)} Pending", delta=f"{len(my_orders)} Total" if my_orders else None)
            with st3:
                st.metric("Matched Buyers ", len(open_demands) if open_demands else 28)
            with st4:
                st.metric("At-Risk Produce ", f"{len(at_risk)} items" if at_risk else "6 items")
            with st5:
                st.metric("Today's Sales ", fmt_inr(total_sales) if total_sales > 0 else "₹42,500")

            st.markdown("---")

            # Main Layout: 2 Columns (Left: 2/3, Right: 1/3) matching screenshot!
            dash_left, dash_right = st.columns([2, 1])

            with dash_left:
                # CARD 1: Tell us what you have (AI Supply Entry)
                st.markdown("""
                <div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #cbd5e1; margin-bottom: 20px;">
                    <h4 style="margin: 0; color: #0f172a;"> Tell us what you have</h4>
                    <p style="color: #64748b; font-size: 0.9rem; margin-top: 4px;">Type or speak your available produce, and AI will list it instantly to all buyers across Tamil Nadu.</p>
                </div>
                """, unsafe_allow_html=True)

                ai_supply_text = st.text_area(
                    "Supply Description",
                    placeholder=f"e.g., I have 500 kg tomatoes at ₹30 per kg, available today in {district}. Can deliver within 20 km.",
                    height=90,
                    key="dash_ai_supply_input"
                )

                if st.button("Analyze & Publish Supply Live", type="primary", use_container_width=True, key="btn_dash_analyze"):
                    if not ai_supply_text or not ai_supply_text.strip():
                        st.warning("⚠️ Please enter a supply description before publishing.")
                        st.stop()
                    parsed_s = parse_buyer_demand_nlp(ai_supply_text, district)
                    crop_p = parsed_s.get("crop", "Tomato")
                    qty_p = float(parsed_s.get("quantity_kg", 500))
                    price_p = float(parsed_s.get("max_price_per_kg", 30))

                    new_id = f"SUP-{len(st.session_state.supply_listings) + 101}"
                    new_listing = {
                        "id": new_id,
                        "farmer_name": farmer_name,
                        "phone": prof.get("phone_email", "9840012345"),
                        "crop": crop_p,
                        "quantity_kg": qty_p,
                        "price_per_kg": price_p,
                        "district": district,
                        "harvest_hours_ago": 6,
                        "status": "ACTIVE",
                        "posted_by_phone": prof.get("phone_email", "")
                    }
                    st.session_state.supply_listings.append(new_listing)
                    save_listing(new_listing)   #  Write to Supabase listings table

                    st.success(f" **{farmer_name}** — Published **{qty_p:.0f} kg {crop_p}** at ₹{price_p}/kg live to all buyers! Listing ID: {new_id}")
                    st.balloons()
                    st.rerun()

                # CARD 2: Near-Spoilage Alert
                st.markdown("""
                <div style="background: #fef2f2; border-radius: 12px; padding: 18px; border: 1px solid #fca5a5; margin-top: 20px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin: 0; color: #dc2626;"> Near-Spoilage Alert</h4>
                        <span style="background: #fee2e2; color: #dc2626; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 0.8rem;">High Risk</span>
                    </div>
                    <p style="color: #991b1b; margin-top: 8px; font-weight: 500;">
                        <b>250 kg Tomatoes</b> in your inventory are approaching their freshness threshold. Freshness remaining: <b>14h 28m</b>
                    </p>
                </div>
                """, unsafe_allow_html=True)

                fl_col1, fl_col2, fl_col3 = st.columns(3)
                with fl_col1:
                    if st.button("Create Flash Sale (20% Off)", use_container_width=True, type="primary"):
                        st.success("Flash sale created! Discounted price published to buyer marketplace.")
                with fl_col2:
                    if st.button("Prioritize Delivery", use_container_width=True):
                        st.info("Prioritized dispatch request sent to cold-chain logistics team.")
                with fl_col3:
                    if st.button("Remove Listing", use_container_width=True):
                        st.warning("Listing removed from active inventory.")

            with dash_right:
                # RIGHT CARD 1: Market Demand Insight
                st.markdown(f"""
                <div style="background: #faf5ff; border-radius: 12px; padding: 16px; border: 1px solid #e9d5ff; margin-bottom: 20px;">
                    <h4 style="margin: 0; color: #7e22ce;"> Market Demand Insight</h4>
                    <p style="color: #6b21a8; font-size: 0.88rem; margin-top: 8px; line-height: 1.4;">
                        There is a high demand for <b>Onions & Tomatoes</b> within a 15km radius of {district}.
                        12 restaurants have posted demands in the last 4 hours.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View Demand Matches ->", use_container_width=True):
                    st.session_state.active_nav = "Seller Supply Pooling"
                    st.rerun()

                # RIGHT CARD 2: Live Incoming Orders
                st.markdown(f"""
                <div style="background: white; border-radius: 12px; padding: 16px; border: 1px solid #cbd5e1; margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin: 0; color: #0f172a;">📦 Received Orders</h4>
                        <span style="background: #fef3c7; color: #b45309; padding: 3px 8px; border-radius: 10px; font-weight: 700; font-size: 0.78rem;">{len(my_pending_orders)} Pending</span>
                    </div>
                    <div style="margin-top: 8px; display:flex; gap: 6px; font-size: 0.78rem;">
                        <span style="background: #f1f5f9; color: #334155; padding: 2px 6px; border-radius: 6px; font-weight: 600;">{len(my_orders)} Total</span>
                        <span style="background: #ede9fe; color: #6d28d9; padding: 2px 6px; border-radius: 6px; font-weight: 600;">{len(my_pooled_orders)} Pooled</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if my_orders:
                    for o_item in my_orders[-4:]:
                        o_id = o_item.get("id", "ORD")
                        o_crop = o_item.get("crop", "Produce")
                        o_qty = float(o_item.get("quantity_kg", 0))
                        o_amt = float(o_item.get("total_amount", 0) or (o_qty * float(o_item.get("price_per_kg", 0))))
                        o_stat = str(o_item.get("status", "PENDING SELLER CONFIRMATION"))
                        is_p = o_item.get("is_pooled", False)
                        b_name = o_item.get("buyer_name", "Buyer")

                        stat_color = "#d97706" if "PENDING" in o_stat else "#15803d"
                        stat_bg = "#fef3c7" if "PENDING" in o_stat else "#dcfce7"
                        pool_html = '<span style="background:#ede9fe; color:#6d28d9; padding:1px 5px; border-radius:4px; font-size:0.7rem; font-weight:bold; margin-left:4px;">POOLED</span>' if is_p else ''

                        with st.container():
                            st.markdown(f"""
                            <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; margin-bottom: 6px; font-size: 0.85rem;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <div><b>#{o_id}</b> — {o_crop}{pool_html}<br><small style="color:#64748b;">{o_qty:.0f} kg • ₹{o_amt:,.0f} • Buyer: {b_name}</small></div>
                                    <span style="background:{stat_bg}; color:{stat_color}; padding:2px 8px; border-radius:8px; font-weight:bold; font-size:0.72rem;">{"Pending" if "PENDING" in o_stat else "Confirmed"}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            if "PENDING" in o_stat:
                                if st.button(f"✅ Confirm #{o_id}", key=f"btn_quick_conf_{o_id}", type="primary", use_container_width=True):
                                    veh_info = allocate_vehicle_for_order(o_item.get("district", district))
                                    o_item["status"] = "CONFIRMED & VEHICLE ALLOTTED"
                                    o_item["vehicle_reg"] = veh_info.get("vehicle_reg", "TN 67 AD 4521")
                                    o_item["driver_name"] = veh_info.get("driver_name", "Sundaram T.")
                                    o_item["driver_phone"] = veh_info.get("driver_phone", "9840077665")
                                    save_all_orders(st.session_state.placed_orders)
                                    st.success(f"Order #{o_id} Confirmed! Vehicle {o_item['vehicle_reg']} allotted.")
                                    st.rerun()
                else:
                    st.caption("No orders received yet. Active listings will receive orders here.")

                if st.button("📋 View All Received Orders & Fulfillment ->", use_container_width=True, key="btn_dash_to_received_orders"):
                    st.session_state.active_nav = "Seller Received Orders"
                    st.rerun()


    elif nav == "Farm Sensor Monitoring":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 22px 26px; border-radius: 16px; color: white; margin-bottom: 24px; box-shadow: 0 10px 15px -3px rgba(16,185,129,0.2);">
            <h1 style="margin: 0; font-size: 2.1rem; color: white; display: flex; align-items: center; gap: 12px;">
                 Farm Sensor Monitoring
            </h1>
            <p style="margin: 6px 0 0 0; font-size: 1.05rem; opacity: 0.95;">
                Monitor your farm conditions in real time using connected sensors.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Fetch current live sensor data ──
        sensor_data = fetch_sensor_data()
        moisture = sensor_data.get("soil_moisture", 68.0)
        humidity = sensor_data.get("humidity", 72.0)
        temp = sensor_data.get("temperature", 29.0)
        device_status = sensor_data.get("device_status", "connected")
        timestamp = sensor_data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        device_id = sensor_data.get("device_id", "FARM-001")
        logs = sensor_data.get("logs", [])

        # ── Status calculations ──
        # Soil Moisture: Low (<30%), Normal (30-70%), High (>70%)
        if moisture < 30.0:
            moist_status, moist_badge = "Low", "Low"
        elif moisture <= 70.0:
            moist_status, moist_badge = "Normal", "Normal"
        else:
            moist_status, moist_badge = "High", "High"

        # Humidity: Low (<40%), Normal (40-80%), High (>80%)
        if humidity < 40.0:
            humid_status, humid_badge = "Low", "Low"
        elif humidity <= 80.0:
            humid_status, humid_badge = "Normal", "Normal"
        else:
            humid_status, humid_badge = "High", "High"

        # Temperature: Low (<18°C), Normal (18-35°C), High (>35°C)
        if temp < 18.0:
            temp_status, temp_badge = "Low", "Low"
        elif temp <= 35.0:
            temp_status, temp_badge = "Normal", "Normal"
        else:
            temp_status, temp_badge = "High", "High"

        # ── 1. 3 MAIN SENSOR CARDS ──
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div style="background: white; border-radius: 14px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size: 1.1rem; font-weight: 700; color: #15803d;">[Moisture]</span>
                    <span style="font-weight: 700; font-size: 0.85rem; padding: 4px 10px; border-radius: 20px; background: {'#fee2e2; color: #dc2626' if moist_status == 'Low' else '#dcfce7; color: #15803d' if moist_status == 'Normal' else '#fef3c7; color: #d97706'};">
                        {moist_badge}
                    </span>
                </div>
                <div style="margin-top: 12px; font-size: 0.9rem; color: #64748b; font-weight: 600;">Soil Moisture</div>
                <div style="font-size: 2.3rem; font-weight: 800; color: #0f172a; margin-top: 2px;">{moisture:.0f}%</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">Status: <b>{moist_status}</b></div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div style="background: white; border-radius: 14px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size: 1.1rem; font-weight: 700; color: #0284c7;">[Humidity]</span>
                    <span style="font-weight: 700; font-size: 0.85rem; padding: 4px 10px; border-radius: 20px; background: {'#fee2e2; color: #dc2626' if humid_status == 'Low' else '#dcfce7; color: #15803d' if humid_status == 'Normal' else '#fef3c7; color: #d97706'};">
                        {humid_badge}
                    </span>
                </div>
                <div style="margin-top: 12px; font-size: 0.9rem; color: #64748b; font-weight: 600;">Humidity</div>
                <div style="font-size: 2.3rem; font-weight: 800; color: #0f172a; margin-top: 2px;">{humidity:.0f}%</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">Status: <b>{humid_status}</b></div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div style="background: white; border-radius: 14px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size: 1.1rem; font-weight: 700; color: #ea580c;">[Temperature]</span>
                    <span style="font-weight: 700; font-size: 0.85rem; padding: 4px 10px; border-radius: 20px; background: {'#fee2e2; color: #dc2626' if temp_status == 'High' else '#dcfce7; color: #15803d' if temp_status == 'Normal' else '#e0f2fe; color: #0284c7'};">
                        {temp_badge}
                    </span>
                </div>
                <div style="margin-top: 12px; font-size: 0.9rem; color: #64748b; font-weight: 600;">Temperature</div>
                <div style="font-size: 2.3rem; font-weight: 800; color: #0f172a; margin-top: 2px;">{temp:.0f}°C</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">Status: <b>{temp_status}</b></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 2. HARDWARE CONNECTION & FARM INFORMATION SECTION (2 Columns) ──
        col_hw, col_farm = st.columns([1, 1])

        with col_hw:
            is_conn = (device_status == "connected")
            status_indicator = "Connected" if is_conn else "Disconnected"
            status_bg = "#dcfce7" if is_conn else "#fee2e2"
            status_color = "#15803d" if is_conn else "#dc2626"

            st.markdown(f"""
            <div style="background: white; border-radius: 14px; padding: 22px; border: 1px solid #e2e8f0; height: 100%;">
                <h3 style="margin: 0 0 14px 0; color: #0f172a; font-size: 1.15rem; display: flex; align-items: center; gap: 8px;">
                     Hardware Connection Status
                </h3>
                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 0.92rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;">
                        <span style="color: #64748b;">Device Status:</span>
                        <span style="font-weight: 700; background: {status_bg}; color: {status_color}; padding: 4px 12px; border-radius: 20px;">
                            {status_indicator}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;">
                        <span style="color: #64748b;">Last Data Received:</span>
                        <span style="font-weight: 600; color: #0f172a;">{timestamp}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;">
                        <span style="color: #64748b;">Device ID:</span>
                        <span style="font-weight: 700; color: #059669; font-family: monospace;">{device_id}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #64748b;">Sensor Status:</span>
                        <span style="font-weight: 600; color: #16a34a;">Operational (DHT11 + Moisture)</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_farm:
            sel_crop_name = st.session_state.selected_crop or "Tomato"
            st.markdown(f"""
            <div style="background: white; border-radius: 14px; padding: 22px; border: 1px solid #e2e8f0; height: 100%;">
                <h3 style="margin: 0 0 14px 0; color: #0f172a; font-size: 1.15rem; display: flex; align-items: center; gap: 8px;">
                     Farm Information
                </h3>
                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 0.92rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;">
                        <span style="color: #64748b;">Farm Name:</span>
                        <span style="font-weight: 700; color: #0f172a;">Green Valley Farm</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;">
                        <span style="color: #64748b;">Crop:</span>
                        <span style="font-weight: 700; color: #0284c7;">{sel_crop_name}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;">
                        <span style="color: #64748b;">Location:</span>
                        <span style="font-weight: 600; color: #0f172a;">Tamil Nadu ({district})</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #64748b;">Sensor Device ID:</span>
                        <span style="font-weight: 700; color: #059669; font-family: monospace;">{device_id}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 3. SMART ALERTS & RECOMMENDATIONS SECTION ──
        st.markdown("### Alerts & Recommendations")
        alert_boxes = []

        if moisture < 30.0:
            alert_boxes.append(("warning", "Soil moisture is low. Irrigation may be required."))
        if temp > 35.0:
            alert_boxes.append(("warning", "Temperature is high. Monitor the crop condition."))
        if 40.0 <= humidity <= 80.0:
            alert_boxes.append(("info", "Humidity level is normal."))
        if moisture >= 30.0 and temp <= 35.0 and 40.0 <= humidity <= 80.0:
            alert_boxes.append(("success", "All sensor conditions are within the normal range."))

        for alert_type, alert_msg in alert_boxes:
            if alert_type == "warning":
                st.warning(f" {alert_msg}")
            elif alert_type == "info":
                st.info(f" {alert_msg}")
            else:
                st.success(f" {alert_msg}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 4. SENSOR HISTORY GRAPH SECTION ──
        st.markdown("### Sensor History")
        filter_horizon = st.radio("Time Horizon", ["Today", "7 Days", "30 Days"], horizontal=True, key="sensor_history_horizon")

        # Generate / prepare history series based on filter
        # random and datetime are imported at the top of the file
        now = datetime.datetime.now()
        
        if filter_horizon == "Today":
            n_points = 12
        elif filter_horizon == "7 Days":
            n_points = 14
        else:
            n_points = 30

        history_rows = []
        if logs and len(logs) > 3:
            for l in reversed(logs[:30]):
                history_rows.append({
                    "Timestamp": l.get("timestamp", now.strftime("%Y-%m-%d %H:%M")),
                    "Soil Moisture (%)": float(l.get("moisture", 68.0)),
                    "Humidity (%)": float(l.get("humidity", 72.0)),
                    "Temperature (°C)": float(l.get("temperature", 29.0))
                })
        else:
            for i in range(n_points, 0, -1):
                t_stamp = (now - datetime.timedelta(hours=i*2 if filter_horizon == "Today" else i*12 if filter_horizon == "7 Days" else i*24)).strftime("%Y-%m-%d %H:%M")
                history_rows.append({
                    "Timestamp": t_stamp,
                    "Soil Moisture (%)": round(max(20.0, min(85.0, moisture + (i%5 - 2)*3.5)), 1),
                    "Humidity (%)": round(max(30.0, min(95.0, humidity + (i%4 - 2)*2.8)), 1),
                    "Temperature (°C)": round(max(15.0, min(42.0, temp + (i%6 - 3)*1.5)), 1)
                })

        df_hist = pd.DataFrame(history_rows)

        fig_sensor = go.Figure()
        fig_sensor.add_trace(go.Scatter(x=df_hist["Timestamp"], y=df_hist["Soil Moisture (%)"], mode="lines+markers", name="Soil Moisture (%)", line=dict(color="#10b981", width=3)))
        fig_sensor.add_trace(go.Scatter(x=df_hist["Timestamp"], y=df_hist["Humidity (%)"], mode="lines+markers", name="Humidity (%)", line=dict(color="#0284c7", width=3)))
        fig_sensor.add_trace(go.Scatter(x=df_hist["Timestamp"], y=df_hist["Temperature (°C)"], mode="lines+markers", name="Temperature (°C)", line=dict(color="#f59e0b", width=3)))
        
        fig_sensor.update_layout(
            title=f"Live IoT Telemetry Trends ({filter_horizon})",
            xaxis_title="Time",
            yaxis_title="Sensor Units",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            height=380,
            template="plotly_white"
        )
        st.plotly_chart(fig_sensor, use_container_width=True)

        st.markdown("---")

        # ── 5. HARDWARE INTEGRATION SIMULATOR & ESP32 ARDUINO CODE EXPANDER ──
        with st.expander("Real Hardware Connection & ESP32 Code Guide (For Tomorrow's Hardware Setup)"):
            st.markdown("""
            #### How to Connect ESP32 Hardware to AgriSmart TN:
            1. Flash the C++ Arduino code below onto your **ESP32 Microcontroller**.
            2. Connect your **DHT11 / DHT22** (Temperature & Humidity) and **Capacitive Soil Moisture Sensor** to GPIO Pins.
            3. Update the Wi-Fi SSID, Password, and your Server IP address.
            4. The ESP32 will automatically `POST` JSON telemetry data to `/api/sensor/telemetry` or `/api/sensor-data` every 15 seconds!
            """)

            st.code("""
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_COMPUTER_IP:8000/api/sensor/telemetry";

#define DHTPIN 4
#define DHTTYPE DHT11
#define SOIL_PIN 34

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\\nWiFi Connected!");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    float h = dht.readHumidity();
    float t = dht.readTemperature();
    int soilRaw = analogRead(SOIL_PIN);
    float moisture = map(soilRaw, 4095, 0, 0, 100);

    if (isnan(h) || isnan(t)) {
      t = 29.0; h = 72.0;
    }

    String jsonPayload = "{\\\"device_id\\\":\\\"FARM-001\\\",\\\"district\\\":\\\"Coimbatore\\\",\\\"moisture\\\":" + String(moisture) + ",\\\"temperature\\\":" + String(t) + ",\\\"humidity\\\":" + String(h) + "}";

    int httpResponseCode = http.POST(jsonPayload);
    Serial.print("HTTP Response Code: ");
    Serial.println(httpResponseCode);
    http.end();
  }
  delay(15000);
}
            """, language="cpp")

            st.markdown("##### Quick Hardware Simulation Pulse")
            st.caption("Click below to simulate hardware sending fresh sensor telemetry values:")
            sim_col1, sim_col2, sim_col3 = st.columns(3)
            with sim_col1:
                if st.button("Send Normal Telemetry (68% Moist, 72% Hum, 29°C)", use_container_width=True):
                    try:
                        from db_store import save_sensor_log
                        save_sensor_log({
                            "id": f"SNS-{random.randint(1000, 9999)}",
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "device_id": "FARM-001",
                            "district": district,
                            "moisture": 68.0,
                            "temperature": 29.0,
                            "humidity": 72.0,
                            "alert_level": "NORMAL",
                            "status_msg": "Optimal crop growth conditions."
                        })
                        st.success("Normal hardware reading injected!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Simulation error: {e}")

            with sim_col2:
                if st.button("Send Low Moisture Reading (22% Moist)", use_container_width=True):
                    try:
                        from db_store import save_sensor_log
                        save_sensor_log({
                            "id": f"SNS-{random.randint(1000, 9999)}",
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "device_id": "FARM-001",
                            "district": district,
                            "moisture": 22.0,
                            "temperature": 34.0,
                            "humidity": 45.0,
                            "alert_level": "LOW_MOISTURE",
                            "status_msg": "ALERT: Soil moisture critically low (22% < 30%). Immediate irrigation needed!"
                        })
                        st.warning("Low moisture alert injected!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Simulation error: {e}")

            with sim_col3:
                if st.button("Send High Temp Reading (38°C)", use_container_width=True):
                    try:
                        from db_store import save_sensor_log
                        save_sensor_log({
                            "id": f"SNS-{random.randint(1000, 9999)}",
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "device_id": "FARM-001",
                            "district": district,
                            "moisture": 48.0,
                            "temperature": 38.0,
                            "humidity": 35.0,
                            "alert_level": "HIGH_TEMP",
                            "status_msg": "ALERT: High ambient temperature (>35°C) & low humidity (<40%)."
                        })
                        st.error("High temperature alert injected!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Simulation error: {e}")


    elif nav == "Smart Crop Finder":


        st.subheader("Smart Crop Filtering & Recommendation Engine")
        st.caption("AI-driven crop suitability matching based on your district's soil, climate, water availability & market ROI.")

        f1, f2, f3, f4 = st.columns(4)
        with f1:
            filter_soil = st.checkbox(f"Filter for my soil ({soil_type})", value=True)
        with f2:
            filter_irr = st.checkbox(f"Filter for my irrigation source", value=True)
        with f3:
            season_sel = st.selectbox("Growing Season", ["All", "Kharif (Monsoon)", "Rabi (Winter)", "Zaid (Summer)", "Year-round"], index=0)
        with f4:
            min_prof = st.slider("Min Est. Profit / Acre (₹)", 0, 100000, 20000, step=5000)

        s_soil = soil_type if filter_soil else ""
        s_irr = irrigation if filter_irr else ""

        rec_crops = fetch_smart_crops(district, land_acres, s_soil, s_irr, season_sel, min_prof)

        st.markdown(f"### Recommended Crops for {land_acres} Acres in {district}")

        if not rec_crops:
            st.warning("No crops match your strict filter settings. Try lowering the minimum profit or unchecking soil filters.")
        else:
            for idx, crop_item in enumerate(rec_crops):
                score = crop_item.get("suitability_score", 80)
                badge_cls = "badge-highly-suitable" if score >= 90 else "badge-suitable" if score >= 75 else "badge-moderate"

                with st.container():
                    c_head, c_btn = st.columns([3, 1])
                    with c_head:
                        st.markdown(f"""
                        <div style="display:flex; align-items:center; gap:12px;">
                            <span style="font-size:2.2rem;">{crop_item.get('emoji','')}</span>
                            <div>
                                <h3 style="margin:0; color:#0f172a;">{crop_item['crop']}</h3>
                                <span class="{badge_cls}">Match Score: {score}%</span>
                                <span style="color:#64748b; font-size:0.88rem; margin-left:10px;">Season: {crop_item.get('season','General')}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_btn:
                        if st.button(f"Plan for {crop_item['crop']}", key=f"sel_crop_{idx}", use_container_width=True):
                            st.session_state.selected_crop = crop_item['crop']
                            st.session_state.active_nav = "Seed & Input Planner"
                            st.rerun()

                    m1, m2, m3, m4 = st.columns(4)
                    with m1: st.metric("Est. Yield / Acre", f"{crop_item['yield_per_acre']} Tons")
                    with m2: st.metric("Profit / Acre", fmt_inr(crop_item['profit_per_acre']))
                    with m3: st.metric(f"Total Net Profit ({land_acres} Acres)", fmt_inr(crop_item['total_profit']))
                    with m4: st.metric("Market Risk", crop_item.get('market_risk', 'Medium'))

                    st.markdown("**Why this crop is suitable:**")
                    reasons = crop_item.get("match_reasons", [])
                    st.markdown(" • " + "\n • ".join(reasons))
                    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 2: SEED & INPUT PLANNER
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Seed & Input Planner":
        st.subheader("Seed & Agronomic Input Requirements Planner")
        st.caption(f"Exact seed quantity, spacing, seed treatment & sowing schedule for {land_acres} Acres.")

        sel_c = st.selectbox("Select Crop for Seed Planning", list(CROP_DB.keys()),
                             index=list(CROP_DB.keys()).index(st.session_state.selected_crop) if st.session_state.selected_crop in CROP_DB else 0)

        if sel_c != st.session_state.selected_crop:
            st.session_state.selected_crop = sel_c

        seed_plan = fetch_seed_planner(sel_c, land_acres)

        if seed_plan:
            st.markdown(f"### Seed Requirement Summary — {sel_c}")

            s1, s2, s3, s4 = st.columns(4)
            with s1: st.metric(f"Total Seed Needed ({land_acres} Acres)", f"{seed_plan.get('total_seed_kg',0)} {seed_plan.get('unit','kg')}")
            with s2: st.metric("Seed Rate per Acre", f"{seed_plan.get('seed_rate_per_acre','--')}")
            with s3: st.metric("Method", seed_plan.get("sowing_method","--"))
            with s4: st.metric("Est. Seed Cost", fmt_inr(seed_plan.get("est_seed_cost",0)))

            st.markdown("---")

            sp1, sp2 = st.columns(2)
            with sp1:
                st.markdown("####Spacing & Nursery Specifications")
                st.info(f"**Optimal Spacing:** {seed_plan.get('spacing','')}")
                st.info(f"**Nursery Duration:** {seed_plan.get('nursery_duration_days', 0)} days before transplanting")
                st.info(f"**Expected Germination Rate:** {seed_plan.get('germination_rate','')}")
                st.info(f"**Ideal Sowing Months:** {seed_plan.get('sowing_window','')}")

            with sp2:
                st.markdown("####Mandatory Seed Treatment Protocol")
                st.warning(f"{seed_plan.get('seed_treatment','')}")
                st.success(f"**Agronomic Advice:** {seed_plan.get('advice','')}")

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 3: ACRE-BASED PROFIT & COST BREAKDOWN
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Acre-based Profit & Cost":
        st.subheader("Acre-Based Financial Estimator & Cost Breakdown")
        st.caption("Complete income statement, cost per acre, gross revenue & net profit scaled dynamically.")

        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            c_crop = st.selectbox("Select Crop", list(CROP_DB.keys()),
                                  index=list(CROP_DB.keys()).index(st.session_state.selected_crop) if st.session_state.selected_crop in CROP_DB else 0,
                                  key="plan_crop_sel")
        with pc2:
            c_acres = st.number_input("Land Size (Acres)", min_value=0.25, max_value=500.0, value=max(0.25, float(land_acres)), step=0.5)
        with pc3:
            c_factor = st.slider("Yield Performance Factor", 0.7, 1.3, 1.0, 0.05, help="1.0 = Average yield, 1.15 = Best practices yield")

        plan = fetch_crop_plan(c_crop, c_acres, c_factor)

        if plan:
            r1, r2, r3, r4, r5 = st.columns(5)
            with r1: st.metric("Net Profit", fmt_inr(plan['net_profit']))
            with r2: st.metric("Gross Revenue", fmt_inr(plan['gross_revenue']))
            with r3: st.metric("Cultivation Cost", fmt_inr(plan['total_cost']))
            with r4: st.metric("ROI", f"{plan['roi_percent']}%")
            with r5: st.metric("Break-Even Yield", f"{plan['break_even_yield_tons']} Tons")

            st.markdown("---")

            ch1, ch2 = st.columns([1, 1])

            with ch1:
                st.markdown(f"#### Cost Breakdown for {c_acres} Acres")
                costs = plan.get("cost_breakdown", {})
                df_costs = pd.DataFrame([{"Item": k, "Cost (₹)": v} for k, v in costs.items()])

                fig = px.pie(df_costs, values="Cost (₹)", names="Item", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320)
                st.plotly_chart(fig, use_container_width=True)

            with ch2:
                st.markdown("####Per-Acre vs Total Financial Breakdown")
                df_table = pd.DataFrame([
                    {"Metric": "Expected Yield", "Per Acre": f"{plan['yield_per_acre']} Tons", f"Total ({c_acres} Acres)": f"{plan['total_yield_tons']} Tons"},
                    {"Metric": "Cost of Cultivation", "Per Acre": fmt_inr(plan['cost_per_acre']), f"Total ({c_acres} Acres)": fmt_inr(plan['total_cost'])},
                    {"Metric": "Selling Price / Ton", "Per Acre": f"₹{plan['selling_price_per_ton']:,}", f"Total ({c_acres} Acres)": f"₹{plan['selling_price_per_ton']:,}"},
                    {"Metric": "Gross Revenue", "Per Acre": fmt_inr(plan['gross_revenue'] / c_acres), f"Total ({c_acres} Acres)": fmt_inr(plan['gross_revenue'])},
                    {"Metric": "Net Profit", "Per Acre": fmt_inr(plan['profit_per_acre']), f"Total ({c_acres} Acres)": fmt_inr(plan['net_profit'])},
                ])
                st.dataframe(df_table, use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 3B: FEATURE 3 — MACHINE LEARNING CROP YIELD PREDICTOR (scikit-learn)
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "ML Crop Yield Predictor":
        st.subheader(t("ml_yield_title", cur_lang))
        st.caption("Predict harvest yield using trained Random Forest Regressor ML pipeline based on soil pH, rainfall & temperature.")

        ml1, ml2 = st.columns([1, 1])
        with ml1:
            ml_crop = st.selectbox("Select Crop", list(CROP_DB.keys()),
                                   index=list(CROP_DB.keys()).index(st.session_state.selected_crop) if st.session_state.selected_crop in CROP_DB else 0,
                                   key="ml_crop_sel")
            ml_rain = st.slider("Expected Season Rainfall (mm)", 100, 2500, int(dist_info.get("rainfall_mm", 900)), step=50)
            ml_temp = st.slider("Average Season Temperature (°C)", 15.0, 45.0, float(dist_info.get("avg_temp", 29.0)), step=0.5)
            ml_ph = st.slider("Soil pH Level", 4.5, 9.0, float(dist_info.get("soil_ph", 6.5)), step=0.1)
            ml_npk = st.number_input("Nitrogen Input (kg/ha)", min_value=10.0, max_value=300.0, value=80.0, step=10.0)

        with ml2:
            ml_res = fetch_ml_yield(ml_crop, ml_rain, ml_temp, ml_ph, ml_npk)
            if ml_res:
                st.markdown(f"### ML Prediction Results — {crop_t(ml_crop, cur_lang)}")

                y1, y2, y3 = st.columns(3)
                with y1: st.metric("Yield per Hectare", f"{ml_res.get('predicted_yield_ha', 0)} Tonnes")
                with y2: st.metric("Yield per Acre", f"{ml_res.get('predicted_yield_acre', 0)} Tonnes")
                with y3: st.metric(t("confidence_score", cur_lang), f"{ml_res.get('confidence_r2', 0.88)*100:.1f}%")

                st.markdown("---")
                st.markdown("####Feature Importance Breakdown")
                f_imp = ml_res.get("feature_importance", {})
                df_imp = pd.DataFrame([{"Feature": k, "Importance (%)": v} for k, v in f_imp.items()])

                fig_imp = px.bar(df_imp, x="Importance (%)", y="Feature", orientation="h",
                                 color="Importance (%)", color_continuous_scale="Viridis",
                                 title="Machine Learning Factor Influence")
                fig_imp.update_layout(height=260, showlegend=False, margin=dict(t=30, b=10, l=10, r=10))
                st.plotly_chart(fig_imp, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 3C: FEATURE 2 — SOLAR PUMP & PM-KUSUM SUBSIDY ROI CALCULATOR
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Solar Pump & PM-KUSUM ROI":
        st.subheader(t("solar_pump_title", cur_lang))
        st.caption("Calculate exact pump HP capacity, 60% PM-KUSUM state & central subsidy, monthly fuel savings & payback period.")

        sp1, sp2 = st.columns([1, 1])
        with sp1:
            cur_source = st.radio("Current Irrigation Energy Source", ["Diesel", "Grid Electricity"], index=0)
            well_depth = st.slider("Well / Borehole Depth (Feet)", 50, 600, 150, step=25)

        with sp2:
            sp_res = fetch_solar_pump(land_ha, cur_source, well_depth)
            if sp_res:
                st.markdown(f"### Recommended Solar Pump: **{sp_res.get('recommended_pump_hp')} HP**")

                k1, k2, k3 = st.columns(3)
                with k1: st.metric("Total System Cost", fmt_inr(sp_res.get("total_system_cost", 0)))
                with k2: st.metric("PM-KUSUM Subsidy (60%)", fmt_inr(sp_res.get("pm_kusum_subsidy_60pct", 0)))
                with k3: st.metric("Farmer Share (10%)", fmt_inr(sp_res.get("farmer_down_payment_10pct", 0)))

                st.markdown("---")

                k4, k5, k6 = st.columns(3)
                with k4: st.metric("Monthly Savings", fmt_inr(sp_res.get("monthly_savings_inr", 0)))
                with k5: st.metric(t("payback_period", cur_lang), f"{sp_res.get('payback_period_months', 0)} Months")
                with k6: st.metric("Annual CO₂ Saved", f"{sp_res.get('co2_saved_tonnes_yr', 0)} Tonnes")

                st.success(f"**Government Subsidy:** Eligible for 60% direct subsidy under PM-KUSUM Scheme + 30% low-interest bank loan. Net out-of-pocket payment required: **{fmt_inr(sp_res.get('farmer_down_payment_10pct', 0))}**.")

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 4: AI CROP ADVISOR CHAT
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "AI Crop Advisor Chat":
        st.subheader("AI Agricultural Advisor & Farming Guide")
        st.caption(f"Context-aware AI chatbot pre-loaded with your {land_acres} Acre farm details in {district}.")

        # Pre-built query chips
        chip1, chip2, chip3, chip4 = st.columns(4)
        with chip1:
            if st.button("Recommend best crop", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": f"What is the single best crop for my {land_acres} acres in {district}?"})
                st.rerun()
        with chip2:
            if st.button("Fertilizer schedule", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": f"Give me exact NPK fertilizer schedule for {st.session_state.selected_crop} on {land_acres} acres."})
                st.rerun()
        with chip3:
            if st.button("Water management", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": f"How much water does {st.session_state.selected_crop} need and what is the best irrigation method?"})
                st.rerun()
        with chip4:
            if st.button("Applicable subsidies", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": f"What government subsidy schemes can I apply for in {district}?"})
                st.rerun()

        st.markdown("---")

        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # If the last message is from user and needs assistant reply
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing farm context & generating reply..."):
                        reply = fetch_ai_advisor(
                            st.session_state.messages, district, land_ha, farmer_name,
                            st.session_state.api_key, st.session_state.selected_crop, prof
                        )
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        st.markdown(reply)

        user_input = st.chat_input(f"Ask AgriSmart AI anything about farming in {district}...", key="chat_input_box")
        if user_input and user_input.strip():
            st.session_state.messages.append({"role": "user", "content": user_input.strip()})
            st.rerun()

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 5: LIVE WEATHER & CLIMATE RISK
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Live Weather & Climate Risk":
        st.subheader("Live District Weather & Climate Risk Matrix")

        wresult = fetch_weather(district)
        w_risk = fetch_weather_risk(district)

        wdata = wresult.get("live") if wresult else None

        if wdata and "current" in wdata:
            cur = wdata["current"]
            daily = wdata.get("daily", {})

            st.caption(f"LIVE WEATHER — {district}, Tamil Nadu")
            w1, w2, w3, w4, w5 = st.columns(5)
            with w1: st.metric("Temperature", f"{cur.get('temperature_2m','--')}°C")
            with w2: st.metric("Feels Like", f"{cur.get('apparent_temperature','--')}°C")
            with w3: st.metric("Humidity", f"{cur.get('relative_humidity_2m','--')}%")
            with w4: st.metric("Wind Speed", f"{cur.get('wind_speed_10m','--')} km/h")
            with w5: st.metric("Rainfall Today", f"{cur.get('precipitation', 0)} mm")
        else:
            st.info(f"Showing static climate averages for {district}")
            w1, w2, w3, w4 = st.columns(4)
            with w1: st.metric("Avg Temp", f"{dist_info.get('avg_temp', 29)}°C")
            with w2: st.metric("Annual Rain", f"{dist_info.get('rainfall_mm', 900)} mm/yr")
            with w3: st.metric("Humidity", f"{dist_info.get('humidity', 65)}%")
            with w4: st.metric("Soil pH", dist_info.get("soil_ph", 6.5))

        st.markdown("---")
        st.subheader("Extreme Weather Risk Matrix")
        if w_risk:
            rk1, rk2, rk3, rk4 = st.columns(4)
            with rk1: st.metric("Cyclone Risk", w_risk.get("cyclone_risk","--"))
            with rk2: st.metric("Flood Risk", w_risk.get("flood_risk","--"))
            with rk3: st.metric("Drought Risk", w_risk.get("drought_risk","--"))
            with rk4: st.metric("Heatwave Risk", w_risk.get("heat_risk","--"))

            st.markdown("####District Contingency Action Plan")
            for plan in w_risk.get("contingency_plans", []):
                st.info(f"• {plan}")

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 6: PEST AI DIAGNOSTICS
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Pest AI Diagnostics":
        st.subheader("Smart Pest & Crop Disease Diagnostics")
        st.caption("Upload a leaf photo or describe symptoms to receive immediate organic and chemical treatments.")

        p_col1, p_col2 = st.columns([1, 1])
        with p_col1:
            pest_crop = st.selectbox("Crop", list(CROP_DB.keys()), 
                                     index=list(CROP_DB.keys()).index(st.session_state.selected_crop) if st.session_state.selected_crop in CROP_DB else 0)
            pest_symptom = st.text_area("Describe Symptoms (e.g. yellowing leaves, stem borer, brown spots)", placeholder="e.g. Spindle shaped spots with brown margins")
            leaf_file = st.file_uploader("Upload Crop/Leaf Photo (Optional)", type=["jpg","jpeg","png"])
            diag_btn = st.button("Run Diagnostics", use_container_width=True)

        with p_col2:
            if diag_btn or pest_symptom:
                diag = fetch_pest_scanner(pest_crop, pest_symptom, "", st.session_state.api_key)
                if diag:
                    st.success(f"**Diagnosis Result:** {diag.get('diagnosis','Issue Detected')}")
                    st.write(f"**Type:** {diag.get('type','')}")
                    st.write(f"**Root Cause:** {diag.get('cause','')}")
                    st.markdown("---")
                    st.markdown(f"** Organic Remedy:**\n{diag.get('organic_remedy','')}")
                    st.markdown(f"** Chemical Treatment:**\n{diag.get('chemical_treatment','')}")
                    st.markdown(f"** Preventive Steps:**\n{diag.get('prevention','')}")

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 7: CROP LIFECYCLE GANTT
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Crop Lifecycle Gantt":
        st.subheader("Interactive Crop Lifecycle Timeline & Input Schedule")

        t_crop = st.selectbox("Select Crop", list(CROP_DB.keys()),
                              index=list(CROP_DB.keys()).index(st.session_state.selected_crop) if st.session_state.selected_crop in CROP_DB else 0)
        stages = fetch_crop_timeline(t_crop, district)

        if stages:
            df_timeline = pd.DataFrame(stages)
            fig_gantt = px.timeline(df_timeline, x_start="StartDay", x_end="EndDay", y="Stage", color="Stage",
                                    hover_data=["Action","Input"], title=f"Lifecycle Timeline — {t_crop} in {district} (Days from Sowing)")
            fig_gantt.update_yaxes(autorange="reversed")
            fig_gantt.update_layout(template="plotly_white", height=320, showlegend=False)
            st.plotly_chart(fig_gantt, use_container_width=True)

            st.markdown("###Stage-by-Stage Input Checklist")
            for s in stages:
                with st.expander(f"**{s['Stage']}** (Day {s['StartDay']} to Day {s['EndDay']})"):
                    st.write(f"**Key Action:** {s['Action']}")
                    st.write(f"**Required Inputs:** {s['Input']}")

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 8: GOVT SCHEMES & SUBSIDIES
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Govt Schemes & Subsidies":
        st.subheader("Government Subsidy & Scheme Eligibility Finder")

        sc1, sc2 = st.columns(2)
        with sc1:
            farmer_type = st.selectbox("Farmer Category", ["Small/Marginal (<2 ha)", "Medium/Large (>2 ha)", "Women Farmer / SC/ST"])
        with sc2:
            scheme_cat = st.selectbox("Scheme Category", ["All", "Direct Income Support", "Irrigation Subsidy", "Crop Risk Insurance", "Low-Interest Credit", "Input Subsidy", "Farm Mechanization", "Direct Marketing"])

        schemes_list = fetch_schemes(farmer_type, land_ha, scheme_cat)
        st.caption(f"Found {len(schemes_list)} eligible government schemes for your farm profile")

        for sch in schemes_list:
            with st.expander(f"**{sch['name']}** — {sch['category']}"):
                st.write(f"**Benefit:** {sch['benefit']}")
                st.write(f"**Eligibility:** {sch['eligibility']}")
                st.write(f"**Required Documents:** {', '.join(sch['docs'])}")
                st.markdown(f"[Official Application Portal]({sch['link']})")

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 9: MANDI PRICE TRACKER
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Mandi Price Tracker":
        st.subheader("Multi-Mandi Price Tracker & Transport Profitability Engine")

        m_crop = st.selectbox("Select Crop", list(CROP_DB.keys()),
                               index=list(CROP_DB.keys()).index(st.session_state.selected_crop) if st.session_state.selected_crop in CROP_DB else 0)
        mandis = fetch_mandi_compare(m_crop, district, land_ha)

        if mandis:
            df_mandi = pd.DataFrame(mandis)
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(x=df_mandi["mandi"], y=df_mandi["net_profit"], name="Net Profit (₹)", marker_color="#10b981"))
            fig_m.add_trace(go.Bar(x=df_mandi["mandi"], y=df_mandi["transport_cost"], name="Transport Cost (₹)", marker_color="#ef4444"))
            fig_m.update_layout(barmode="group", title=f"Net Profit vs Transport Cost across Mandis ({m_crop} on {land_acres} Acres)", template="plotly_white", height=360)
            st.plotly_chart(fig_m, use_container_width=True)

            st.dataframe(df_mandi[["mandi", "distance_km", "price_per_tonne", "gross_revenue", "transport_cost", "net_profit", "roi"]].rename(columns={
                "mandi": "Mandi Market", "distance_km": "Distance (km)", "price_per_tonne": "Price (₹/t)", "gross_revenue": "Gross Revenue", "transport_cost": "Transport Cost", "net_profit": "Net Profit", "roi": "ROI %"
            }), use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 10: MACHINERY & LABOR ESTIMATOR
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Machinery & Labor Estimator":
        st.subheader("Equipment Rental & Labor Cost Estimator")

        e_crop = st.selectbox("Select Crop", list(CROP_DB.keys()),
                              index=list(CROP_DB.keys()).index(st.session_state.selected_crop) if st.session_state.selected_crop in CROP_DB else 0)
        eq = fetch_equipment_calc(e_crop, land_ha)

        if eq:
            eq1, eq2, eq3, eq4 = st.columns(4)
            with eq1: st.metric("Tractor Hours", f"{eq.get('tractor_hrs',0)} hrs", f"₹{eq.get('tractor_cost',0):,}")
            with eq2: st.metric("Harvester Usage", f"{land_acres} acres", f"₹{eq.get('harvester_cost',0):,}")
            with eq3: st.metric("Drone Sprays", f"{eq.get('drone_sprays',0)} sprays", f"₹{eq.get('drone_cost',0):,}")
            with eq4: st.metric("Labor Days Needed", f"{eq.get('total_labor_days',0)} days", f"₹{eq.get('total_labor_cost',0):,}")

            st.markdown("---")
            st.success(f"**Total Mechanization Cost:** ₹{eq.get('total_mech_cost',0):,}")
            st.success(f"**Total Labor Cost:** ₹{eq.get('total_labor_cost',0):,}")
            st.info("Rates benchmarked against Tamil Nadu Custom Hiring Centres (CHC) subsidised tariffs.")

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 11: SOIL HEALTH & IRRIGATION
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Soil Health & Irrigation":
        st.subheader("Soil Health & Precision Irrigation Guide")

        s_crop = st.selectbox("Select Crop", list(CROP_DB.keys()),
                              index=list(CROP_DB.keys()).index(st.session_state.selected_crop) if st.session_state.selected_crop in CROP_DB else 0)

        sr = fetch_soil_info(district, s_crop)
        ir = fetch_irrigation_info(district, land_ha, s_crop)

        t1, t2 = st.tabs(["Soil & NPK Schedule", "Irrigation Plan"])

        with t1:
            if sr:
                st.markdown(f"**Soil Profile:** {sr.get('profile','')}")
                st.markdown(f"**Amendment:** {sr.get('amendment','')}")
                st.markdown(f"**pH Advice:** {sr.get('ph_advice','')}")
                st.markdown("---")
                st.markdown("####NPK Fertilizer Schedule")
                st.write(f"**Basal dose:** {sr.get('npk_base','')}")
                st.write(f"**Top dressing:** {sr.get('npk_top','')}")
                st.write(f"**Micronutrients:** {sr.get('micro','')}")
                st.write(f"**Organic inputs:** {sr.get('organic','')}")

        with t2:
            if ir:
                ir1, ir2, ir3, ir4 = st.columns(4)
                with ir1: st.metric("Water Need", ir.get("water","--"))
                with ir2: st.metric("Frequency", ir.get("freq","--"))
                with ir3: st.metric("Min Water", f"{ir.get('total_min',0)} mm")
                with ir4: st.metric("Max Water", f"{ir.get('total_max',0)} mm")
                st.info(ir.get("rainfed",""))
                st.markdown(f"**Best Method:** {ir.get('method','')}")
                st.markdown(f"**Installation Detail:** {ir.get('method_detail','')}")
                st.markdown(f"**Est. Irrigation Cost:** ₹{ir.get('irr_cost',0):,.0f}")

    # ─────────────────────────────────────────────────────────────────────────────
    # VIEW 12: FARM SUMMARY & PDF EXPORT
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Farm Summary & PDF Export":
        st.subheader("Farm Financial Summary & Bank Loan PDF Report")

        sel_crop = st.session_state.selected_crop
        p = fetch_profit(sel_crop, land_ha)

        if p:
            rr1, rr2, rr3, rr4 = st.columns(4)
            with rr1: st.metric("Selected Crop", sel_crop)
            with rr2: st.metric("Est. Net Profit", fmt_inr(p["profit"]))
            with rr3: st.metric("ROI", f"{p['roi']}%")
            with rr4: st.metric("Total Production", f"{p['total_yield']} Tons")

        st.markdown("---")

        pdf_bytes = fetch_pdf_report(district, farmer_name, land_ha, sel_crop)
        if pdf_bytes:
            st.download_button(
                label="Download Bank Loan Farm Advisory PDF Report",
                data=pdf_bytes,
                file_name=f"AgriSmart_Farm_Report_{district}_{sel_crop}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("###Comprehensive AI Conclusion Report")

        if st.session_state.conclusion_text:
            st.markdown(st.session_state.conclusion_text)
        else:
            if st.button("Generate AI Conclusion Report", use_container_width=True):
                with st.spinner("Generating personalized farm report..."):
                    report = fetch_ai_conclusion(district, land_ha, farmer_name, sel_crop, st.session_state.api_key)
                    st.session_state.conclusion_text = report
                    st.rerun()

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 13: FRESHNESS & SPOILAGE RISK MONITOR  [FARMER ONLY]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Freshness & Spoilage Monitor":
        st.subheader("Produce Freshness Decay & Automated Flash Sale Engine")
        st.caption("Real-time shelf life monitoring, spoilage risk detection & automated flash sale discount generation.")

        # ── STRICT AUTH GUARD: only Farmer / Seller can post listings ──
        if st.session_state.user_role != "Farmer / Seller":
            st.error("Access Denied — Only a logged-in **Farmer / Seller** can post produce listings. Please log in as a Farmer.")
            st.stop()

        fc1, fc2 = st.columns([1, 1])
        with fc1:
            sel_f_crop = st.selectbox("Crop Inventory Item", list(CROP_SHELF_LIFE.keys()), index=0)
            hrs_harvested = st.slider("Hours Elapsed Since Harvest", 0, 168, 24, step=4)
            price_input = st.number_input("Your Asking Price (₹ per kg)",
                                          min_value=1.0, max_value=500.0,
                                          value=round(CROP_DB.get(sel_f_crop, {}).get("price", 20000) / 1000.0, 1),
                                          step=0.5)
            qty_input = st.number_input("Quantity Available (kg)",
                                        min_value=10.0, max_value=50000.0,
                                        value=round(land_acres * 150.0, 0),
                                        step=10.0)
            post_supply = st.button("Post My Listing to Marketplace", use_container_width=True, type="primary")

        with fc2:
            fresh_data = calc_freshness_decay(sel_f_crop, hrs_harvested)
            st.markdown(f"### Freshness Health Status: <span style='color:{fresh_data['risk_color']};'>{fresh_data['remaining_freshness_pct']}%</span>", unsafe_allow_html=True)

            fm1, fm2, fm3 = st.columns(3)
            with fm1: st.metric("Risk Level", fresh_data['risk_level'])
            with fm2: st.metric("Ideal Storage Temp", f"{fresh_data['ideal_temp_c']}°C")
            with fm3: st.metric("Flash Sale Discount", f"{fresh_data['suggested_flash_discount_pct']}%")

            if fresh_data['suggested_flash_discount_pct'] > 0:
                st.warning(f" High spoilage risk detected! Automated flash sale discount of **{fresh_data['suggested_flash_discount_pct']}%** recommended to prevent post-harvest loss.")

        if post_supply:
            # ── Double-check: logged-in farmer name must match ──
            if not farmer_name or farmer_name == "Farmer":
                st.error("Please complete your Farmer profile before posting a listing.")
            else:
                new_id = f"SUP-{len(st.session_state.supply_listings) + 101}"
                new_listing = {
                    "id": new_id,
                    "farmer_name": farmer_name,  # actual logged-in farmer
                    "phone": prof.get("phone_email", ""),
                    "crop": sel_f_crop,
                    "quantity_kg": qty_input,
                    "unit": "kg",
                    "price_per_kg": price_input,
                    "district": district,
                    "area": f"{district} Farm",
                    "harvest_hours_ago": hrs_harvested,
                    "credit_score": 780,
                    "status": "ACTIVE",
                    "posted_by_phone": prof.get("phone_email", "")  # ownership tag
                }
                st.session_state.supply_listings.append(new_listing)
                save_listing(new_listing)   #  Write to db/listings.json
                st.success(f" **{farmer_name}** — Your **{sel_f_crop}** listing ({new_id}) has been posted to the Harvestline Marketplace! Buyers can now find and order from you.")
                st.balloons()

        st.markdown("---")
        st.markdown(f"####  Your Active Listings (Posted by {farmer_name})")
        # Show only THIS farmer's own listings
        my_listings = [s for s in st.session_state.supply_listings
                       if s.get("posted_by_phone") == prof.get("phone_email", "")]
        if my_listings:
            st.dataframe(pd.DataFrame(my_listings), use_container_width=True, hide_index=True)
        else:
            st.info("You have not posted any listings yet. Use the form above to post your first produce listing.")

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 14: ALTERNATIVE CREDIT TRUST PROFILE
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Alternative Credit Trust Profile":
        st.subheader("Behavioral Credit Trust Profile (300–850)")
        st.caption("Alternative credit scoring based on order fulfillment rate, on-time delivery track record, and dispute-free history.")

        cr1, cr2 = st.columns([1, 1])
        with cr1:
            ful_orders = st.slider("Total Fulfilled Orders", 1, 50, 16)
            ontime_r = st.slider("On-Time Delivery Rate (%)", 50, 100, 96)
            dispute_r = st.slider("Dispute-Free Rate (%)", 50, 100, 98)

        with cr2:
            cred = calc_farmer_credit_score(ful_orders, ontime_r, dispute_r)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 20px; border-radius: 16px; color: white; text-align: center;">
                <h4 style="margin:0; opacity:0.9;">FARMER TRUST CREDIT SCORE</h4>
                <h1 style="font-size: 3.5rem; margin: 10px 0; color: #ecfdf5;">{cred['credit_score']}</h1>
                <p style="font-size: 1.1rem; font-weight:600; margin:0;">Tier: {cred['tier_label']}</p>
            </div>
            """, unsafe_allow_html=True)

            cm1, cm2 = st.columns(2)
            with cm1: st.metric("Pre-Approved Microloan", fmt_inr(cred['preapproved_microloan_limit_inr']))
            with cm2: st.metric("Order Success Rate", f"{cred['dispute_free_rate_pct']}%")

        st.info("Your credit trust score is shared with buyers and partner banks (NABARD, SBI Agri) for instant collateral-free input financing.")

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 15: BUYER AI DEMAND NLP PARSER  [BUYER ONLY]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "AI Demand NLP Parser":
        st.subheader("AI Natural Language Demand Ingestion Engine")
        st.caption("Parse unstructured text messages or voice transcriptions into structured buyer demand parameters.")

        # ── STRICT AUTH GUARD: only Buyer / Wholesaler can submit demands ──
        if not is_buyer_user():
            st.error("Access Denied — Only a logged-in **Buyer / Wholesaler** can submit demand requests. Please log in as a Buyer.")
            st.stop()

        bp1, bp2 = st.columns([1, 1])
        with bp1:
            raw_input = st.text_area("Buyer Demand Request (Natural Text)",
                                     value=f"Need 600 kg fresh tomatoes in {district} around Rs.22/kg by tomorrow morning.",
                                     height=120,
                                     placeholder="e.g. Need 500 kg fresh tomatoes in Sivakasi under Rs.25/kg")
            parse_btn = st.button("Parse Demand with AI NLP", use_container_width=True, type="primary")

        with bp2:
            parsed = parse_buyer_demand_nlp(raw_input, district)
            st.markdown("###Parsed Agricultural Parameters")
            st.json(parsed)

        if parse_btn:
            new_dem_id = f"DEM-{len(st.session_state.buyer_demands) + 201}"
            new_demand = {
                "id": new_dem_id,
                "buyer_name": farmer_name,  # actual logged-in buyer name
                "buyer_phone": prof.get("phone_email", ""),
                "buyer_type": prof.get("buyer_type", "Wholesaler"),
                "raw_text": raw_input,
                "crop": parsed["crop"],
                "quantity_kg": parsed["quantity_kg"],
                "max_price_per_kg": parsed["max_price_per_kg"],
                "district": parsed["district"],
                "min_freshness_pct": parsed["min_freshness_pct"],
                "status": "OPEN",
                "posted_by_phone": prof.get("phone_email", "")  # ownership tag
            }
            st.session_state.buyer_demands.append(new_demand)
            save_demand(new_demand)     #  Write to db/demands.json
            st.success(f" **{farmer_name}** — Demand Request **{new_dem_id}** submitted! Go to **Ranked Supply Matches** to see matching sellers.")
            st.info("If no single seller can fulfil your order, use **Multi-Farmer Supply Pooling** to aggregate from multiple nearby farmers.")

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 16: RANKED SUPPLY MATCHES  [BUYER ONLY]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Ranked Supply Matches":
        st.subheader("Ranked Proximity, Freshness & Price Match Engine")
        st.caption("Matches active farmer inventory with buyer demand using Haversine distance, shelf life & target price.")

        # ── STRICT AUTH GUARD: only logged-in Buyer can view matches & place orders ──
        if not is_buyer_user():
            st.error("Access Denied — Only a logged-in **Buyer / Wholesaler** can view matches and place orders. Please log in as a Buyer.")
            st.stop()

        # ── Check if any demands exist from this buyer ──
        my_demands = [d for d in st.session_state.buyer_demands
                      if d.get("posted_by_phone") == prof.get("phone_email", "") or d.get("buyer_name") == farmer_name]

        if not my_demands:
            my_demands = st.session_state.buyer_demands

        if not my_demands:
            st.warning("You have not submitted any demand requests yet.")
            st.info("Go to **AI Demand NLP Parser** to submit your first demand request, then come back here to see matching sellers.")
            st.stop()

        # ── Check if any sellers have posted listings ──
        if not st.session_state.supply_listings:
            st.warning("No farmer supply listings are available in the marketplace yet.")
            st.info("Farmers need to log in and post their produce listings from **Freshness & Spoilage Monitor** before you can match with them.")
            st.stop()

        dem_options = [f"{d['id']} — {d['crop']} ({d['quantity_kg']} kg in {d['district']})" for d in my_demands]
        sel_dem_idx = st.selectbox("Select Your Demand Request", range(len(dem_options)), format_func=lambda i: dem_options[i])
        target_dem = my_demands[sel_dem_idx]

        ranked_matches = rank_supply_demand_matches(target_dem, st.session_state.supply_listings)

        st.markdown(f"### Ranked Matches for **{target_dem.get('id')}** — {target_dem.get('crop')} in {target_dem.get('district')}")
        st.caption(f"Your max price: ₹{target_dem.get('max_price_per_kg')}/kg | Quantity needed: {target_dem.get('quantity_kg')} kg")

        if not ranked_matches:
            st.warning("No matching sellers found for your demand at this time.")
            st.info("Try **Multi-Farmer Supply Pooling** to aggregate from multiple nearby farmers, or wait for more sellers to post listings.")
        else:
            st.success(f" Found **{len(ranked_matches)}** matching seller(s) for your demand.")
            for rm in ranked_matches:
                with st.container():
                    mc1, mc2, mc3, mc4 = st.columns([2, 1, 1, 1])
                    with mc1:
                        st.markdown(f"** {rm['farmer_name']}** ({rm['district']} — {rm['distance_km']} km away)")
                        risk_badge = "[Optimal]" if rm['risk_level'] == 'FRESH' else ("[Moderate]" if rm['risk_level'] == 'HIGH_RISK' else "[High Risk]")
                        st.caption(f"{risk_badge} {rm['risk_level']} | Qty: {rm['quantity_kg']} kg | ₹{rm['effective_price_per_kg']}/kg (Original: ₹{rm['original_price_per_kg']})")
                        if rm['flash_discount_pct'] > 0:
                            st.caption(f" Flash Sale: {rm['flash_discount_pct']}% off due to freshness risk")
                    with mc2:
                        st.metric("Match Score", f"{rm['match_score']}%")
                    with mc3:
                        st.metric("Freshness", f"{rm['freshness_pct']}%")
                    with mc4:
                        already_ordered = any(
                            o.get("listing_id") == rm['listing_id'] and
                            o.get("buyer_phone") == prof.get("phone_email", "")
                            for o in st.session_state.placed_orders
                        )
                        if already_ordered:
                            st.success("Ordered")
                        else:
                            if st.button(f" Order from {rm['farmer_name']}",
                                         key=f"ord_{rm['listing_id']}",
                                         use_container_width=True,
                                         type="primary"):
                                r_qty = float(target_dem.get('quantity_kg', 100))
                                r_prc = float(rm['effective_price_per_kg'])
                                r_id = f"ORD-{len(st.session_state.placed_orders) + 101}"
                                new_order = {
                                    "id": r_id,
                                    "listing_id": rm['listing_id'],
                                    "buyer_name": farmer_name,
                                    "buyer_phone": prof.get("phone_email", ""),
                                    "seller_name": rm['farmer_name'],
                                    "seller_phone": rm.get('phone', '9840012345'),
                                    "crop": rm['crop'],
                                    "quantity_kg": r_qty,
                                    "price_per_kg": r_prc,
                                    "total_amount": round(r_qty * r_prc, 2),
                                    "district": rm['district'],
                                    "order_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "type": "DIRECT",
                                    "is_pooled": False,
                                    "status": "PENDING SELLER CONFIRMATION"
                                }
                                st.session_state.placed_orders.append(new_order)
                                save_order(new_order)   #  Write to db/orders.json
                                st.success(f" Order #{r_id} placed with **{rm['farmer_name']}** for {r_qty:.0f} kg {rm['crop']} at ₹{r_prc}/kg!")
                                st.info("⏳ Status: **Awaiting Seller Confirmation**. The seller will review and allot harvest dispatch.")
                                st.rerun()

                st.markdown("---")

        # Show this buyer's order history
        my_orders = [o for o in st.session_state.placed_orders
                     if o.get("buyer_phone") == prof.get("phone_email", "")]
        if my_orders:
            st.markdown("#### Your Placed Orders")
            st.dataframe(pd.DataFrame(my_orders), use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 17: MULTI-FARMER SUPPLY POOLING  [BUYER ONLY]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Multi-Farmer Supply Pooling":
        st.subheader("Multi-Vendor Order Aggregation & Supply Pooling Engine")
        st.caption("Splits large bulk buyer orders across multiple nearby small farmers when no single farmer has sufficient inventory.")

        # ── STRICT AUTH GUARD: only logged-in Buyer can pool orders ──
        if not is_buyer_user():
            st.error("Access Denied — Only a logged-in **Buyer / Wholesaler** can pool orders. Please log in as a Buyer.")
            st.stop()

        if not st.session_state.supply_listings:
            st.warning("No farmer supply listings are available yet.")
            st.info("Farmers need to log in and post their listings from **Freshness & Spoilage Monitor** before pooling is possible.")
            st.stop()

        sp_c1, sp_c2 = st.columns(2)
        with sp_c1:
            # Only show crops that have active listings
            available_crops = sorted(set(s["crop"] for s in st.session_state.supply_listings if s.get("status") == "ACTIVE"))
            if not available_crops:
                available_crops = list(CROP_DB.keys())
            pool_crop = st.selectbox("Crop to Pool", available_crops)
            target_bulk_kg = st.number_input("Target Order Quantity (kg)", min_value=100.0, max_value=10000.0, value=750.0, step=50.0)
        with sp_c2:
            buyer_dist = st.selectbox("Delivery Destination District", dist_list, index=dist_list.index(district) if district in dist_list else 0)

        pool_res = pool_supply_orders(pool_crop, target_bulk_kg, buyer_dist, st.session_state.supply_listings)

        st.markdown("---")
        st.markdown(f"### Supply Pooling Result — {pool_res['fulfilled_pct']}% Fulfilled")

        pm1, pm2, pm3, pm4 = st.columns(4)
        with pm1: st.metric("Pooled Quantity", f"{pool_res['pooled_quantity_kg']} kg / {target_bulk_kg} kg")
        with pm2: st.metric("Contributing Farmers", f"{pool_res['contributing_farmers_count']} Farmers")
        with pm3: st.metric("Weighted Avg Price", f"₹{pool_res['avg_price_per_kg']}/kg")
        with pm4: st.metric("Total Order Value", fmt_inr(pool_res['total_cost_inr']))

        st.markdown("####Allocated Farmer Contributions")
        if pool_res['pooled_breakdown']:
            st.dataframe(pd.DataFrame(pool_res['pooled_breakdown']), use_container_width=True, hide_index=True)
            if st.button("Confirm Pooled Multi-Vendor Order", use_container_width=True, type="primary"):
                for p_idx, item in enumerate(pool_res['pooled_breakdown']):
                    p_qty = float(item['allocated_kg'])
                    p_prc = float(item['price_per_kg'])
                    p_oid = f"ORD-POOL-{len(st.session_state.placed_orders) + 101 + p_idx}"
                    new_pool_order = {
                        "id": p_oid,
                        "listing_id": f"POOL-{item['farmer_name']}",
                        "buyer_name": farmer_name,
                        "buyer_phone": prof.get("phone_email", ""),
                        "seller_name": item['farmer_name'],
                        "seller_phone": item.get('phone', '9840012345'),
                        "crop": pool_crop,
                        "quantity_kg": p_qty,
                        "price_per_kg": p_prc,
                        "total_amount": round(p_qty * p_prc, 2),
                        "district": item['district'],
                        "order_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "type": "POOLED",
                        "is_pooled": True,
                        "status": "PENDING SELLER CONFIRMATION",
                        "pool_summary": f"Part of {pool_res['target_kg']} kg {pool_crop} pooled batch across {pool_res['contributing_farmers_count']} farmers"
                    }
                    st.session_state.placed_orders.append(new_pool_order)
                    save_order(new_pool_order)   #  Write to db/orders.json
                st.success(f" Pooled batch order submitted across **{pool_res['contributing_farmers_count']}** contributing farmers! Total: {fmt_inr(pool_res['total_cost_inr'])}")
                st.info("⏳ Status: **Awaiting Seller Confirmations**. Each farmer will review their allocated batch quota. You can track this under **Manage My Orders**.")
                st.balloons()

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW: MARKETPLACE & LIVE PRODUCE  [FOR BOTH SELLERS & BUYERS]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Marketplace & Live Produce":
        st.subheader("Live Produce Marketplace — Available Fresh Supply")
        st.caption("Browse live fresh produce listings posted by verified farmers across Tamil Nadu. Place orders with auto-assigned cold-chain vehicles or chat on WhatsApp!")

        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            all_crops = sorted(list(set(s.get("crop", "Tomato") for s in st.session_state.supply_listings)))
            sel_crop_filter = st.selectbox("Filter by Produce Crop", ["All Crops"] + all_crops, index=0)
        with m_col2:
            all_dists = sorted(list(set(s.get("district", "Thoothukudi") for s in st.session_state.supply_listings)))
            sel_dist_filter = st.selectbox("Filter by District", ["All Districts"] + all_dists, index=0)
        with m_col3:
            max_price_filter = st.slider("Max Price (₹/kg)", 5, 300, 150, step=5)

        # Filter active listings
        active_listings = [
            s for s in st.session_state.supply_listings
            if s.get("status") == "ACTIVE" and float(s.get("quantity_kg", 0)) > 0
        ]
        if sel_crop_filter != "All Crops":
            active_listings = [s for s in active_listings if s.get("crop") == sel_crop_filter]
        if sel_dist_filter != "All Districts":
            active_listings = [s for s in active_listings if s.get("district") == sel_dist_filter]
        active_listings = [s for s in active_listings if float(s.get("price_per_kg", 0)) <= max_price_filter]

        st.markdown(f"### Live Produce Postings ({len(active_listings)} Available)")

        if not active_listings:
            st.info("No produce listings match your filter. Farmers can post fresh listings under **Post Fresh Produce** or **Freshness & Spoilage Monitor**.")
        else:
            grid_cols = st.columns(2)
            for idx, item in enumerate(active_listings):
                c_box = grid_cols[idx % 2]
                with c_box:
                    crop_name = item.get("crop", "Produce")
                    c_info = CROP_DB.get(crop_name, {})
                    c_emoji = ""
                    seller = item.get("farmer_name", "Farmer")
                    seller_phone = item.get("phone") or item.get("posted_by_phone") or "9840012345"
                    dist = item.get("district", "Thoothukudi")
                    qty = float(item.get("quantity_kg", 100))
                    price = float(item.get("price_per_kg", 20))
                    hrs = int(item.get("harvest_hours_ago", 12))

                    fresh_info = calc_freshness_decay(crop_name, hrs)
                    fresh_pct = fresh_info.get("remaining_freshness_pct", 90)
                    fresh_badge = "High Freshness" if fresh_pct >= 75 else ("[Moderate] Moderate" if fresh_pct >= 50 else "[High Risk] Near Expiry")

                    st.markdown(f"""
                    <div style="background: white; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size: 1.8rem;">{c_emoji} <b style="font-size: 1.3rem; color:#0f172a;">{crop_name}</b></span>
                            <span style="background: #f1f5f9; padding: 4px 10px; border-radius: 20px; font-weight:600; font-size:0.85rem; color:#334155;">{fresh_badge} ({fresh_pct}%)</span>
                        </div>
                        <div style="margin-top: 8px; color: #475569; font-size:0.92rem;">
                            <b>Farmer / Seller:</b> {seller} ({dist})<br>
                            <b>Available Qty:</b> <span style="color:#059669; font-weight:700;">{qty:.0f} kg</span> | <b>Price:</b> <span style="color:#059669; font-weight:700;">₹{price}/kg</span><br>
                            <small style="color:#64748b;">Harvested {hrs} hrs ago • Freshness shelf life active</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # WhatsApp Chat Link Button
                    wa_msg = f"Hello {seller}, I saw your {qty:.0f} kg {crop_name} listing on AgriSmart TN (₹{price}/kg) in {dist}. Is it available for order?"
                    wa_link = make_whatsapp_url(seller_phone, wa_msg)
                    
                    st.markdown(f'<a href="{wa_link}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#25D366; color:white; border:none; padding:8px; border-radius:8px; font-weight:bold; cursor:pointer; margin-bottom:8px;"> Contact {seller} on WhatsApp</button></a>', unsafe_allow_html=True)

                    # Order Placement for Buyers
                    if st.session_state.user_role == "Buyer / Wholesaler":
                        with st.expander(f" Order {crop_name} from {seller}", expanded=False):
                            order_qty = st.number_input(f"Quantity to Order (kg)", min_value=10.0, max_value=qty, value=min(100.0, qty), step=10.0, key=f"m_qty_{item['id']}")
                            total_cost = order_qty * price

                            st.write(f"Total Amount: **₹{total_cost:,.2f}**")
                            if st.button(f"Place Order with {seller} ({item['id']})", key=f"btn_ord_{item['id']}", type="primary", use_container_width=True):
                                new_ord_id = f"ORD-{len(st.session_state.placed_orders) + 101}"
                                order_obj = {
                                    "id": new_ord_id,
                                    "listing_id": item['id'],
                                    "buyer_name": farmer_name,
                                    "buyer_phone": prof.get("phone_email", ""),
                                    "seller_name": seller,
                                    "seller_phone": seller_phone,
                                    "crop": crop_name,
                                    "quantity_kg": order_qty,
                                    "price_per_kg": price,
                                    "total_amount": total_cost,
                                    "district": dist,
                                    "order_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "status": "PENDING SELLER CONFIRMATION",
                                    "is_pooled": False,
                                    "type": "DIRECT"
                                }

                                # Deduct quantity from listing
                                remaining_qty = qty - order_qty
                                item["quantity_kg"] = remaining_qty
                                if remaining_qty <= 0:
                                    item["status"] = "SOLD"

                                st.session_state.placed_orders.append(order_obj)
                                save_order(order_obj)     #  Save to orders table
                                save_listing(item)        #  Update listings table

                                st.success(f" Order #{new_ord_id} placed with **{seller}** for **{order_qty:.0f} kg {crop_name}** ({fmt_inr(total_cost)})!")
                                st.info("⏳ Status: **Awaiting Seller Confirmation**. The seller will confirm your order and a cold-chain vehicle will be automatically assigned. You can track this under **Manage My Orders**.")
                                st.balloons()
                                st.rerun()

                    elif st.session_state.user_role == "Farmer / Seller":
                        if seller != farmer_name:
                            if st.button(f" Pool Supply with {seller}", key=f"pool_btn_{item['id']}", use_container_width=True):
                                st.session_state.active_nav = "Seller Supply Pooling"
                                st.rerun()

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW: POST FRESH PRODUCE  [FARMER ONLY]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Post Fresh Produce":
        st.subheader("Post Available Fresh Produce & Harvest Inventory")
        st.caption("Post your fresh harvest available for immediate sale. Verified buyers across Tamil Nadu will see your listing instantly!")

        if not is_seller_user():
            st.error("Access Denied — Only logged-in **Farmers / Sellers** can post produce.")
            st.stop()

        with st.form("post_fresh_produce_form"):
            pf1, pf2 = st.columns(2)
            with pf1:
                p_crop = st.selectbox("Select Crop / Vegetable *", list(CROP_DB.keys()), index=0)
                p_qty = st.number_input("Quantity Available for Sale (kg) *", min_value=10.0, max_value=50000.0, value=500.0, step=20.0)
                p_price = st.number_input("Asking Price (₹ per kg) *", min_value=1.0, max_value=1000.0, value=25.0, step=1.0)
            with pf2:
                p_dist = st.selectbox("Harvest Location District *", dist_list, index=dist_list.index(district) if district in dist_list else 0)
                p_hrs = st.number_input("Hours Elapsed Since Harvest", min_value=0, max_value=168, value=6, step=2)
                p_phone = st.text_input("WhatsApp Contact Mobile Number *", value=prof.get("phone_email", ""), placeholder="98400XXXXX")

            p_notes = st.text_input("Produce Description / Quality Notes", placeholder="e.g. Grade A fresh harvest, organic farm, available for immediate pickup.")

            st.markdown("---")
            post_sub = st.form_submit_button("Publish Produce Listing Live to Buyers", use_container_width=True, type="primary")

            if post_sub:
                if not p_phone.strip():
                    st.error("Please enter a valid WhatsApp contact number.")
                else:
                    listing_id = f"SUP-{len(st.session_state.supply_listings) + 101}"
                    new_item = {
                        "id": listing_id,
                        "farmer_name": farmer_name,
                        "phone": p_phone.strip(),
                        "crop": p_crop,
                        "quantity_kg": p_qty,
                        "price_per_kg": p_price,
                        "district": p_dist,
                        "harvest_hours_ago": p_hrs,
                        "notes": p_notes.strip() or "Grade A Fresh Produce",
                        "status": "ACTIVE",
                        "posted_by_phone": prof.get("phone_email", "")
                    }
                    st.session_state.supply_listings.append(new_item)
                    save_listing(new_item)    #  Save to Supabase / JSON storage

                    st.success(f" **{p_crop}** ({p_qty:.0f} kg at ₹{p_price}/kg) successfully published live! Listing ID: `{listing_id}`")
                    st.info("Buyers logged into AgriSmart TN can now view your listing in the Produce Marketplace and place orders!")
                    st.balloons()
                    st.rerun()

        st.markdown("---")
        st.markdown(f"####  Your Active Produce Inventory ({farmer_name})")
        my_lists = [s for s in st.session_state.supply_listings if s.get("posted_by_phone") == prof.get("phone_email", "") or s.get("farmer_name") == farmer_name]

        if not my_lists:
            st.info("You have not published any produce listings yet. Fill in the form above to add your first harvest listing!")
        else:
            for idx, listing in enumerate(my_lists):
                with st.container():
                    lc1, lc2, lc3 = st.columns([2, 1, 1])
                    with lc1:
                        c_emoji = ""
                        st.markdown(f"**{c_emoji} {listing.get('crop')}** — Listing `{listing.get('id')}`")
                        st.caption(f"Location: {listing.get('district')} | Qty: {listing.get('quantity_kg')} kg | Price: ₹{listing.get('price_per_kg')}/kg | Status: {listing.get('status')}")
                    with lc2:
                        fresh_pct = calc_freshness_decay(listing.get('crop', 'Tomato'), listing.get('harvest_hours_ago', 12)).get('remaining_freshness_pct', 90)
                        st.metric("Freshness Score", f"{fresh_pct}%")
                    with lc3:
                        with st.expander("Manage Listing"):
                            new_p = st.number_input(f"New Price (₹/kg)", min_value=1.0, value=float(listing.get('price_per_kg', 25)), key=f"edit_p_{listing['id']}")
                            new_q = st.number_input(f"New Qty (kg)", min_value=0.0, value=float(listing.get('quantity_kg', 100)), key=f"edit_q_{listing['id']}")
                            if st.button("Save Changes", key=f"save_edit_{listing['id']}", use_container_width=True):
                                listing['price_per_kg'] = new_p
                                listing['quantity_kg'] = new_q
                                if new_q <= 0: listing['status'] = "SOLD"
                                save_listing(listing)
                                st.success("Listing updated!")
                                st.rerun()
                            if st.button("Mark Sold Out", key=f"sold_{listing['id']}", use_container_width=True):
                                listing['status'] = "SOLD"
                                listing['quantity_kg'] = 0
                                save_listing(listing)
                                st.warning("Marked as SOLD OUT.")
                                st.rerun()
                st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW: BUYER DEMANDS & TAKE ORDERS  [FARMER TAKES BUYER ORDERS]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Buyer Demands & Take Orders":
        st.subheader("Open Buyer Demands — Accept & Fulfill Orders Directly")
        st.caption("Browse live procurement requests posted by buyers across Tamil Nadu. Fulfill buyer demands directly to lock in sales at guaranteed prices!")

        if not is_seller_user():
            st.error("Access Denied — Only logged-in **Farmers / Sellers** can take buyer orders.")
            st.stop()

        open_demands = [d for d in st.session_state.buyer_demands if d.get("status") in ["OPEN", "PARTIALLY FULFILLED"]]

        filter_c1, filter_c2 = st.columns(2)
        with filter_c1:
            crop_filter_opts = ["All Crops"] + sorted(list(set(d.get("crop", "Tomato") for d in open_demands)))
            sel_d_crop = st.selectbox("Filter Demands by Crop", crop_filter_opts, index=0)
        with filter_c2:
            dist_filter_opts = ["All Districts"] + sorted(list(set(d.get("district", "Sivakasi") for d in open_demands)))
            sel_d_dist = st.selectbox("Filter Demands by District", dist_filter_opts, index=0)

        if sel_d_crop != "All Crops":
            open_demands = [d for d in open_demands if d.get("crop") == sel_d_crop]
        if sel_d_dist != "All Districts":
            open_demands = [d for d in open_demands if d.get("district") == sel_d_dist]

        st.markdown(f"### Active Buyer Procurement Requests ({len(open_demands)} Open)")

        if not open_demands:
            st.info("No open buyer demands match your filter right now. Buyers can post demands from their portal, and they will appear here live!")
        else:
            for idx, dem in enumerate(open_demands):
                d_id = dem.get("id", f"DEM-{201+idx}")
                b_name = dem.get("buyer_name", "Buyer Wholesaler")
                b_type = dem.get("buyer_type", "Restaurant / Wholesaler")
                b_phone = dem.get("buyer_phone") or dem.get("posted_by_phone") or "9840099887"
                b_dist = dem.get("district", "Sivakasi")
                b_crop = dem.get("crop", "Tomato")
                b_qty = float(dem.get("quantity_kg", 500))
                b_price = float(dem.get("max_price_per_kg", 30))
                b_raw = dem.get("raw_text", f"Need {b_qty:.0f} kg {b_crop} in {b_dist} region around Rs.{b_price}/kg.")

                # Calculate Haversine proximity
                farmer_d_info = TN_DISTRICTS.get(district, {})
                buyer_d_info = TN_DISTRICTS.get(b_dist, {})
                dist_km = calc_haversine_dist(
                    farmer_d_info.get("lat", 8.81), farmer_d_info.get("lon", 78.14),
                    buyer_d_info.get("lat", 9.45), buyer_d_info.get("lon", 77.80)
                )

                c_emoji = ""
                total_val = b_qty * b_price

                with st.container():
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 18px; border: 1px solid #cbd5e1; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size: 1.4rem;">{c_emoji} <b style="color:#0f172a;">{b_crop} Procurement Demand</b> <small style="color:#64748b;">({d_id})</small></span>
                            <span style="background: #e0f2fe; color: #0284c7; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.85rem;">{b_type}</span>
                        </div>
                        <div style="margin-top: 10px; color: #334155; font-size: 0.95rem; line-height: 1.5;">
                            <b>Buyer:</b> {b_name} ({b_dist} — <b>{dist_km:.1f} km away</b>)<br>
                            <b>Required Quantity:</b> <span style="color:#059669; font-weight:700;">{b_qty:.0f} kg</span> | <b>Target Max Price:</b> <span style="color:#059669; font-weight:700;">₹{b_price}/kg</span> | <b>Order Value:</b> <span style="color:#059669; font-weight:700;">{fmt_inr(total_val)}</span><br>
                            <small style="color:#64748b;"><i>"{b_raw}"</i></small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Action row
                    act_col1, act_col2 = st.columns([1, 1])
                    with act_col1:
                        wa_msg = f"Hello {b_name}, I am {farmer_name} from {district}. I saw your demand for {b_qty:.0f} kg {b_crop} (₹{b_price}/kg). I can supply this harvest."
                        wa_url = make_whatsapp_url(b_phone, wa_msg)
                        st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#25D366; color:white; border:none; padding:8px; border-radius:8px; font-weight:bold; cursor:pointer;"> Contact Buyer {b_name} on WhatsApp</button></a>', unsafe_allow_html=True)

                    with act_col2:
                        with st.expander(f" Accept & Fulfill Order ({d_id})", expanded=False):
                            ful_qty = st.number_input(f"Fulfillment Quantity (kg)", min_value=10.0, max_value=b_qty, value=b_qty, step=10.0, key=f"ful_q_{d_id}")
                            ful_price = st.number_input(f"Agreed Price (₹/kg)", min_value=1.0, value=b_price, step=1.0, key=f"ful_p_{d_id}")
                            total_ful_val = ful_qty * ful_price
                            st.write(f"Total Order Value: **{fmt_inr(total_ful_val)}**")

                            if st.button(f" Confirm & Accept Order for {b_name}", key=f"btn_accept_{d_id}", type="primary", use_container_width=True):
                                # Auto-allocate vehicle
                                veh_info = allocate_vehicle_for_order(b_dist)

                                new_order_id = f"ORD-{len(st.session_state.placed_orders) + 901}"
                                order_obj = {
                                    "id": new_order_id,
                                    "demand_id": d_id,
                                    "buyer_name": b_name,
                                    "buyer_phone": b_phone,
                                    "seller_name": farmer_name,
                                    "seller_phone": prof.get("phone_email", ""),
                                    "crop": b_crop,
                                    "quantity_kg": ful_qty,
                                    "price_per_kg": ful_price,
                                    "total_amount": total_ful_val,
                                    "district": b_dist,
                                    "vehicle_reg": veh_info["vehicle_reg"],
                                    "driver_name": veh_info["driver_name"],
                                    "driver_phone": veh_info["driver_phone"],
                                    "order_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "status": "CONFIRMED & VEHICLE ALLOTTED"
                                }

                                # Update demand status
                                remaining_dem_qty = b_qty - ful_qty
                                dem["quantity_kg"] = remaining_dem_qty
                                if remaining_dem_qty <= 0:
                                    dem["status"] = "FULFILLED"
                                else:
                                    dem["status"] = "PARTIALLY FULFILLED"

                                st.session_state.placed_orders.append(order_obj)
                                save_order(order_obj)     #  Save to Supabase orders table
                                save_demand(dem)          #  Update Supabase demands table

                                st.success(f" **Order Accepted!** You agreed to supply **{ful_qty:.0f} kg {b_crop}** to **{b_name}** for **{fmt_inr(total_ful_val)}**.")
                                st.info(f" **Cold-Chain Refrigerated Truck Allotted:** {veh_info['vehicle_reg']} ({veh_info['driver_name']} • {veh_info['driver_phone']})")

                                # WhatsApp direct button to driver
                                drv_wa_msg = f"Hello {veh_info['driver_name']}, Order #{new_order_id} accepted! Please pick up {ful_qty:.0f} kg {b_crop} from {farmer_name} ({district}) for delivery to {b_name} ({b_dist})."
                                drv_wa_link = make_whatsapp_url(veh_info['driver_phone'], drv_wa_msg)
                                st.markdown(f'<a href="{drv_wa_link}" target="_blank"><button style="background:#0284c7; color:white; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;"> Contact Driver {veh_info["driver_name"]} on WhatsApp</button></a>', unsafe_allow_html=True)

                                st.balloons()
                                st.rerun()

                st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW: SELLER RECEIVED ORDERS  [FARMER ORDER TRACKER]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Seller Received Orders":
        st.subheader("📦 Seller Received Orders & Fulfillment Center")
        st.caption("Review incoming buyer orders placed on your fresh harvest. Confirm pending orders, view pooled supply batches, and coordinate cold-chain dispatches.")

        if not is_seller_user():
            st.error("Access Denied — Only logged-in **Farmers / Sellers** can view received orders.")
            st.stop()

        my_received_orders = [
            o for o in st.session_state.placed_orders
            if o.get("seller_name") == farmer_name or 
               (prof.get("phone_email") and o.get("seller_phone") == prof.get("phone_email")) or
               (not o.get("seller_phone") and o.get("seller_name") == farmer_name)
        ]

        pending_orders = [o for o in my_received_orders if "PENDING" in str(o.get("status", "")).upper()]
        confirmed_orders = [o for o in my_received_orders if "CONFIRMED" in str(o.get("status", "")).upper() or "DISPATCH" in str(o.get("status", "")).upper() or "DELIVERED" in str(o.get("status", "")).upper()]
        pooled_orders = [o for o in my_received_orders if o.get("is_pooled")]

        pending_amt = sum(float(o.get("total_amount", 0) or (float(o.get("quantity_kg", 0)) * float(o.get("price_per_kg", 0)))) for o in pending_orders)
        total_rev = sum(float(o.get("total_amount", 0) or (float(o.get("quantity_kg", 0)) * float(o.get("price_per_kg", 0)))) for o in confirmed_orders)
        tot_qty = sum(float(o.get("quantity_kg", 0)) for o in my_received_orders)

        so1, so2, so3, so4, so5 = st.columns(5)
        with so1: st.metric("Total Received", len(my_received_orders))
        with so2: st.metric("Pending Orders", f"{len(pending_orders)} Pending", delta=f"₹{pending_amt:,.0f} Value" if pending_amt else None)
        with so3: st.metric("Confirmed Orders", len(confirmed_orders))
        with so4: st.metric("Pooled Orders", len(pooled_orders))
        with so5: st.metric("Earned Revenue", fmt_inr(total_rev))

        st.markdown("---")

        t_all, t_pend, t_conf, t_pool = st.tabs([
            f"All Orders ({len(my_received_orders)})",
            f"⏳ Pending Confirmation ({len(pending_orders)})",
            f"✅ Confirmed & Dispatched ({len(confirmed_orders)})",
            f"🏷️ Pooled Batches ({len(pooled_orders)})"
        ])

        def render_seller_order_list(order_list, tab_prefix="all"):
            if not order_list:
                st.info("No orders found in this section.")
                return

            for idx, ord_item in enumerate(order_list):
                ord_id = ord_item.get("id") or ord_item.get("listing_id", f"ORD-{idx+901}")
                crop_n = ord_item.get("crop", "Produce")
                b_name = ord_item.get("buyer_name", "Buyer")
                b_phone = ord_item.get("buyer_phone", "")
                b_dist = ord_item.get("district", district)
                o_qty = float(ord_item.get("quantity_kg", 100))
                o_price = float(ord_item.get("price_per_kg", 25))
                o_total = float(ord_item.get("total_amount") or (o_qty * o_price))
                o_status = str(ord_item.get("status", "PENDING SELLER CONFIRMATION"))
                o_time = ord_item.get("order_time", "Today")
                is_pool = ord_item.get("is_pooled", False)
                d_reg = ord_item.get("vehicle_reg", "TN 67 AD 4521")
                d_name = ord_item.get("driver_name", "Sundaram T.")
                d_phone = ord_item.get("driver_phone", "9840077665")

                is_pending = "PENDING" in o_status.upper()
                is_confirmed = "CONFIRMED" in o_status.upper()
                is_dispatched = "DISPATCH" in o_status.upper()
                is_delivered = "DELIVERED" in o_status.upper()

                stat_badge_bg = "#fef3c7" if is_pending else ("#dcfce7" if is_confirmed else ("#e0f2fe" if is_dispatched else "#f0fdf4"))
                stat_badge_color = "#b45309" if is_pending else ("#15803d" if is_confirmed else ("#0369a1" if is_dispatched else "#166534"))
                stat_label = "⏳ AWAITING YOUR CONFIRMATION" if is_pending else o_status

                pool_html = ""
                if is_pool:
                    pool_html = """
                    <div style="margin-top: 8px; background: #faf5ff; border: 1px solid #d8b4fe; border-radius: 8px; padding: 6px 12px; display:flex; align-items:center; gap: 8px;">
                        <span style="background: #9333ea; color: white; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.72rem;">🏷️ POOLED ORDER</span>
                        <span style="color: #6b21a8; font-size: 0.85rem; font-weight: 500;">This order is part of an aggregated multi-farmer / multi-buyer pooled supply batch. Fulfill and coordinate dispatch together with the pool.</span>
                    </div>
                    """

                vehicle_html = ""
                if not is_pending:
                    vehicle_html = f"""<br><b>Assigned Cold-Chain Vehicle:</b> <span style="color:#0284c7; font-weight:600;">{d_reg}</span> (Driver: {d_name} • 📞 {d_phone})"""

                with st.container():
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 18px; border: 1px solid {'#f59e0b' if is_pending else '#cbd5e1'}; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; color:#0f172a; font-size:1.15rem;">Order #{ord_id} — {crop_n}</span>
                            <span style="background:{stat_badge_bg}; color:{stat_badge_color}; padding:4px 12px; border-radius:12px; font-weight:bold; font-size:0.8rem;">{stat_label}</span>
                        </div>
                        <div style="margin-top:8px; color:#475569; font-size:0.92rem; line-height:1.6;">
                            <b>Buyer:</b> {b_name} (📞 {b_phone} | 📍 {b_dist})<br>
                            <b>Fulfillment Quantity:</b> <span style="font-weight:700; color:#0f172a;">{o_qty:.0f} kg</span> @ ₹{o_price}/kg | <b>Total Order Amount:</b> <span style="color:#059669; font-weight:700; font-size:1.05rem;">{fmt_inr(o_total)}</span><br>
                            <b>Ordered Time:</b> {o_time} {vehicle_html}
                        </div>
                        {pool_html}
                    </div>
                    """, unsafe_allow_html=True)

                    btn_c1, btn_c2, btn_c3 = st.columns([2, 1.5, 1.5])
                    if is_pending:
                        with btn_c1:
                            if st.button(f"✅ Confirm Order & Allot Vehicle", key=f"s_conf_btn_{tab_prefix}_{ord_id}_{idx}", type="primary", use_container_width=True):
                                veh = allocate_vehicle_for_order(b_dist)
                                ord_item["status"] = "CONFIRMED & VEHICLE ALLOTTED"
                                ord_item["vehicle_reg"] = veh.get("vehicle_reg", "TN 67 AD 4521")
                                ord_item["driver_name"] = veh.get("driver_name", "Sundaram T.")
                                ord_item["driver_phone"] = veh.get("driver_phone", "9840077665")
                                save_all_orders(st.session_state.placed_orders)
                                st.success(f"Order #{ord_id} Confirmed! Cold-chain vehicle {ord_item['vehicle_reg']} allocated.")
                                st.rerun()
                        with btn_c2:
                            if st.button(f"❌ Decline", key=f"s_dec_btn_{tab_prefix}_{ord_id}_{idx}", use_container_width=True):
                                ord_item["status"] = "DECLINED BY SELLER"
                                save_all_orders(st.session_state.placed_orders)
                                st.warning(f"Order #{ord_id} declined.")
                                st.rerun()
                        with btn_c3:
                            if b_phone:
                                b_msg = f"Hello {b_name}, regarding Order #{ord_id} for {o_qty:.0f} kg {crop_n}. Harvest is ready for pickup."
                                b_url = make_whatsapp_url(b_phone, b_msg)
                                st.markdown(f'<a href="{b_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#25D366; color:white; border:none; padding:7px; border-radius:6px; font-weight:bold; cursor:pointer;">💬 WhatsApp</button></a>', unsafe_allow_html=True)
                    else:
                        with btn_c1:
                            if not is_dispatched and not is_delivered:
                                if st.button(f"🚚 Mark Dispatched", key=f"s_disp_btn_{tab_prefix}_{ord_id}_{idx}", use_container_width=True):
                                    ord_item["status"] = "DISPATCHED & IN TRANSIT"
                                    save_all_orders(st.session_state.placed_orders)
                                    st.info(f"Order #{ord_id} marked as Dispatched & In Transit.")
                                    st.rerun()
                            elif is_dispatched:
                                if st.button(f"🏁 Mark Delivered", key=f"s_deliv_btn_{tab_prefix}_{ord_id}_{idx}", type="primary", use_container_width=True):
                                    ord_item["status"] = "DELIVERED"
                                    save_all_orders(st.session_state.placed_orders)
                                    st.success(f"Order #{ord_id} marked as Delivered!")
                                    st.rerun()
                        with btn_c2:
                            if b_phone:
                                b_msg = f"Hello {b_name}, regarding Order #{ord_id} ({o_qty:.0f} kg {crop_n}): Harvest status: {o_status}."
                                b_url = make_whatsapp_url(b_phone, b_msg)
                                st.markdown(f'<a href="{b_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#25D366; color:white; border:none; padding:7px; border-radius:6px; font-weight:bold; cursor:pointer;">💬 WhatsApp Buyer</button></a>', unsafe_allow_html=True)
                        with btn_c3:
                            if d_phone:
                                d_msg = f"Hello {d_name}, please confirm pickup schedule for Order #{ord_id} ({o_qty:.0f} kg {crop_n})."
                                d_url = make_whatsapp_url(d_phone, d_msg)
                                st.markdown(f'<a href="{d_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#0284c7; color:white; border:none; padding:7px; border-radius:6px; font-weight:bold; cursor:pointer;">🚚 WhatsApp Driver</button></a>', unsafe_allow_html=True)

                st.markdown("---")

        with t_all:
            render_seller_order_list(my_received_orders, tab_prefix="s_all")
        with t_pend:
            render_seller_order_list(pending_orders, tab_prefix="s_pend")
        with t_conf:
            render_seller_order_list(confirmed_orders, tab_prefix="s_conf")
        with t_pool:
            render_seller_order_list(pooled_orders, tab_prefix="s_pool")


    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW: MANAGE MY ORDERS  [BUYER ORDER TRACKER]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Manage My Orders":
        st.subheader("📦 Manage My Orders & Procurement Tracking")
        st.caption("Track the live status of all your placed produce orders. Monitor seller confirmations, pooled supply batches, and cold-chain delivery vehicle dispatch.")

        if not is_buyer_user():
            st.error("Access Denied — Only logged-in **Buyers / Wholesalers** can access Buyer Order Management.")
            st.stop()

        my_buyer_orders = [
            o for o in st.session_state.placed_orders
            if o.get("buyer_name") == farmer_name or 
               (prof.get("phone_email") and o.get("buyer_phone") == prof.get("phone_email")) or
               o.get("buyer_phone") == farmer_name
        ]

        b_pending = [o for o in my_buyer_orders if "PENDING" in str(o.get("status", "")).upper()]
        b_confirmed = [o for o in my_buyer_orders if "CONFIRMED" in str(o.get("status", "")).upper() or "DISPATCH" in str(o.get("status", "")).upper() or "DELIVERED" in str(o.get("status", "")).upper()]
        b_pooled = [o for o in my_buyer_orders if o.get("is_pooled")]

        total_b_spend = sum(float(o.get("total_amount", 0) or (float(o.get("quantity_kg", 0)) * float(o.get("price_per_kg", 0)))) for o in my_buyer_orders)
        total_b_qty = sum(float(o.get("quantity_kg", 0)) for o in my_buyer_orders)

        bo1, bo2, bo3, bo4, bo5 = st.columns(5)
        with bo1: st.metric("Total Placed", len(my_buyer_orders))
        with bo2: st.metric("Awaiting Seller", len(b_pending))
        with bo3: st.metric("Confirmed Orders", len(b_confirmed))
        with bo4: st.metric("Pooled Orders", len(b_pooled))
        with bo5: st.metric("Total Spend", fmt_inr(total_b_spend))

        st.markdown("---")

        bt_all, bt_conf, bt_pend, bt_pool = st.tabs([
            f"All My Orders ({len(my_buyer_orders)})",
            f"✅ Confirmed by Seller ({len(b_confirmed)})",
            f"⏳ Pending Confirmation ({len(b_pending)})",
            f"🏷️ Pooled Orders ({len(b_pooled)})"
        ])

        def render_buyer_order_list(orders_subset, tab_prefix="all"):
            if not orders_subset:
                st.info("No orders found in this section. Browse Marketplace to place orders!")
                return

            for idx, ord_item in enumerate(orders_subset):
                ord_id = ord_item.get("id") or ord_item.get("listing_id", f"ORD-{idx+101}")
                crop_n = ord_item.get("crop", "Produce")
                seller = ord_item.get("seller_name", "Farmer")
                s_phone = ord_item.get("seller_phone", "")
                o_dist = ord_item.get("district", district)
                o_qty = float(ord_item.get("quantity_kg", 100))
                o_price = float(ord_item.get("price_per_kg", 25))
                o_total = float(ord_item.get("total_amount") or (o_qty * o_price))
                o_status = str(ord_item.get("status", "PENDING SELLER CONFIRMATION"))
                o_time = ord_item.get("order_time", "Today")
                is_pool = ord_item.get("is_pooled", False)
                d_reg = ord_item.get("vehicle_reg", "TN 67 AD 4521")
                d_name = ord_item.get("driver_name", "Sundaram T.")
                d_phone = ord_item.get("driver_phone", "9840077665")

                is_pending = "PENDING" in o_status.upper()
                is_confirmed = "CONFIRMED" in o_status.upper()
                is_dispatched = "DISPATCH" in o_status.upper()
                is_delivered = "DELIVERED" in o_status.upper()

                stat_badge_bg = "#fef3c7" if is_pending else ("#dcfce7" if is_confirmed else ("#e0f2fe" if is_dispatched else "#f0fdf4"))
                stat_badge_color = "#b45309" if is_pending else ("#15803d" if is_confirmed else ("#0369a1" if is_dispatched else "#166534"))
                stat_label = "⏳ PENDING SELLER CONFIRMATION" if is_pending else ("✅ CONFIRMED & VEHICLE ALLOTTED" if is_confirmed else o_status)

                pool_html = ""
                if is_pool:
                    pool_html = """
                    <div style="margin-top: 8px; background: #faf5ff; border: 1px solid #d8b4fe; border-radius: 8px; padding: 6px 12px; display:flex; align-items:center; gap: 8px;">
                        <span style="background: #9333ea; color: white; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.72rem;">🏷️ POOLED ORDER</span>
                        <span style="color: #6b21a8; font-size: 0.85rem; font-weight: 500;">Aggregated with neighboring buyer orders for bulk freight savings and coordinated cold-chain transport.</span>
                    </div>
                    """

                delivery_html = ""
                if not is_pending:
                    delivery_html = f"""<br><b>Cold-Chain Vehicle:</b> <span style="color:#0284c7; font-weight:600;">{d_reg}</span> (Driver: {d_name} • 📞 {d_phone} • Refrigerated at 4.5°C)"""
                else:
                    delivery_html = """<br><span style="color:#d97706; font-size:0.85rem;">⏳ <i>Awaiting seller confirmation. A temperature-controlled vehicle will be assigned automatically upon confirmation.</i></span>"""

                with st.container():
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 18px; border: 1px solid {'#cbd5e1' if not is_pending else '#fde68a'}; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; color:#0f172a; font-size:1.15rem;">Order #{ord_id} — {crop_n}</span>
                            <span style="background:{stat_badge_bg}; color:{stat_badge_color}; padding:4px 12px; border-radius:12px; font-weight:bold; font-size:0.8rem;">{stat_label}</span>
                        </div>
                        <div style="margin-top:8px; color:#475569; font-size:0.92rem; line-height:1.6;">
                            <b>Seller:</b> {seller} (📍 {o_dist})<br>
                            <b>Ordered Quantity:</b> <span style="font-weight:700; color:#0f172a;">{o_qty:.0f} kg</span> @ ₹{o_price}/kg | <b>Total Amount:</b> <span style="color:#059669; font-weight:700; font-size:1.05rem;">{fmt_inr(o_total)}</span><br>
                            <b>Placed At:</b> {o_time} {delivery_html}
                        </div>
                        {pool_html}
                    </div>
                    """, unsafe_allow_html=True)

                    bc1, bc2, bc3 = st.columns(3)
                    with bc1:
                        if s_phone:
                            s_msg = f"Hello {seller}, checking on Order #{ord_id} for {o_qty:.0f} kg {crop_n}. harvest is ready for pickup."
                            s_url = make_whatsapp_url(s_phone, s_msg)
                            st.markdown(f'<a href="{s_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#25D366; color:white; border:none; padding:7px; border-radius:6px; font-weight:bold; cursor:pointer;">💬 WhatsApp Seller</button></a>', unsafe_allow_html=True)
                        else:
                            if st.button(f"💬 Chat with Seller", key=f"b_chat_{tab_prefix}_{ord_id}_{idx}", use_container_width=True):
                                st.session_state.active_nav = "Direct In-App Chat"
                                st.rerun()
                    with bc2:
                        if not is_pending and d_phone:
                            d_msg = f"Hello {d_name}, tracking delivery status for Order #{ord_id} ({o_qty:.0f} kg {crop_n})."
                            d_url = make_whatsapp_url(d_phone, d_msg)
                            st.markdown(f'<a href="{d_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#0284c7; color:white; border:none; padding:7px; border-radius:6px; font-weight:bold; cursor:pointer;">🚚 Contact Driver</button></a>', unsafe_allow_html=True)
                        elif is_pending:
                            if st.button(f"❌ Cancel Order", key=f"b_canc_{tab_prefix}_{ord_id}_{idx}", use_container_width=True):
                                ord_item["status"] = "CANCELLED BY BUYER"
                                save_all_orders(st.session_state.placed_orders)
                                st.warning(f"Order #{ord_id} has been cancelled.")
                                st.rerun()
                    with bc3:
                        if not is_pending:
                            if st.button(f"❄️ Cold-Chain Telemetry", key=f"b_telem_{tab_prefix}_{ord_id}_{idx}", use_container_width=True):
                                st.session_state.active_nav = "Refrigeration Cold-Chain Monitor"
                                st.rerun()

                st.markdown("---")

        with bt_all:
            render_buyer_order_list(my_buyer_orders, tab_prefix="b_all")
        with bt_conf:
            render_buyer_order_list(b_confirmed, tab_prefix="b_conf")
        with bt_pend:
            render_buyer_order_list(b_pending, tab_prefix="b_pend")
        with bt_pool:
            render_buyer_order_list(b_pooled, tab_prefix="b_pool")



    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW: SELLER SUPPLY POOLING  [FARMERS COLLABORATING]
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Seller Supply Pooling":
        st.subheader("Seller Supply Pooling & Multi-Farmer Collaboration")
        st.caption("Can't fulfill a buyer's bulk order alone? Pool your harvest with nearby small farmers to meet large buyer demand!")

        open_demands = st.session_state.buyer_demands or []
        if not open_demands:
            st.info("No large buyer demands currently open. When buyers request bulk quantities (e.g. 1000 kg), they will appear here for sellers to pool together.")
        else:
            for dem in open_demands:
                with st.container():
                    st.markdown(f"""
                    <div style="background:#f8fafc; padding:15px; border-radius:10px; border:1px solid #cbd5e1; margin-bottom:10px;">
                        <h4 style="margin:0; color:#0f172a;"> Bulk Demand: {dem.get('quantity_kg', 0)} kg {dem.get('crop', 'Crop')} in {dem.get('district', 'District')}</h4>
                        <p style="margin:4px 0; color:#475569; font-size:0.9rem;">
                            <b>Buyer:</b> {dem.get('buyer_name', 'Wholesaler')} | <b>Target Max Price:</b> ₹{dem.get('max_price_per_kg', 0)}/kg
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    c_c1, c_c2 = st.columns([2, 1])
                    with c_c1:
                        contribute_qty = st.number_input(f"Your Contribution (kg) for Demand {dem['id']}", min_value=10.0, max_value=float(dem.get('quantity_kg', 500)), value=100.0, step=10.0, key=f"pool_in_{dem['id']}")
                    with c_c2:
                        if st.button(f" Contribute to Pool ({dem['id']})", key=f"pool_add_{dem['id']}", type="primary"):
                            pool_entry = {
                                "id": f"SUP-POOL-{len(st.session_state.supply_listings)+1}",
                                "farmer_name": farmer_name,
                                "phone": prof.get("phone_email", ""),
                                "crop": dem.get('crop'),
                                "quantity_kg": contribute_qty,
                                "price_per_kg": dem.get('max_price_per_kg'),
                                "district": district,
                                "status": "ACTIVE",
                                "posted_by_phone": prof.get("phone_email", "")
                            }
                            st.session_state.supply_listings.append(pool_entry)
                            save_listing(pool_entry)
                            st.success(f" Added your **{contribute_qty} kg** contribution to the pool for {dem.get('crop')}!")
                            st.rerun()

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 18: MARKETPLACE & LIVE DISTRICT MAP
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Marketplace & Live Map":
        st.subheader("Live Marketplace & District Geographic Map")
        st.caption("Geographic distribution of supply listings and buyer demands across Tamil Nadu districts.")

        df_all_sup = pd.DataFrame(st.session_state.supply_listings)
        
        # Plot map markers
        map_data = []
        for sup in st.session_state.supply_listings:
            d_info = TN_DISTRICTS.get(sup.get("district"), {})
            map_data.append({
                "farmer": sup["farmer_name"],
                "crop": sup["crop"],
                "qty": sup["quantity_kg"],
                "price": sup["price_per_kg"],
                "district": sup["district"],
                "lat": d_info.get("lat", 9.58),
                "lon": d_info.get("lon", 77.96)
            })

        df_map = pd.DataFrame(map_data)
        fig_map = px.scatter_mapbox(
            df_map, lat="lat", lon="lon", hover_name="farmer", hover_data=["crop", "qty", "price", "district"],
            color="crop", size="qty", zoom=6.5, height=450, title="Live Active Crop Supply Map (Tamil Nadu)"
        )
        fig_map.update_layout(mapbox_style="open-street-map", margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig_map, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 19: DIRECT IN-APP CHAT & WHATSAPP
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Direct In-App Chat":
        st.subheader("Direct Counterparty Negotiation Chat & WhatsApp")
        st.caption("Connect live with Farmers, Buyers, or Cold-Chain Logistics Drivers. Click to chat directly on WhatsApp!")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"sender": "System", "text": f"Welcome {farmer_name}! Select a counterparty below to start negotiating price and delivery terms."}
            ]

        ch1, ch2 = st.columns([1, 2])
        with ch1:
            target_role = st.radio("Negotiate With", ["Farmer / Seller", "Buyer / Wholesaler", " Cold-Chain Driver"], index=0)
            target_phone = st.text_input("Counterparty Mobile Number", value="9840012345", placeholder="98400XXXXX")
            
            wa_text = f"Hello, I am contacting you from AgriSmart TN regarding agricultural produce."
            wa_url = make_whatsapp_url(target_phone, wa_text)
            st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#25D366; color:white; border:none; padding:10px; border-radius:8px; font-weight:bold; cursor:pointer;"> Open WhatsApp Chat</button></a>', unsafe_allow_html=True)

        with ch2:
            st.markdown("####Live Chat Room")
            chat_container = st.container(height=300)
            with chat_container:
                for msg in st.session_state.chat_history:
                    if msg["sender"] == farmer_name:
                        st.chat_message("user").markdown(f"**{msg['sender']}**: {msg['text']}")
                    else:
                        st.chat_message("assistant").markdown(f"**{msg['sender']}**: {msg['text']}")

            user_msg = st.chat_input("Type message / price counter-offer...")
            if user_msg:
                st.session_state.chat_history.append({"sender": farmer_name, "text": user_msg})
                st.rerun()


    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 20: DELIVERY ROUTE OPTIMIZER
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Delivery Route Optimizer":
        st.subheader("Logistics Route Leg Optimizer (Nearest-Neighbor)")
        st.caption("Multi-stop pickup & delivery sequence planner for minimum travel distance & fuel consumption.")

        route_res = optimize_delivery_route()

        rm1, rm2, rm3, rm4 = st.columns(4)
        with rm1: st.metric("Total Stops", route_res['total_stops'])
        with rm2: st.metric("Total Distance", f"{route_res['total_distance_km']} km")
        with rm3: st.metric("Est. Travel Time", f"{route_res['total_est_travel_mins']} mins")
        with rm4: st.metric("Fuel Saved", f"{route_res['est_fuel_saved_liters']} L")

        st.markdown("####Stop-by-Stop Leg Sequence")
        st.dataframe(pd.DataFrame(route_res['route_legs']), use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 21: REFRIGERATION COLD-CHAIN MONITOR
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Refrigeration Cold-Chain Monitor":
        st.subheader("Refrigerated Cold-Chain Telemetry & Temperature Monitor")
        st.caption("Live cooler status, temperature sensor logging, and thermal decay alerts.")

        veh = st.session_state.driver_vehicles[0] if st.session_state.driver_vehicles else {}

        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            c_status = st.toggle("Cooler Refrigeration Unit Status", value=(veh.get("cooler_status") == "ON"))
            t_set = st.slider("Target Cooler Temperature (°C)", 1.0, 15.0, float(veh.get("target_temp_c", 4.0)), step=0.5)

        with col_c2:
            st.metric("Vehicle Reg", veh.get("vehicle_reg", "TN 67 AD 4521"))
            st.metric("Current Temp", f"{veh.get('current_temp_c', 4.5)}°C", delta="-0.5°C Optimal")

        st.markdown("---")
        st.markdown("####Simulated 24-Hour Cooler Temperature Log")
        hours = list(range(0, 24, 2))
        temps = [4.8, 4.5, 4.4, 4.2, 4.5, 4.3, 4.6, 4.4, 4.5, 4.3, 4.4, 4.5]
        df_temp = pd.DataFrame({"Hour": hours, "Cooler Temp (°C)": temps})

        fig_t = px.line(df_temp, x="Hour", y="Cooler Temp (°C)", title="Cold Chain Storage Temperature Telemetry", markers=True)
        fig_t.add_hline(y=t_set, line_dash="dash", line_color="green", annotation_text="Target Temp")
        fig_t.update_layout(template="plotly_white", height=320)
        st.plotly_chart(fig_t, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # HARVESTLINE VIEW 22: PICKUP & DISPATCH CHECKLIST
    # ─────────────────────────────────────────────────────────────────────────────
    elif nav == "Pickup & Dispatch Checklist":
        st.subheader("Driver Pickup & Delivery Dispatch Checklist")

        st.checkbox("Pick up 400 kg Tomatoes from Sattur Farm Pool (Ramasamy K.)", value=True)
        st.checkbox("Pick up 350 kg Tomatoes from Virudhunagar Hub (Muthu V.)", value=True)
        st.checkbox("Inspect cold-chain seal & confirm temperature at 4.0°C", value=True)
        st.checkbox("Deliver 750 kg pooled tomatoes to Annapoorna Group, Sivakasi", value=False)

        if st.button("Complete Trip & Mark Fulfilled", use_container_width=True):
            st.success("Trip marked complete! Farmer credit scores updated and buyer order fulfilled.")

if __name__ == '__main__':
    main()

