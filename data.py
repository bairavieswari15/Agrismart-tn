"""
AgriSmart TN - Backend Data Module
Contains Tamil Nadu district profiles, crop database, crop exclusion maps, ideal conditions, and historical yield records.
"""

# ALL 38 TAMIL NADU DISTRICTS
TN_DISTRICTS = {
    "Ariyalur": {"zone":"Central","avg_temp":30,"rainfall_mm":950,"humidity":68,"soil":"Alluvial / Red Loam","soil_ph":6.9,"main_crops":["Paddy","Sugarcane","Groundnut","Pulses"],"river":"Kollidam","known_for":"Limestone, Paddy","lat":11.14,"lon":79.08},
    "Chengalpattu": {"zone":"North Coastal","avg_temp":29,"rainfall_mm":1200,"humidity":74,"soil":"Sandy Loam / Clay","soil_ph":6.8,"main_crops":["Paddy","Vegetables","Groundnut","Banana"],"river":"Palar","known_for":"Paddy, Vegetables","lat":12.69,"lon":79.98},
    "Chennai": {"zone":"North Coastal","avg_temp":29,"rainfall_mm":1400,"humidity":76,"soil":"Sandy Loam / Red Laterite","soil_ph":6.8,"main_crops":["Vegetables","Groundnut","Paddy"],"river":"Cooum, Adyar","known_for":"Urban farming, Vegetables","lat":13.08,"lon":80.27},
    "Coimbatore": {"zone":"Western","avg_temp":27,"rainfall_mm":700,"humidity":60,"soil":"Black Cotton / Red Laterite","soil_ph":7.2,"main_crops":["Banana","Coconut","Sugarcane","Cotton","Maize"],"river":"Noyyal","known_for":"Banana, Cotton","lat":11.02,"lon":76.96},
    "Cuddalore": {"zone":"East Coastal","avg_temp":29,"rainfall_mm":1300,"humidity":78,"soil":"Alluvial / Clay Loam","soil_ph":7.0,"main_crops":["Paddy","Sugarcane","Banana","Coconut"],"river":"Pennaiyar, Paravanar","known_for":"Paddy, Coconut","lat":11.75,"lon":79.76},
    "Dharmapuri": {"zone":"North-Western","avg_temp":28,"rainfall_mm":900,"humidity":58,"soil":"Red Sandy / Loam","soil_ph":6.4,"main_crops":["Mango","Banana","Paddy","Groundnut","Tapioca"],"river":"Cauvery (upstream)","known_for":"Mango, Tapioca","lat":12.12,"lon":78.16},
    "Dindigul": {"zone":"Central","avg_temp":28,"rainfall_mm":800,"humidity":62,"soil":"Red Sandy / Black Cotton","soil_ph":6.8,"main_crops":["Banana","Coconut","Paddy","Groundnut","Mango"],"river":"Kodaganar","known_for":"Banana, Coconut","lat":10.36,"lon":77.97},
    "Erode": {"zone":"Western","avg_temp":28,"rainfall_mm":750,"humidity":61,"soil":"Red Laterite / Sandy Loam","soil_ph":6.6,"main_crops":["Turmeric","Coconut","Banana","Sugarcane","Cotton"],"river":"Kaveri, Bhavani","known_for":"Turmeric capital of India","lat":11.34,"lon":77.72},
    "Kallakurichi": {"zone":"Central","avg_temp":29,"rainfall_mm":1000,"humidity":67,"soil":"Red Loam / Alluvial","soil_ph":6.7,"main_crops":["Paddy","Sugarcane","Banana","Tapioca"],"river":"Sankarabarani","known_for":"Paddy, Sugarcane","lat":11.74,"lon":79.01},
    "Kancheepuram": {"zone":"North Coastal","avg_temp":29,"rainfall_mm":1150,"humidity":73,"soil":"Red Loam / Sandy Loam","soil_ph":6.7,"main_crops":["Paddy","Groundnut","Vegetables","Sugarcane"],"river":"Palar","known_for":"Paddy, Silk weaving","lat":12.83,"lon":79.70},
    "Kanyakumari": {"zone":"Southern Tip","avg_temp":27,"rainfall_mm":1800,"humidity":82,"soil":"Laterite / Alluvial","soil_ph":5.8,"main_crops":["Coconut","Banana","Paddy","Rubber","Vegetables"],"river":"Thamirabarani, Pazhayar","known_for":"Coconut, Banana, Spices","lat":8.09,"lon":77.55},
    "Karur": {"zone":"Central","avg_temp":29,"rainfall_mm":850,"humidity":63,"soil":"Sandy Loam / Red Loam","soil_ph":6.6,"main_crops":["Paddy","Banana","Coconut","Groundnut","Maize"],"river":"Amaravathi, Kaveri","known_for":"Banana, Textiles","lat":10.96,"lon":78.08},
    "Krishnagiri": {"zone":"North-Western","avg_temp":27,"rainfall_mm":950,"humidity":60,"soil":"Red Sandy / Laterite","soil_ph":6.3,"main_crops":["Mango","Groundnut","Paddy","Tomato","Millets"],"river":"Ponnaiyar","known_for":"Mango export hub","lat":12.52,"lon":78.21},
    "Madurai": {"zone":"Southern","avg_temp":31,"rainfall_mm":850,"humidity":65,"soil":"Red Sandy / Black Cotton","soil_ph":7.0,"main_crops":["Paddy","Banana","Jasmine","Groundnut","Maize"],"river":"Vaigai","known_for":"Jasmine flowers, Banana","lat":9.93,"lon":78.12},
    "Mayiladuthurai": {"zone":"Cauvery Delta","avg_temp":29,"rainfall_mm":1100,"humidity":77,"soil":"Alluvial / Clay","soil_ph":7.3,"main_crops":["Paddy","Banana","Sugarcane","Black Gram"],"river":"Cauvery, Arasalar","known_for":"Paddy bowl of TN","lat":11.10,"lon":79.65},
    "Nagapattinam": {"zone":"East Coastal Delta","avg_temp":29,"rainfall_mm":1350,"humidity":80,"soil":"Alluvial / Clay Loam","soil_ph":7.2,"main_crops":["Paddy","Banana","Coconut","Sugarcane"],"river":"Cauvery delta","known_for":"Paddy, Coconut","lat":10.76,"lon":79.84},
    "Namakkal": {"zone":"Central","avg_temp":28,"rainfall_mm":900,"humidity":62,"soil":"Red Sandy / Loam","soil_ph":6.5,"main_crops":["Banana","Coconut","Turmeric","Paddy","Maize"],"river":"Kaveri tributary","known_for":"Poultry, Banana, Eggs","lat":11.22,"lon":78.17},
    "Nilgiris": {"zone":"Western Ghats Hills","avg_temp":17,"rainfall_mm":2200,"humidity":85,"soil":"Loamy / Forest Soil","soil_ph":5.5,"main_crops":["Tea","Coffee","Vegetables","Potato","Carrot"],"river":"Bhavani","known_for":"Tea, Coffee, Hill vegetables","lat":11.49,"lon":76.73},
    "Perambalur": {"zone":"Central","avg_temp":30,"rainfall_mm":900,"humidity":65,"soil":"Red Sandy / Alluvial","soil_ph":6.7,"main_crops":["Paddy","Groundnut","Sugarcane","Pulses"],"river":"Vellar","known_for":"Paddy, Cement industries","lat":11.23,"lon":78.88},
    "Pudukkottai": {"zone":"Southern Central","avg_temp":30,"rainfall_mm":850,"humidity":65,"soil":"Red Sandy / Black Cotton","soil_ph":6.9,"main_crops":["Paddy","Groundnut","Banana","Sugarcane","Pulses"],"river":"Vellar, Amaravathi","known_for":"Groundnut, Paddy","lat":10.38,"lon":78.82},
    "Ramanathapuram": {"zone":"Southern Coast","avg_temp":31,"rainfall_mm":620,"humidity":70,"soil":"Sandy / Red Sandy","soil_ph":6.5,"main_crops":["Paddy","Groundnut","Pearl Millet","Cotton","Coconut"],"river":"Vaigai (lower)","known_for":"Salt, Pearl Millet, Groundnut","lat":9.37,"lon":78.83},
    "Ranipet": {"zone":"North-Western","avg_temp":28,"rainfall_mm":1000,"humidity":65,"soil":"Red Loam / Sandy","soil_ph":6.5,"main_crops":["Paddy","Groundnut","Sugarcane","Millets","Tomato"],"river":"Palar","known_for":"Leather, Paddy","lat":12.92,"lon":79.33},
    "Salem": {"zone":"Central","avg_temp":29,"rainfall_mm":950,"humidity":63,"soil":"Red Loam / Sandy","soil_ph":6.5,"main_crops":["Mango","Banana","Turmeric","Paddy","Tapioca"],"river":"Thirumanimutharu","known_for":"Mango, Turmeric, Steel","lat":11.65,"lon":78.16},
    "Sivaganga": {"zone":"Southern","avg_temp":31,"rainfall_mm":800,"humidity":65,"soil":"Red Sandy / Black Cotton","soil_ph":6.8,"main_crops":["Paddy","Groundnut","Cotton","Banana","Pulses"],"river":"Vaigai tributary","known_for":"Paddy, Groundnut","lat":9.84,"lon":78.48},
    "Tenkasi": {"zone":"Southern Western Ghats","avg_temp":27,"rainfall_mm":1400,"humidity":78,"soil":"Laterite / Loamy","soil_ph":6.0,"main_crops":["Banana","Coconut","Paddy","Rubber","Vegetables"],"river":"Chittar","known_for":"Banana, Rubber, Spices","lat":8.96,"lon":77.32},
    "Thanjavur": {"zone":"Cauvery Delta","avg_temp":29,"rainfall_mm":1050,"humidity":74,"soil":"Alluvial / Clay Loam","soil_ph":7.3,"main_crops":["Paddy","Banana","Sugarcane","Coconut","Black Gram"],"river":"Kaveri, Vennar","known_for":"Rice granary of Tamil Nadu","lat":10.79,"lon":79.14},
    "Theni": {"zone":"Southern Western","avg_temp":28,"rainfall_mm":950,"humidity":66,"soil":"Red Loam / Sandy","soil_ph":6.6,"main_crops":["Banana","Grapes","Turmeric","Paddy","Vegetables"],"river":"Vaigai (upper)","known_for":"Banana, Grapes","lat":10.01,"lon":77.48},
    "Thiruvallur": {"zone":"North Coastal","avg_temp":29,"rainfall_mm":1200,"humidity":73,"soil":"Red Loam / Sandy","soil_ph":6.7,"main_crops":["Paddy","Groundnut","Sugarcane","Vegetables"],"river":"Koratalai, Kusasthalai","known_for":"Paddy, Vegetables","lat":13.14,"lon":79.91},
    "Thiruvarur": {"zone":"Cauvery Delta","avg_temp":29,"rainfall_mm":1150,"humidity":77,"soil":"Alluvial / Clay","soil_ph":7.2,"main_crops":["Paddy","Banana","Sugarcane","Coconut"],"river":"Cauvery delta","known_for":"Paddy, Delta agriculture","lat":10.77,"lon":79.64},
    "Tirunelveli": {"zone":"Southern Tip","avg_temp":31,"rainfall_mm":650,"humidity":62,"soil":"Red Sandy / Alluvial","soil_ph":6.7,"main_crops":["Banana","Paddy","Groundnut","Coconut","Cotton"],"river":"Thamirabarani","known_for":"Banana, Halwa, Groundnut","lat":8.71,"lon":77.76},
    "Tirupathur": {"zone":"North-Western","avg_temp":27,"rainfall_mm":1050,"humidity":64,"soil":"Red Laterite / Sandy Loam","soil_ph":6.3,"main_crops":["Mango","Groundnut","Paddy","Millets","Tomato"],"river":"Ponnaiyar","known_for":"Mango, Hill area farming","lat":12.49,"lon":78.57},
    "Tiruppur": {"zone":"Western","avg_temp":27,"rainfall_mm":680,"humidity":59,"soil":"Red Loam / Sandy Loam","soil_ph":6.5,"main_crops":["Cotton","Banana","Coconut","Maize","Groundnut"],"river":"Noyyal","known_for":"Cotton, Knitwear industry","lat":11.10,"lon":77.34},
    "Tiruvanamalai": {"zone":"North-Eastern","avg_temp":29,"rainfall_mm":1100,"humidity":68,"soil":"Red Sandy / Loam","soil_ph":6.6,"main_crops":["Paddy","Groundnut","Sugarcane","Banana","Millets"],"river":"Pennaiyar","known_for":"Paddy, Groundnut, Temple","lat":12.23,"lon":79.07},
    "Thoothukudi": {"zone":"Southern Coast","avg_temp":30,"rainfall_mm":640,"humidity":74,"soil":"Sandy / Red Sandy Loam","soil_ph":6.6,"main_crops":["Paddy","Groundnut","Cotton","Pearl Millet","Banana"],"river":"Thamirabarani (delta)","known_for":"Salt, Pearl Fishery, Port city","lat":8.76,"lon":78.13},
    "Trichy": {"zone":"Central Delta","avg_temp":30,"rainfall_mm":900,"humidity":68,"soil":"Alluvial / Black Cotton","soil_ph":7.1,"main_crops":["Paddy","Sugarcane","Banana","Pulses","Groundnut"],"river":"Kaveri","known_for":"Paddy, Sugarcane, Tourism","lat":10.79,"lon":78.70},
    "Vellore": {"zone":"North-Western","avg_temp":28,"rainfall_mm":1000,"humidity":65,"soil":"Red Loam / Sandy","soil_ph":6.4,"main_crops":["Groundnut","Paddy","Mango","Tomato","Millets"],"river":"Palar","known_for":"Groundnut, Hospitals, Leather","lat":12.92,"lon":79.13},
    "Viluppuram": {"zone":"Eastern","avg_temp":29,"rainfall_mm":1100,"humidity":70,"soil":"Red Loam / Sandy","soil_ph":6.6,"main_crops":["Paddy","Sugarcane","Groundnut","Banana","Millets"],"river":"Ponnaiyar, Pennaiyar","known_for":"Sugarcane, Paddy","lat":11.94,"lon":79.49},
    "Virudhunagar": {"zone":"Southern","avg_temp":30,"rainfall_mm":750,"humidity":63,"soil":"Red Sandy / Loamy","soil_ph":6.7,"main_crops":["Banana","Paddy","Groundnut","Cotton","Coconut"],"river":"Vaippar","known_for":"Fireworks, Banana, Groundnut","lat":9.58,"lon":77.96},
}

