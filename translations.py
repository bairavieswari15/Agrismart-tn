"""
AgriSmart TN — Multilingual Translation Dictionary (English / தமிழ்)
Provides instant UI translation for Streamlit frontend.
"""

TRANSLATIONS = {
    "English": {
        "app_title": "AgriSmart TN — Smart Agriculture Platform",
        "app_subtitle": "Tamil Nadu Agricultural Precision Advisory Engine",
        "nav_crop_finder": "Smart Crop Finder",
        "nav_profit_calc": "Financial Profit Calculator",
        "nav_solar_pump": "Solar Pump & PM-KUSUM ROI",
        "nav_ml_yield": "ML Crop Yield Predictor",
        "nav_pest_ai": "Pest AI Diagnostics",
        "nav_gantt": "Crop Lifecycle Gantt",
        "nav_schemes": "Govt Schemes & Subsidies",
        "nav_mandi": "Mandi Price Tracker",
        "nav_machinery": "Machinery & Labor Estimator",
        "nav_soil_irrigation": "Soil Health & Irrigation",
        "nav_summary_pdf": "Farm Summary & PDF Export",
        "farmer_profile": "Farmer Profile & Account",
        "district": "District",
        "land_acres": "Land Area (Acres)",
        "soil_type": "Soil Type",
        "irrigation": "Irrigation Source",
        "calculate_profit": "Calculate Profitability",
        "solar_pump_title": "Solar Pump & PM-KUSUM Subsidy ROI Calculator",
        "ml_yield_title": "Machine Learning Crop Yield Predictor (scikit-learn)",
        "subsidy": "Subsidy",
        "payback_period": "Payback Period",
        "predicted_yield": "Predicted Harvest Yield",
        "confidence_score": "ML Model Accuracy (R²)",
    },
    "தமிழ்": {
        "app_title": "அக்ரிஸ்மார்ட் தமிழ்நாடு — நவீன விவசாய வழிகாட்டி",
        "app_subtitle": "தமிழ்நாடு துல்லிய வேளாண்மை மற்றும் வருமான கணக்கீட்டு மையம்",
        "nav_crop_finder": "சிறந்த பயிர் தேர்வு",
        "nav_profit_calc": "விவசாய லாப கணக்கீட்டாளர்",
        "nav_solar_pump": "சூரிய சக்தி பம்ப் & பிஎம்-குசும் மானியம்",
        "nav_ml_yield": "இயந்திர கற்றல் (ML) மகசூல் கணிப்பு",
        "nav_pest_ai": "பயிர் நோய் அறிதல் (Pest AI)",
        "nav_gantt": "பயிர் வளர்ச்சிக்காலம் (Gantt)",
        "nav_schemes": "அரசு மானியங்கள் & திட்டங்கள்",
        "nav_mandi": "சந்தை விலை நிலவரம் (Mandi)",
        "nav_machinery": "எந்திர வாடகை & கூலி கணக்கீடு",
        "nav_soil_irrigation": "மண் வளம் & பாசன முறை",
        "nav_summary_pdf": "பண்ணை அறிக்கை & PDF டவுன்லோட்",
        "farmer_profile": "விவசாயி சுயவிவரம்",
        "district": "மாவட்டம்",
        "land_acres": "நில அளவு (ஏக்கர்)",
        "soil_type": "மண் வகை",
        "irrigation": "பாசன வசதி",
        "calculate_profit": "லாபம் கணக்கிடுக",
        "solar_pump_title": "சூரிய சக்தி பம்ப்செட் & PM-KUSUM 60% மானியம்",
        "ml_yield_title": "AI/ML மூலம் பயிர் மகசூல் கணிப்பான்",
        "subsidy": "அரசு மானியம்",
        "payback_period": "முதலீடு திரும்பப் பெறும் காலம்",
        "predicted_yield": "எதிர்பார்க்கப்படும் மகசூல்",
        "confidence_score": "ML மாதிரி துல்லியம் (R²)",
    }
}

CROP_TAMIL = {
    "Paddy": "நெல்",
    "Banana": "வாழை",
    "Sugarcane": "கரும்பு",
    "Coconut": "தென்னை",
    "Groundnut": "வேர்க்கடலை",
    "Cotton": "பருத்தி",
    "Turmeric": "மஞ்சள்",
    "Maize": "சோளம்",
    "Tomato": "தக்காளி",
    "Millets": "சிறு தானியங்கள்",
    "Pearl Millet": "கம்பு",
    "Vegetables": "காய்கறிகள்",
    "Mango": "மாம்பழம்",
    "Tapioca": "மரவள்ளிக்கிழங்கு",
    "Pulses": "பயறு வகைகள்",
    "Black Gram": "உளுந்து",
    "Grapes": "திராட்சை",
    "Tea": "தேயிலை",
    "Coffee": "காபி",
    "Potato": "உருளைக்கிழங்கு",
    "Carrot": "கேரட்",
    "Rubber": "ரப்பர்",
    "Jasmine": "மல்லிகை",
    "Betel Nut": "பாக்கு"
}

def t(key: str, lang: str = "English") -> str:
    """Helper to return translation string for key in selected language."""
    dict_lang = TRANSLATIONS.get(lang, TRANSLATIONS["English"])
    return dict_lang.get(key, TRANSLATIONS["English"].get(key, key))

def crop_t(crop_name: str, lang: str = "English") -> str:
    """Helper to translate crop name into Tamil if selected."""
    if lang == "தமிழ்":
        tn = CROP_TAMIL.get(crop_name)
        if tn:
            return f"{crop_name} ({tn})"
    return crop_name
