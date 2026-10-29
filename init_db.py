"""
Database Initialization Script
Run this script to create all tables and populate initial seed data:
    python init_db.py
Supports both MySQL (smart_mobility_db) and SQLite fallback.
"""

import sys
from db import init_db, query_db, ACTIVE_DB_TYPE, determine_active_db

def main():
    print("=" * 60)
    print(" Smart Public Transport & Clean Mobility System - DB Setup")
    print("=" * 60)
    
    active_type = determine_active_db()
    print(f"[*] Target database mode: {active_type.upper()}")
    
    try:
        engine = init_db()
        print(f"[+] Database tables and seed records initialized successfully using {engine.upper()}!")
        
        # Verify counts
        users_count = query_db("SELECT COUNT(*) as count FROM users", one=True)['count']
        routes_count = query_db("SELECT COUNT(*) as count FROM routes", one=True)['count']
        stops_count = query_db("SELECT COUNT(*) as count FROM stops", one=True)['count']
        ev_count = query_db("SELECT COUNT(*) as count FROM ev_charging_stations", one=True)['count']
        feedback_count = query_db("SELECT COUNT(*) as count FROM feedback", one=True)['count']
        
        print("\n--- Seed Verification ---")
        print(f" Users:                {users_count}")
        print(f" Routes:               {routes_count}")
        print(f" Stops:                {stops_count}")
        print(f" EV Charging Stations: {ev_count}")
        print(f" Feedback entries:     {feedback_count}")
        print("-------------------------")
        print("[OK] Ready to run: python app.py")
        print("=" * 60)
    except Exception as e:
        print(f"[!] Initialization error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