# CROP DATABASE
CROP_DB = {
    "Paddy": {"emoji":"","season":"Samba (Aug-Jan) / Kuruvai (Jun-Sep)","yield_min":4.5,"yield_max":6.0,"price":20000,"cost_ha":35000,"water":"High","days":120,"sell":"APMC Mandi, Uzhavar Sandhai, FCI procurement"},
    "Banana": {"emoji":"","season":"Year-round","yield_min":35,"yield_max":45,"price":15000,"cost_ha":90000,"water":"High","days":300,"sell":"Local market, Chennai wholesale, Export"},
    "Sugarcane": {"emoji":"","season":"Year-round","yield_min":80,"yield_max":100,"price":3150,"cost_ha":120000,"water":"Very High","days":365,"sell":"Sugar mills (TNSC), Cooperative societies"},
    "Coconut": {"emoji":"","season":"Year-round","yield_min":7000,"yield_max":10000,"price":20,"cost_ha":25000,"water":"Medium","days":2190,"sell":"Oil mills, Local traders, Direct retail"},
    "Groundnut": {"emoji":"","season":"Kharif & Rabi","yield_min":2.0,"yield_max":2.5,"price":55000,"cost_ha":38000,"water":"Low","days":100,"sell":"APMC, Oil mills, NAFED procurement"},
    "Turmeric": {"emoji":"","season":"Jun-Dec","yield_min":20,"yield_max":25,"price":70000,"cost_ha":100000,"water":"Medium","days":270,"sell":"Erode market (Asia's largest), Spice board"},
    "Mango": {"emoji":"","season":"Feb-May harvest","yield_min":10,"yield_max":15,"price":30000,"cost_ha":40000,"water":"Low","days":1825,"sell":"Export, Juice factories, Local wholesale"},
    "Cotton": {"emoji":"","season":"Kharif (Jun-Nov)","yield_min":1.5,"yield_max":2.0,"price":65000,"cost_ha":50000,"water":"Medium","days":180,"sell":"CCI, Private ginning mills, APMC"},
    "Tomato": {"emoji":"","season":"Oct-Jan","yield_min":20,"yield_max":25,"price":12000,"cost_ha":60000,"water":"Medium","days":90,"sell":"Koyambedu market, Local mandi, Paste factories"},
    "Maize": {"emoji":"","season":"Kharif & Rabi","yield_min":5,"yield_max":6,"price":17000,"cost_ha":28000,"water":"Low","days":90,"sell":"Poultry feed companies, APMC, Starch factories"},
    "Vegetables": {"emoji":"","season":"Year-round","yield_min":15,"yield_max":20,"price":10000,"cost_ha":50000,"water":"Medium","days":60,"sell":"Uzhavar Sandhai, Koyambedu, Local markets"},
    "Millets": {"emoji":"","season":"Kharif","yield_min":1.0,"yield_max":1.5,"price":25000,"cost_ha":15000,"water":"Very Low","days":75,"sell":"Organic stores, TNCSC, Health food brands"},
    "Pulses": {"emoji":"","season":"Rabi (Nov-Feb)","yield_min":0.8,"yield_max":1.2,"price":60000,"cost_ha":18000,"water":"Low","days":80,"sell":"NAFED, APMC, Local traders"},
    "Jasmine": {"emoji":"","season":"Year-round","yield_min":3,"yield_max":4,"price":200000,"cost_ha":80000,"water":"Medium","days":365,"sell":"Madurai flower market, Wedding contractors"},
    "Tapioca": {"emoji":"","season":"Year-round","yield_min":30,"yield_max":35,"price":5000,"cost_ha":30000,"water":"Low","days":270,"sell":"Sago factories (Salem), Starch units"},
    "Black Gram": {"emoji":"","season":"Rabi (Nov-Feb)","yield_min":0.8,"yield_max":1.0,"price":65000,"cost_ha":20000,"water":"Low","days":75,"sell":"NAFED, Dal mills, APMC"},
    "Pearl Millet": {"emoji":"","season":"Kharif","yield_min":1.2,"yield_max":1.8,"price":22000,"cost_ha":14000,"water":"Very Low","days":75,"sell":"TNCSC, Flour mills, Feed companies"},
    "Grapes": {"emoji":"","season":"Dec-Apr harvest","yield_min":12,"yield_max":18,"price":40000,"cost_ha":150000,"water":"High","days":365,"sell":"Wine companies, Export, Raisin factories"},
    "Tea": {"emoji":"","season":"Year-round (flush)","yield_min":2.5,"yield_max":3.5,"price":180000,"cost_ha":200000,"water":"High","days":1825,"sell":"Tea Board, Auction centres (Coimbatore)"},
    "Coffee": {"emoji":"","season":"Oct-Feb harvest","yield_min":1.0,"yield_max":1.5,"price":250000,"cost_ha":150000,"water":"High","days":1825,"sell":"Coffee Board, Exporters, Cooperatives"},
    "Potato": {"emoji":"","season":"Oct-Jan","yield_min":20,"yield_max":28,"price":12000,"cost_ha":70000,"water":"Medium","days":90,"sell":"Local market, Cold storage, Chips factories"},
    "Rubber": {"emoji":"","season":"Year-round (tapping)","yield_min":1.5,"yield_max":2.0,"price":200000,"cost_ha":80000,"water":"High","days":2555,"sell":"Rubber Board, Tire companies, Cooperatives"},
    "Betel Nut": {"emoji":"","season":"Year-round","yield_min":2,"yield_max":3,"price":250000,"cost_ha":80000,"water":"High","days":1825,"sell":"Pan traders, Export market"},
    "Carrot": {"emoji":"","season":"Oct-Feb (hills)","yield_min":20,"yield_max":28,"price":15000,"cost_ha":55000,"water":"Medium","days":90,"sell":"Local markets, Chennai, Hotels"},
}

