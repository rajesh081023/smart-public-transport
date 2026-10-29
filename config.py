import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration parameters."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'smart_transport_clean_mobility_secret_key_2026')
    
    # Database Settings
    DB_TYPE = os.getenv('DB_TYPE', 'auto').lower()  # 'mysql', 'sqlite', or 'auto'
    
    # MySQL Settings
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'smart_mobility_db')
    
    # SQLite Settings
    SQLITE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.getenv('SQLITE_DB', 'smart_mobility.db'))
    
    # Carbon Emission Factors (grams of CO2 equivalent per passenger-kilometer)
    # References: IPCC Guidelines & Central Pollution Control Board / UK DEFRA standards
    EMISSION_FACTORS = {
        'petrol_car': 171.0,      # Baseline private ICE vehicle
        'diesel_car': 165.0,
        'electric_car': 47.0,     # Based on average power grid carbon intensity
        'electric_bus': 22.0,     # Zero tailpipe, low grid-derived per pax
        'cng_bus': 58.0,          # Clean urban transit bus
        'diesel_bus': 68.0,       # Standard city bus
        'metro': 16.0,            # High capacity rapid transit
        'bicycle': 0.0,           # Active zero emission
        'walking': 0.0            # Active zero emission
    }
    
    # Transport Mode Defaults (speed in km/h, base fare in INR, per km fare in INR)
    TRANSPORT_MODES_META = {
        'walking': {'name': 'Walking', 'speed_kmh': 4.5, 'base_fare': 0.0, 'per_km': 0.0, 'co2_per_km': 0.0, 'icon': 'fa-person-walking'},
        'bicycle': {'name': 'Public Bicycle / E-Bike', 'speed_kmh': 15.0, 'base_fare': 5.0, 'per_km': 1.0, 'co2_per_km': 0.0, 'icon': 'fa-bicycle'},
        'metro': {'name': 'City Metro Rail', 'speed_kmh': 42.0, 'base_fare': 15.0, 'per_km': 2.8, 'co2_per_km': 16.0, 'icon': 'fa-train-subway'},
        'bus': {'name': 'Smart Eco Bus (CNG/Electric)', 'speed_kmh': 24.0, 'base_fare': 10.0, 'per_km': 2.0, 'co2_per_km': 35.0, 'icon': 'fa-bus'},
        'ev': {'name': 'Shared Electric Cab (EV)', 'speed_kmh': 32.0, 'base_fare': 35.0, 'per_km': 12.0, 'co2_per_km': 47.0, 'icon': 'fa-bolt'},
        'car': {'name': 'Private Petrol Car (Baseline)', 'speed_kmh': 30.0, 'base_fare': 40.0, 'per_km': 15.0, 'co2_per_km': 171.0, 'icon': 'fa-car'}
    }
