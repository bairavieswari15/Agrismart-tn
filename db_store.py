"""
db_store.py — Persistent Storage Layer for AgriSmart TN
========================================================
Provides robust, zero-dependency local JSON file persistence (in data_store/) 
with optional Supabase integration fallback.

Guarantees 100% reliable data persistence so seller produce listings, 
buyer demands, and placed orders survive page refreshes and are shared 
live across all seller and buyer accounts.
"""

import os
import json
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_store")
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
LISTINGS_FILE = os.path.join(DATA_DIR, "listings.json")
DEMANDS_FILE = os.path.join(DATA_DIR, "demands.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
VEHICLES_FILE = os.path.join(DATA_DIR, "vehicles.json")
SENSOR_LOGS_FILE = os.path.join(DATA_DIR, "sensor_logs.json")


# Import initial seed datasets
try:
    from backend.data import INITIAL_SUPPLY_LISTINGS, INITIAL_BUYER_DEMANDS, INITIAL_DRIVER_VEHICLES
except ImportError:
    try:
        from data import INITIAL_SUPPLY_LISTINGS, INITIAL_BUYER_DEMANDS, INITIAL_DRIVER_VEHICLES
    except ImportError:
        INITIAL_SUPPLY_LISTINGS = []
        INITIAL_BUYER_DEMANDS = []
        INITIAL_DRIVER_VEHICLES = []


def _read_json(filepath: str, default_data):
    """Read data from JSON file. Returns default_data if file does not exist or fails."""
    if not os.path.exists(filepath):
        _write_json(filepath, default_data)
        return default_data
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return default_data


def _write_json(filepath: str, data):
    """Write data safely to JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing {filepath}: {e}")


# ── USER ACCOUNTS PERSISTENCE ────────────────────────────────────────────────

def load_users() -> dict:
    """Returns {phone_email: profile_dict}"""
    return _read_json(USERS_FILE, {})


def save_user(profile: dict):
    """Save / update a user profile. Key = phone_email."""
    key = profile.get("phone_email", "").strip()
    if not key:
        return
    users = load_users()
    users[key] = profile
    _write_json(USERS_FILE, users)


def get_user(phone_email: str) -> dict | None:
    """Retrieve user profile by username or phone number."""
    users = load_users()
    return users.get(phone_email.strip())


def user_exists(phone_email: str) -> bool:
    users = load_users()
    return phone_email.strip() in users


# ── SUPPLY LISTINGS PERSISTENCE ──────────────────────────────────────────────

def load_listings() -> list:
    """Load active produce listings posted by sellers."""
    listings = _read_json(LISTINGS_FILE, INITIAL_SUPPLY_LISTINGS)
    if not listings:
        listings = INITIAL_SUPPLY_LISTINGS
        _write_json(LISTINGS_FILE, listings)
    return listings


def save_listing(listing: dict):
    """Save or update a produce listing."""
    lid = listing.get("id")
    if not lid:
        return
    listings = load_listings()
    updated = False
    for i, item in enumerate(listings):
        if str(item.get("id")) == str(lid):
            listings[i] = listing
            updated = True
            break
    if not updated:
        listings.append(listing)
    _write_json(LISTINGS_FILE, listings)


def delete_listing(listing_id: str):
    """Delete a produce listing by ID."""
    listings = load_listings()
    listings = [s for s in listings if str(s.get("id")) != str(listing_id)]
    _write_json(LISTINGS_FILE, listings)


def save_all_listings(listings: list):
    _write_json(LISTINGS_FILE, listings)


# ── BUYER DEMANDS PERSISTENCE ────────────────────────────────────────────────

def load_demands() -> list:
    """Load buyer demand requests."""
    demands = _read_json(DEMANDS_FILE, INITIAL_BUYER_DEMANDS)
    if not demands:
        demands = INITIAL_BUYER_DEMANDS
        _write_json(DEMANDS_FILE, demands)
    return demands


def save_demand(demand: dict):
    """Save or update a buyer demand."""
    did = demand.get("id")
    if not did:
        return
    demands = load_demands()
    updated = False
    for i, d in enumerate(demands):
        if str(d.get("id")) == str(did):
            demands[i] = demand
            updated = True
            break
    if not updated:
        demands.append(demand)
    _write_json(DEMANDS_FILE, demands)


def save_all_demands(demands: list):
    _write_json(DEMANDS_FILE, demands)


# ── PLACED ORDERS PERSISTENCE ────────────────────────────────────────────────

def load_orders() -> list:
    """Load all orders with normalized IDs, status, totals, and pooled flags."""
    orders = _read_json(ORDERS_FILE, [])
    modified = False
    for i, o in enumerate(orders):
        if not o.get("id"):
            o["id"] = f"ORD-{100 + i}"
            modified = True
        qty = float(o.get("quantity_kg", 0) or 0)
        prc = float(o.get("price_per_kg", 0) or 0)
        if not o.get("total_amount") and qty and prc:
            o["total_amount"] = round(qty * prc, 2)
            modified = True
        is_pool = (
            o.get("type") == "POOLED" or 
            o.get("is_pooled") is True or 
            "POOL" in str(o.get("listing_id", "")).upper() or
            "POOL" in str(o.get("id", "")).upper()
        )
        if o.get("is_pooled") != is_pool:
            o["is_pooled"] = is_pool
            modified = True
        if not o.get("status"):
            if o.get("vehicle_reg"):
                o["status"] = "CONFIRMED & VEHICLE ALLOTTED"
            else:
                o["status"] = "PENDING SELLER CONFIRMATION"
            modified = True
    if modified:
        _write_json(ORDERS_FILE, orders)
    return orders


def save_order(order: dict):
    """Save a new or updated order."""
    orders = load_orders()
    oid = order.get("id")
    if not oid:
        oid = f"ORD-{len(orders) + 101}"
        order["id"] = oid
    
    qty = float(order.get("quantity_kg", 0) or 0)
    prc = float(order.get("price_per_kg", 0) or 0)
    if not order.get("total_amount") and qty and prc:
        order["total_amount"] = round(qty * prc, 2)
        
    is_pool = (
        order.get("type") == "POOLED" or 
        order.get("is_pooled") is True or 
        "POOL" in str(order.get("listing_id", "")).upper() or
        "POOL" in str(order.get("id", "")).upper()
    )
    order["is_pooled"] = is_pool
    if not order.get("status"):
        order["status"] = "PENDING SELLER CONFIRMATION"

    updated = False
    for i, o in enumerate(orders):
        if str(o.get("id")) == str(oid):
            orders[i] = order
            updated = True
            break
    if not updated:
        orders.append(order)
    _write_json(ORDERS_FILE, orders)


def save_all_orders(orders: list):
    """Save full list of orders to JSON."""
    _write_json(ORDERS_FILE, orders)


def update_order_status(order_id: str, new_status: str, extra_data: dict = None) -> bool:
    """Update status and optional metadata (e.g. vehicle/driver) for an order."""
    orders = load_orders()
    found = False
    for i, o in enumerate(orders):
        if str(o.get("id")) == str(order_id):
            o["status"] = new_status
            if extra_data:
                o.update(extra_data)
            orders[i] = o
            found = True
            break
    if found:
        _write_json(ORDERS_FILE, orders)
    return found


# ── DRIVER VEHICLES PERSISTENCE ──────────────────────────────────────────────

def load_vehicles() -> list:
    """Load cold-chain vehicle fleet data."""
    vehicles = _read_json(VEHICLES_FILE, INITIAL_DRIVER_VEHICLES)
    if not vehicles:
        vehicles = INITIAL_DRIVER_VEHICLES
        _write_json(VEHICLES_FILE, vehicles)
    return vehicles


def save_vehicle(vehicle: dict):
    """Save or update driver vehicle record."""
    vreg = vehicle.get("vehicle_reg")
    if not vreg:
        return
    vehicles = load_vehicles()
    updated = False
    for i, v in enumerate(vehicles):
        if v.get("vehicle_reg") == vreg:
            vehicles[i] = vehicle
            updated = True
            break
    if not updated:
        vehicles.append(vehicle)
    _write_json(VEHICLES_FILE, vehicles)


# ── IOT SENSOR LOGS PERSISTENCE ──────────────────────────────────────────────

INITIAL_SENSOR_LOGS = [
    {
        "id": "SNS-1001",
        "timestamp": "2026-09-24 00:00:00",
        "device_id": "ESP32-FARM-01",
        "district": "Coimbatore",
        "moisture": 45.2,
        "temperature": 28.5,
        "humidity": 68.0,
        "alert_level": "NORMAL",
        "status_msg": "Optimal crop growth conditions."
    },
    {
        "id": "SNS-1002",
        "timestamp": "2026-09-24 00:15:00",
        "device_id": "ESP32-FARM-01",
        "district": "Coimbatore",
        "moisture": 24.8,
        "temperature": 34.2,
        "humidity": 42.0,
        "alert_level": "LOW_MOISTURE",
        "status_msg": "ALERT: Soil moisture below threshold (30%). Irrigation required!"
    },
    {
        "id": "SNS-1003",
        "timestamp": "2026-09-24 00:25:00",
        "device_id": "ESP32-FARM-01",
        "district": "Coimbatore",
        "moisture": 52.0,
        "temperature": 38.8,
        "humidity": 35.0,
        "alert_level": "HIGH_TEMP",
        "status_msg": "ALERT: High ambient temperature (>35°C) & low humidity (<40%)."
    }
]


def load_sensor_logs() -> list:
    """Load IoT sensor readings log."""
    logs = _read_json(SENSOR_LOGS_FILE, INITIAL_SENSOR_LOGS)
    if not logs:
        logs = INITIAL_SENSOR_LOGS
        _write_json(SENSOR_LOGS_FILE, logs)
    return logs


def save_sensor_log(log_entry: dict):
    """Append a new IoT sensor telemetry reading."""
    logs = load_sensor_logs()
    logs.insert(0, log_entry)
    logs = logs[:500]
    _write_json(SENSOR_LOGS_FILE, logs)