# CROP EXCLUSION MAP
CROP_EXCLUSION = {
    "Tea": {
        "exclude_districts": [
            "Chennai","Chengalpattu","Kancheepuram","Thiruvallur","Cuddalore",
            "Nagapattinam","Thanjavur","Thiruvarur","Mayiladuthurai","Trichy",
            "Karur","Perambalur","Ariyalur","Kallakurichi","Villupuram",
            "Madurai","Dindigul","Sivaganga","Ramanathapuram","Thoothukudi",
            "Tirunelveli","Kanyakumari","Virudhunagar","Pudukkottai","Salem",
            "Namakkal","Erode","Dharmapuri","Krishnagiri","Vellore","Ranipet",
            "Tirupathur","Tiruvanamalai"
        ],
        "exclude_zones": [
            "Coastal","Delta","Central","Southern","North Coastal","East Coastal",
            "Cauvery Delta","Southern Coast","Southern Tip"
        ]
    },
    "Coffee": {
        "exclude_districts": [
            "Chennai","Chengalpattu","Kancheepuram","Thiruvallur","Cuddalore",
            "Nagapattinam","Thanjavur","Thiruvarur","Mayiladuthurai","Trichy",
            "Karur","Perambalur","Ariyalur","Kallakurichi","Villupuram",
            "Madurai","Sivaganga","Ramanathapuram","Thoothukudi","Tirunelveli",
            "Pudukkottai","Salem","Namakkal","Erode","Vellore","Ranipet",
            "Tiruvanamalai","Coimbatore","Tiruppur"
        ],
        "exclude_zones": [
            "Coastal","Delta","Central","Southern Coast","Cauvery Delta",
            "North Coastal","East Coastal"
        ]
    },
    "Rubber": {
        "exclude_districts": [
            "Chennai","Chengalpattu","Kancheepuram","Thiruvallur","Cuddalore",
            "Nagapattinam","Thanjavur","Thiruvarur","Mayiladuthurai","Trichy",
            "Karur","Perambalur","Ariyalur","Kallakurichi","Villupuram",
            "Madurai","Sivaganga","Ramanathapuram","Thoothukudi",
            "Pudukkottai","Salem","Namakkal","Erode","Dharmapuri",
            "Krishnagiri","Vellore","Ranipet","Tiruvanamalai","Coimbatore",
            "Tiruppur"
        ],
        "exclude_zones": [
            "Coastal","Delta","Central","Southern Coast","Cauvery Delta",
            "North Coastal","East Coastal","North-Western","Western"
        ]
    },
    "Potato": {
        "exclude_districts": [
            "Ramanathapuram","Thoothukudi","Tirunelveli","Madurai","Sivaganga",
            "Pudukkottai","Thanjavur","Thiruvarur","Nagapattinam","Mayiladuthurai",
            "Cuddalore","Chennai","Chengalpattu","Kancheepuram","Thiruvallur"
        ],
        "exclude_zones": [
            "Southern Coast","Southern Tip","Cauvery Delta","East Coastal Delta",
            "North Coastal"
        ]
    },
    "Carrot": {
        "exclude_districts": [
            "Ramanathapuram","Thoothukudi","Tirunelveli","Madurai","Sivaganga",
            "Pudukkottai","Thanjavur","Thiruvarur","Nagapattinam","Mayiladuthurai",
            "Cuddalore","Chennai","Chengalpattu","Kancheepuram","Thiruvallur",
            "Trichy","Karur","Perambalur","Ariyalur"
        ],
        "exclude_zones": [
            "Southern Coast","Southern Tip","Cauvery Delta","East Coastal Delta",
            "Central Delta","North Coastal","East Coastal","Central"
        ]
    },
    "Grapes": {
        "exclude_districts": [
            "Ramanathapuram","Thoothukudi","Nagapattinam","Mayiladuthurai",
            "Thiruvarur","Cuddalore","Chennai","Kanyakumari","Tenkasi"
        ],
        "exclude_zones": [
            "Southern Coast","East Coastal Delta","Cauvery Delta",
            "North Coastal","Southern Tip","Southern Western Ghats"
        ]
    },
    "Jasmine": {
        "exclude_districts": ["Nilgiris","Ramanathapuram","Thoothukudi"],
        "exclude_zones": ["Western Ghats Hills"]
    },
    "Sugarcane": {
        "exclude_districts": ["Ramanathapuram","Thoothukudi","Nilgiris"],
        "exclude_zones": ["Southern Coast","Western Ghats Hills"]
    },
    "Betel Nut": {
        "exclude_districts": [
            "Ramanathapuram","Thoothukudi","Nilgiris","Dharmapuri","Krishnagiri",
            "Vellore","Ranipet","Tirupathur","Tiruvanamalai"
        ],
        "exclude_zones": [
            "Southern Coast","Western Ghats Hills","North-Western"
        ]
    },
}

# IDEAL GROWING CONDITIONS PER CROP
CROP_IDEAL = {
    "Paddy": {"rain":(900,2500),"temp":(22,35),"ph":(5.5,7.5),"humidity":(70,90)},
    "Banana": {"rain":(750,2500),"temp":(24,35),"ph":(6.0,7.5),"humidity":(60,85)},
    "Sugarcane": {"rain":(750,1800),"temp":(24,38),"ph":(6.0,8.0),"humidity":(55,85)},
    "Coconut": {"rain":(1000,3000),"temp":(24,32),"ph":(5.5,8.0),"humidity":(60,90)},
    "Groundnut": {"rain":(400,1200),"temp":(24,32),"ph":(6.0,7.5),"humidity":(40,75)},
    "Turmeric": {"rain":(1000,2000),"temp":(20,32),"ph":(5.5,7.0),"humidity":(65,90)},
    "Cotton": {"rain":(500,1200),"temp":(25,40),"ph":(6.0,8.0),"humidity":(40,70)},
    "Maize": {"rain":(500,1200),"temp":(18,35),"ph":(5.8,7.5),"humidity":(50,80)},
    "Mango": {"rain":(500,1500),"temp":(24,35),"ph":(5.5,7.5),"humidity":(40,75)},
    "Tomato": {"rain":(400,1200),"temp":(18,30),"ph":(6.0,7.0),"humidity":(50,80)},
    "Vegetables": {"rain":(500,1500),"temp":(18,32),"ph":(5.8,7.2),"humidity":(55,85)},
    "Millets": {"rain":(300,900),"temp":(25,38),"ph":(5.5,7.5),"humidity":(30,65)},
    "Pearl Millet":{"rain":(300,800),"temp":(25,40),"ph":(5.5,7.5),"humidity":(30,65)},
    "Tapioca": {"rain":(750,2000),"temp":(25,35),"ph":(5.5,7.5),"humidity":(55,80)},
    "Tea": {"rain":(1500,3000),"temp":(13,25),"ph":(4.5,6.0),"humidity":(75,90)},
    "Coffee": {"rain":(1200,2500),"temp":(15,25),"ph":(5.5,6.5),"humidity":(70,90)},
    "Rubber": {"rain":(1500,3000),"temp":(25,32),"ph":(4.5,6.5),"humidity":(75,95)},
    "Potato": {"rain":(500,1200),"temp":(10,20),"ph":(5.0,6.5),"humidity":(60,80)},
    "Carrot": {"rain":(400,1000),"temp":(10,22),"ph":(5.5,7.0),"humidity":(55,80)},
    "Grapes": {"rain":(600,1200),"temp":(20,35),"ph":(6.0,7.5),"humidity":(40,75)},
    "Jasmine": {"rain":(600,1200),"temp":(24,35),"ph":(6.0,7.5),"humidity":(55,80)},
    "Black Gram": {"rain":(600,1000),"temp":(25,35),"ph":(6.0,7.5),"humidity":(50,80)},
    "Pulses": {"rain":(400,900),"temp":(20,32),"ph":(6.0,7.5),"humidity":(40,75)},
}

# HISTORICAL YIELD RECORDS
HISTORICAL_YIELD = {
    "Paddy": [3.8,4.0,4.2,4.5,4.8,5.0],"Banana": [28,30,33,36,38,40],
    "Sugarcane": [70,74,78,82,87,90],"Groundnut": [1.4,1.6,1.7,1.9,2.0,2.2],
    "Turmeric": [15,17,18,20,22,23],"Cotton": [1.0,1.1,1.2,1.4,1.5,1.6],
    "Maize": [3.5,4.0,4.2,4.5,4.8,5.0],"Tomato": [14,16,17,19,21,22],
    "Coconut": [7200, 7500, 7800, 8100, 8300, 8500],
    "Mango": [10.5, 11.0, 11.5, 12.0, 12.5, 13.0],
    "Vegetables": [15.5, 16.0, 16.5, 17.0, 17.5, 18.0],
    "Millets": [1.0, 1.1, 1.15, 1.2, 1.25, 1.3],
    "Pulses": [0.8, 0.85, 0.9, 0.95, 1.0, 1.05],
    "Jasmine": [3.0, 3.1, 3.2, 3.3, 3.4, 3.5],
    "Tapioca": [30.0, 31.0, 31.5, 32.0, 32.5, 33.0],
    "Black Gram": [0.8, 0.85, 0.88, 0.92, 0.95, 0.98],
    "Pearl Millet": [1.2, 1.3, 1.4, 1.45, 1.5, 1.6],
    "Grapes": [12.0, 13.0, 13.5, 14.0, 14.5, 15.0],
    "Tea": [2.5, 2.6, 2.7, 2.8, 2.9, 3.0],
    "Coffee": [1.0, 1.1, 1.15, 1.2, 1.25, 1.3],
    "Potato": [20.0, 21.0, 22.0, 23.0, 24.0, 25.0],
    "Rubber": [1.5, 1.6, 1.65, 1.7, 1.75, 1.8],
    "Betel Nut": [2.0, 2.1, 2.2, 2.3, 2.4, 2.5],
    "Carrot": [20.0, 21.0, 21.5, 22.0, 22.5, 23.0]
}
HIST_YEARS = ["2019","2020","2021","2022","2023","2024"]


# MANDI BENCHMARK PRICES & DISTANCES (TN MANDIS)
MANDI_PRICES = {
    "Koyambedu (Chennai)": {"lat": 13.07,"lon": 80.19,"type":"Perishable Wholesale","district":"Chennai"},
    "Oddanchatram (Dindigul)": {"lat": 10.48,"lon": 77.74,"type":"Vegetable & Fruit Hub","district":"Dindigul"},
    "Erode Turmeric Market": {"lat": 11.34,"lon": 77.72,"type":"Turmeric Special APMC","district":"Erode"},
    "Madurai Mattuthavani Mandi": {"lat": 9.94,"lon": 78.15,"type":"Jasmine & General APMC","district":"Madurai"},
    "Trichy Gandhi Market": {"lat": 10.82,"lon": 78.69,"type":"Central Delta Mandi","district":"Trichy"},
    "Uzhavar Sandhai (Local District)": {"lat": 0.0,"lon": 0.0,"type":"Direct Farmer Retail","district":"Local"},
}


# GOVERNMENT SCHEMES DATASET
GOVT_SCHEMES = [
    {
        "id":"pm_kisan",
        "name":"PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "benefit":"Rs. 6,000 per year in 3 equal installments (Rs. 2,000 every 4 months)",
        "eligibility":"All landholding farmer families with cultivable land up to 5 hectares.",
        "category":"Direct Income Support",
        "docs": ["Aadhaar Card","Land Pattadhar Passbook / Chitta","Bank Account linked with Aadhaar"],
        "link":"https://pmkisan.gov.in"
    },
    {
        "id":"pmksy_drip",
        "name":"PMKSY — Micro Irrigation Drip & Sprinkler Subsidy",
        "benefit":"100% subsidy for Small & Marginal Farmers (<2 ha) in TN; 75% subsidy for other farmers.",
        "eligibility":"Farmers with assured water source & valid land title.",
        "category":"Irrigation Subsidy",
        "docs": ["Land Chitta/Adangal","Aadhaar Card","Water test report","Bank passbook copy"],
        "link":"https://tnagrisnet.tn.gov.in"
    },
    {
        "id":"pmfby",
        "name":"PMFBY — Pradhan Mantri Fasal Bima Yojana (Crop Insurance)",
        "benefit":"Low premium rate (1.5% for Rabi, 2% for Kharif, 5% for Annual/Horticultural crops). Covers yield loss & localized disasters.",
        "eligibility":"All farmers growing notified crops in notified areas.",
        "category":"Crop Risk Insurance",
        "docs": ["Adangal / Sowing certificate","Aadhaar","KCC / Bank passbook","Land document"],
        "link":"https://pmfby.gov.in"
    },
    {
        "id":"kcc_loan",
        "name":"Kisan Credit Card (KCC) Subsidized Crop Loan",
        "benefit":"Subsidized crop loans up to Rs. 3 Lakhs at 4% effective annual interest rate (3% prompt repayment incentive).",
        "eligibility":"Owner cultivators, tenant farmers, sharecroppers, and FPO members.",
        "category":"Low-Interest Credit",
        "docs": ["Land revenue record","Identity & address proof","Crop cultivation proposal"],
        "link":"https://www.nabard.org"
    },
    {
        "id":"tnau_seeds",
        "name":"TNSC / TNAU Subsidized Seed Supply Scheme",
        "benefit":"50% cost subsidy on certified paddy, pulse, millet, and oilseed varieties.",
        "eligibility":"Registered TN farmers purchasing through AECs (Agricultural Extension Centres).",
        "category":"Input Subsidy",
        "docs": ["Farmer Registration ID / Aadhaar","Land Chitta"],
        "link":"https://tnagrisnet.tn.gov.in"
    },
    {
        "id":"chc_machinery",
        "name":"SMAM — Agricultural Machinery & Custom Hiring Subsidy",
        "benefit":"40%–50% subsidy on tractors, power tillers, rotavators, and drone sprayers for individual farmers & 80% for FPOs.",
        "eligibility":"Small/marginal farmers, FPOs, and rural youth entrepreneurs.",
        "category":"Farm Mechanization",
        "docs": ["Quotation from approved dealer","Aadhaar","Land record"],
        "link":"https://agrimachinery.nic.in"
    },
    {
        "id":"kalaignar_scheme",
        "name":"Kalaignarin All Village Integrated Agriculture Development Programme",
        "benefit":"Solar pumpset subsidy, borewell creation, farm pond construction & free fruit sapling distribution.",
        "eligibility":"Farmers residing in selected Gram Panchayats under the scheme.",
        "category":"Village Infrastructure",
        "docs": ["Panchayat residency proof","Chitta/Adangal","Aadhaar"],
        "link":"https://tnagrisnet.tn.gov.in"
    },
    {
        "id":"uzhavar_sandhai",
        "name":"Uzhavar Sandhai (Farmers'Direct Market Scheme)",
        "benefit":"Free market stall, free weighing scale, zero commission, and free transport pass for direct retail selling.",
        "eligibility":"Vegetable and fruit growing farmers registered with District Agriculture Officer.",
        "category":"Direct Marketing",
        "docs": ["Uzhavar Sandhai Farmer ID Card","Adangal fruit/veg certification"],
        "link":"https://agri-marketing.tn.gov.in"
    }
]


# PEST & DISEASE DATABASE
PEST_DISEASE_DB = {
    "Paddy": [
        {
            "name":"Rice Blast (Pyricularia oryzae)",
            "type":"Fungal Disease",
            "symptoms":"Spindle-shaped lesions with grey center and reddish-brown margin on leaf and neck rot.",
            "cause":"High humidity (>85%), cooler night temps, over-application of nitrogen.",
            "organic_remedy":"Foliar spray of Panchagavya 3% or Neem seed kernel extract (NSKE) 5%.",
            "chemical_treatment":"Spray Tricyclazole 75% WP @ 0.6 g/L or Azoxystrobin @ 1 mL/L.",
            "prevention":"Avoid excess Urea application; use blast-resistant seeds like CO-51 or ADT-45."
        },
        {
            "name":"Paddy Stem Borer (Scirpophaga incertulas)",
            "type":"Insect Pest",
            "symptoms":"Dead hearts at vegetative stage; white heads (empty panicles) at flowering stage.",
            "cause":"High moth activity in humid weather and continuous rice cropping.",
            "organic_remedy":"Install pheromone traps @ 12 traps/ha; release Trichogramma japonicum egg parasitoid @ 100,000/ha.",
            "chemical_treatment":"Apply Chlorantraniliprole 0.4% GR @ 10 kg/ha or Cartap Hydrochloride 4G.",
            "prevention":"Clip seedling tips before transplanting to destroy egg masses."
        }
    ],
    "Banana": [
        {
            "name":"Panama Wilt (Fusarium oxysporum)",
            "type":"Fungal Disease",
            "symptoms":"Yellowing of lower leaf margins, petiole buckling, vertical splitting of pseudostem base.",
            "cause":"Soil-borne fungus thriving in poorly drained acidic soil.",
            "organic_remedy":"Soil drenching with Trichoderma viride @ 10g/L + Neem cake @ 250g/plant.",
            "chemical_treatment":"Drench pseudostem base with Carbendazim 0.2% (2g/L) or Propiconazole 1 mL/L.",
            "prevention":"Use tissue culture plants; ensure good drainage and lime application."
        },
        {
            "name":"Sigatoka Leaf Spot (Mycosphaerella musicola)",
            "type":"Fungal Disease",
            "symptoms":"Pale yellow-green streaks on leaves expanding into dark brown oval spots with grey center.",
            "cause":"Rainy humid weather and dense plantation canopy.",
            "organic_remedy":"Spray 1% Bordeaux mixture or 5% Neem oil emulsion.",
            "chemical_treatment":"Spray Mancozeb @ 2.5 g/L or Propiconazole @ 1 mL/L with sticker.",
            "prevention":"Maintain proper plant spacing (1.8m x 1.8m) and remove old infected leaves."
        }
    ],
    "Sugarcane": [
        {
            "name":"Red Rot (Colletotrichum falcatum)",
            "type":"Fungal Disease",
            "symptoms":"Third or fourth leaf wilts, internal stalk shows red discoloration with white cross bands.",
            "cause":"Infected seed setts and waterlogging.",
            "organic_remedy":"Sett treatment with Pseudomonas fluorescens @ 10g/L before planting.",
            "chemical_treatment":"Drench soil with Carbendazim 0.1% or Copper Oxychloride 0.25%.",
            "prevention":"Use hot water treated disease-free setts; plant resistant varieties like Co 0238 / Co 86032."
        }
    ],
    "Tomato": [
        {
            "name":"Tomato Leaf Curl Virus (ToLCV)",
            "type":"Viral Disease (Whitefly vector)",
            "symptoms":"Stunted plant growth, severe upward leaf curling, puckering, and yellowing of margins.",
            "cause":"Transmitted by Whiteflies (Bemisia tabaci) in warm dry weather.",
            "organic_remedy":"Yellow sticky traps @ 25/ha; spray Neem oil 3% or Vermiwash 10%.",
            "chemical_treatment":"Control vector whiteflies with Imidacloprid 17.8% SL @ 0.5 mL/L or Acetamiprid @ 0.2g/L.",
            "prevention":"Use yellow mesh insect nets in nursery; avoid planting near infected crops."
        }
    ],
    "Groundnut": [
        {
            "name":"Tikka Leaf Spot (Cercospora arachidicola)",
            "type":"Fungal Disease",
            "symptoms":"Circular dark brown to black spots surrounded by a yellow halo on upper leaf surface.",
            "cause":"High relative humidity and warm leaf wetness.",
            "organic_remedy":"Spray Cow urine 10% + Asafoetida extract or Panchagavya 3%.",
            "chemical_treatment":"Spray Mancozeb @ 2 g/L or Carbendazim 12% + Mancozeb 63% WP @ 2 g/L.",
            "prevention":"Intercrop with Pearl Millet or Maize; crop rotation with pulses."
        }
    ],
    "Turmeric": [
        {
            "name":"Rhizome Rot (Pythium aphanidermatum)",
            "type":"Fungal / Oomycete",
            "symptoms":"Soft rotted water-soaked rhizomes, foul odor, yellowing of leaves from margins inward.",
            "cause":"Stagnant water and poorly drained heavy soils.",
            "organic_remedy":"Rhizome treatment with Trichoderma viride @ 5g/kg rhizome + Trichoderma soil application.",
            "chemical_treatment":"Drench soil with Metalaxyl 8% + Mancozeb 64% WP @ 2 g/L.",
            "prevention":"Plant on raised beds (30 cm high); ensure efficient field drainage."
        }
    ]
}


# EQUIPMENT & LABOR RATES (TN BENCHMARKS)
EQUIPMENT_RATES = {
    "tractor_plow_hr": 950, # Rs per hour
    "rotavator_hr": 1150, # Rs per hour
    "combine_harvester_acre": 2400,# Rs per acre
    "drone_spray_acre": 450, # Rs per acre
    "drip_install_ha": 45000, # Gross cost before subsidy
    "male_labor_day": 550, # Rs per day
    "female_labor_day": 380, # Rs per day
    "labor_days_per_ha": {
        "Paddy": {"sowing": 15,"weeding": 12,"harvest": 18},
        "Banana": {"sowing": 25,"weeding": 18,"harvest": 22},
        "Sugarcane": {"sowing": 30,"weeding": 20,"harvest": 40},
        "Groundnut": {"sowing": 12,"weeding": 10,"harvest": 15},
        "Turmeric": {"sowing": 25,"weeding": 20,"harvest": 30},
        "Tomato": {"sowing": 20,"weeding": 15,"harvest": 25},
    }
}


# TAMIL UI TRANSLATIONS DICTIONARY
TAMIL_TRANSLATIONS = {
    "app_title":"அக்ரிஸ்மார்ட் தமிழ்நாடு — ஸ்மார்ட் பயிர் ஆலோசகர்",
    "sidebar_tagline":"அனைத்து 38 மாவட்டங்களுக்கான விவசாய வழிகாட்டி",
    "connected":"பின்தளம் இணைக்கப்பட்டது",
    "district":"உங்கள் மாவட்டம்",
    "land_area":"நில பரப்பளவு (ஹெக்டேர்)",
    "start_button":"பயிர் ஆலோசகரைத் தொடங்கு",
    "new_session":"புதிய அமர்வு",
    "tabs": {
        "chat":"பயிர் ஆலோசகர்",
        "pest":"பூச்சி நோயறிதல்",
        "timeline":"பயிர் காலவரிசை",
        "profit":"லாபக் கணக்கீடு",
        "schemes":"அரசு மானியங்கள்",
        "mandi":"சந்தை விலை ஒப்பீடு",
        "equipment":"இயந்திரங்கள் & கூலி",
        "weather_risk":"காலநிலை ஆபத்து",
        "report":"முழு பண்ணை அறிக்கை"
    },
    "metrics": {
        "temp":"வெப்பநிலை",
        "rain":"மழைப்பொழிவு",
        "soil_ph":"மண் pH",
        "profit":"மதிப்பிடப்பட்ட லாபம்",
        "roi":"லாப சதவீதம் (ROI)",
        "yield":"எதிர்பார்க்கப்படும் விளைச்சல்"
    }
}


# CROP AGRONOMY DATA (Seed Planner & Plant Population)
CROP_AGRONOMY = {
    "Paddy": {"seed_rate_kg_acre": 15, "row_spacing_cm": 20, "plant_spacing_cm": 15, "germination_pct": 85, "seed_price_per_kg": 40, "varieties": ["ADT 43", "CO 51", "BPT 5204"]},
    "Banana": {"seed_rate_kg_acre": 1000, "row_spacing_cm": 180, "plant_spacing_cm": 180, "germination_pct": 95, "seed_price_per_kg": 15, "varieties": ["Grand Naine", "Poovan", "Nendran"]},
    "Sugarcane": {"seed_rate_kg_acre": 3000, "row_spacing_cm": 90, "plant_spacing_cm": 45, "germination_pct": 90, "seed_price_per_kg": 3, "varieties": ["Co 86032", "Co 0238"]},
    "Coconut": {"seed_rate_kg_acre": 70, "row_spacing_cm": 750, "plant_spacing_cm": 750, "germination_pct": 90, "seed_price_per_kg": 100, "varieties": ["Chowghat Orange Dwarf", "West Coast Tall"]},
    "Groundnut": {"seed_rate_kg_acre": 50, "row_spacing_cm": 30, "plant_spacing_cm": 10, "germination_pct": 80, "seed_price_per_kg": 80, "varieties": ["VRI 2", "TMV 7", "CO 7"]},
    "Turmeric": {"seed_rate_kg_acre": 1000, "row_spacing_cm": 45, "plant_spacing_cm": 15, "germination_pct": 90, "seed_price_per_kg": 60, "varieties": ["BSR 1", "BSR 2", "CO 1"]},
    "Mango": {"seed_rate_kg_acre": 40, "row_spacing_cm": 1000, "plant_spacing_cm": 1000, "germination_pct": 95, "seed_price_per_kg": 150, "varieties": ["Alphonso", "Banganapalli", "Neelum"]},
    "Cotton": {"seed_rate_kg_acre": 2.5, "row_spacing_cm": 90, "plant_spacing_cm": 45, "germination_pct": 75, "seed_price_per_kg": 800, "varieties": ["MCU 5", "Surabhi", "Suvin"]},
    "Tomato": {"seed_rate_kg_acre": 0.1, "row_spacing_cm": 60, "plant_spacing_cm": 45, "germination_pct": 85, "seed_price_per_kg": 5000, "varieties": ["PKM 1", "CO 3", "Shivam"]},
    "Maize": {"seed_rate_kg_acre": 8, "row_spacing_cm": 60, "plant_spacing_cm": 25, "germination_pct": 90, "seed_price_per_kg": 200, "varieties": ["CO 6", "NK 6240"]},
    "Vegetables": {"seed_rate_kg_acre": 2, "row_spacing_cm": 45, "plant_spacing_cm": 30, "germination_pct": 80, "seed_price_per_kg": 1500, "varieties": ["Various local varieties"]},
    "Millets": {"seed_rate_kg_acre": 4, "row_spacing_cm": 25, "plant_spacing_cm": 10, "germination_pct": 85, "seed_price_per_kg": 60, "varieties": ["CO (Te) 7", "CO 10"]},
    "Pulses": {"seed_rate_kg_acre": 8, "row_spacing_cm": 30, "plant_spacing_cm": 10, "germination_pct": 85, "seed_price_per_kg": 120, "varieties": ["VBN 8", "CO 6"]},
    "Jasmine": {"seed_rate_kg_acre": 1000, "row_spacing_cm": 120, "plant_spacing_cm": 120, "germination_pct": 95, "seed_price_per_kg": 20, "varieties": ["Madurai Malli", "CO 1"]},
    "Tapioca": {"seed_rate_kg_acre": 4000, "row_spacing_cm": 90, "plant_spacing_cm": 90, "germination_pct": 95, "seed_price_per_kg": 2, "varieties": ["CO 2", "CO 3", "MVD 1"]},
    "Black Gram": {"seed_rate_kg_acre": 8, "row_spacing_cm": 30, "plant_spacing_cm": 10, "germination_pct": 85, "seed_price_per_kg": 100, "varieties": ["VBN 8", "VBN 11"]},
    "Pearl Millet": {"seed_rate_kg_acre": 2, "row_spacing_cm": 45, "plant_spacing_cm": 15, "germination_pct": 85, "seed_price_per_kg": 80, "varieties": ["CO 9", "CO (Cu) 9"]},
    "Grapes": {"seed_rate_kg_acre": 600, "row_spacing_cm": 300, "plant_spacing_cm": 200, "germination_pct": 95, "seed_price_per_kg": 50, "varieties": ["Muscat Hamburg", "Thomson Seedless"]},
    "Tea": {"seed_rate_kg_acre": 4000, "row_spacing_cm": 120, "plant_spacing_cm": 60, "germination_pct": 95, "seed_price_per_kg": 15, "varieties": ["UPASI-9", "TRF-1"]},
    "Coffee": {"seed_rate_kg_acre": 1200, "row_spacing_cm": 200, "plant_spacing_cm": 200, "germination_pct": 95, "seed_price_per_kg": 25, "varieties": ["Arabica", "Robusta"]},
    "Potato": {"seed_rate_kg_acre": 800, "row_spacing_cm": 60, "plant_spacing_cm": 20, "germination_pct": 95, "seed_price_per_kg": 40, "varieties": ["Kufri Jyoti", "Kufri Giriraj"]},
    "Rubber": {"seed_rate_kg_acre": 150, "row_spacing_cm": 450, "plant_spacing_cm": 450, "germination_pct": 90, "seed_price_per_kg": 50, "varieties": ["RRII 105", "PB 260"]},
    "Betel Nut": {"seed_rate_kg_acre": 500, "row_spacing_cm": 270, "plant_spacing_cm": 270, "germination_pct": 90, "seed_price_per_kg": 20, "varieties": ["Mangala", "Sumangala"]},
    "Carrot": {"seed_rate_kg_acre": 2, "row_spacing_cm": 30, "plant_spacing_cm": 5, "germination_pct": 80, "seed_price_per_kg": 800, "varieties": ["Ooty 1", "Pusa Kesar"]},
}

# ─────────────────────────────────────────────────────────────────────────────
# HARVESTLINE MERGER DATASETS: SHELF LIFE, INITIAL LISTINGS, DEMANDS & DRIVERS
# ─────────────────────────────────────────────────────────────────────────────

CROP_SHELF_LIFE = {
    "Tomato": {"shelf_life_hours": 120, "ideal_temp_c": 12.0, "decay_rate_pct_hr": 0.8},
    "Banana": {"shelf_life_hours": 168, "ideal_temp_c": 13.5, "decay_rate_pct_hr": 0.55},
    "Vegetables": {"shelf_life_hours": 96, "ideal_temp_c": 8.0, "decay_rate_pct_hr": 1.0},
    "Mango": {"shelf_life_hours": 192, "ideal_temp_c": 11.0, "decay_rate_pct_hr": 0.45},
    "Jasmine": {"shelf_life_hours": 36, "ideal_temp_c": 5.0, "decay_rate_pct_hr": 2.5},
    "Grapes": {"shelf_life_hours": 144, "ideal_temp_c": 4.0, "decay_rate_pct_hr": 0.65},
    "Potato": {"shelf_life_hours": 720, "ideal_temp_c": 15.0, "decay_rate_pct_hr": 0.12},
    "Carrot": {"shelf_life_hours": 240, "ideal_temp_c": 4.0, "decay_rate_pct_hr": 0.35},
    "Groundnut": {"shelf_life_hours": 2160, "ideal_temp_c": 20.0, "decay_rate_pct_hr": 0.04},
    "Paddy": {"shelf_life_hours": 4320, "ideal_temp_c": 22.0, "decay_rate_pct_hr": 0.02},
    "Maize": {"shelf_life_hours": 1440, "ideal_temp_c": 18.0, "decay_rate_pct_hr": 0.06},
    "Coconut": {"shelf_life_hours": 2880, "ideal_temp_c": 25.0, "decay_rate_pct_hr": 0.03},
    "Sugarcane": {"shelf_life_hours": 72, "ideal_temp_c": 10.0, "decay_rate_pct_hr": 1.3},
    "Turmeric": {"shelf_life_hours": 4320, "ideal_temp_c": 20.0, "decay_rate_pct_hr": 0.02},
}

INITIAL_SUPPLY_LISTINGS = [
    {
        "id": "SUP-101",
        "farmer_name": "Ramasamy K.",
        "phone": "9840012345",
        "crop": "Tomato",
        "quantity_kg": 400,
        "unit": "kg",
        "price_per_kg": 22.0,
        "district": "Thoothukudi",
        "area": "Sattur Road",
        "harvest_hours_ago": 18,
        "credit_score": 760,
        "status": "ACTIVE"
    },
    {
        "id": "SUP-102",
        "farmer_name": "Muthu V.",
        "phone": "9840054321",
        "crop": "Tomato",
        "quantity_kg": 350,
        "unit": "kg",
        "price_per_kg": 20.0,
        "district": "Virudhunagar",
        "area": "Rajapalayam",
        "harvest_hours_ago": 72,
        "credit_score": 680,
        "status": "ACTIVE"
    },
    {
        "id": "SUP-103",
        "farmer_name": "Karthik S.",
        "phone": "9840098765",
        "crop": "Banana",
        "quantity_kg": 1200,
        "unit": "kg",
        "price_per_kg": 16.0,
        "district": "Madurai",
        "area": "Vadipatti",
        "harvest_hours_ago": 24,
        "credit_score": 810,
        "status": "ACTIVE"
    },
    {
        "id": "SUP-104",
        "farmer_name": "Shanmugam P.",
        "phone": "9840011223",
        "crop": "Tomato",
        "quantity_kg": 500,
        "unit": "kg",
        "price_per_kg": 24.0,
        "district": "Sivakasi",
        "area": "Thiruthangal",
        "harvest_hours_ago": 6,
        "credit_score": 790,
        "status": "ACTIVE"
    },
    {
        "id": "SUP-105",
        "farmer_name": "Velu M.",
        "phone": "9840033445",
        "crop": "Jasmine",
        "quantity_kg": 80,
        "unit": "kg",
        "price_per_kg": 180.0,
        "district": "Madurai",
        "area": "Melur",
        "harvest_hours_ago": 12,
        "credit_score": 740,
        "status": "ACTIVE"
    }
]

INITIAL_BUYER_DEMANDS = [
    {
        "id": "DEM-201",
        "buyer_name": "Annapoorna Restaurant Group",
        "buyer_type": "Restaurant",
        "raw_text": "Need 600 kg fresh quality tomatoes in Sattur / Sivakasi region around Rs.22/kg by tomorrow morning.",
        "crop": "Tomato",
        "quantity_kg": 600,
        "max_price_per_kg": 25.0,
        "district": "Sivakasi",
        "min_freshness_pct": 70,
        "status": "OPEN"
    },
    {
        "id": "DEM-202",
        "buyer_name": "Koyambedu Wholesale Mart",
        "buyer_type": "Wholesaler",
        "raw_text": "Require 1500 kg fresh Grand Naine bananas near Madurai / Dindigul at max Rs.18/kg.",
        "crop": "Banana",
        "quantity_kg": 1500,
        "max_price_per_kg": 18.0,
        "district": "Madurai",
        "min_freshness_pct": 80,
        "status": "OPEN"
    }
]

INITIAL_DRIVER_VEHICLES = [
    {
        "id": "DRV-301",
        "driver_name": "Sundaram T.",
        "vehicle_reg": "TN 67 AD 4521",
        "vehicle_type": "Refrigerated Mini Truck (3.5 Ton)",
        "district": "Sivakasi",
        "cooler_status": "ON",
        "current_temp_c": 4.5,
        "target_temp_c": 4.0,
        "assigned_route": ["Sattur Farm Pool", "Virudhunagar Collection Hub", "Madurai Wholesale Market"],
        "total_distance_km": 72.4,
        "est_fuel_saved_liters": 6.8
    }
]

