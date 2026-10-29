import os
import math
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from db import query_db, determine_active_db

app = Flask(__name__)
app.config.from_object(Config)


# ====================================================================
# AUTHENTICATION HELPERS & DECORATORS
# ====================================================================

def login_required(f):
    """Ensure user is logged in before accessing route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Ensure user is logged in with admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Admin authentication required.', 'warning')
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            flash('Unauthorized access: Administrator privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_global_context():
    """Inject common variables into all Jinja templates."""
    db_mode = determine_active_db()
    return {
        'current_year': datetime.now().year,
        'current_user': {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email'),
            'role': session.get('role')
        } if 'user_id' in session else None,
        'is_admin': session.get('role') == 'admin',
        'db_mode': db_mode,
        'max': max,
        'min': min
    }


# ====================================================================
# HAVERSINE & MOBILITY CALCULATION HELPERS
# ====================================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two GPS coordinates in kilometers.
    Applies an urban transit factor (1.28) for real-world road network curvature.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    direct_km = R * c
    # Return road network estimated distance (minimum 0.3 km)
    road_km = max(0.3, direct_km * 1.28)
    return round(road_km, 2)


def compute_trip_metrics(distance_km):
    """
    Compute multi-modal comparisons for a given distance.
    Returns comparison dictionary for all modes.
    """
    factors = Config.EMISSION_FACTORS
    meta = Config.TRANSPORT_MODES_META
    
    # Baseline car emissions in kg
    baseline_car_co2_kg = (distance_km * factors['petrol_car']) / 1000.0
    baseline_car_fare = meta['car']['base_fare'] + (distance_km * meta['car']['per_km'])
    baseline_car_time = round((distance_km / meta['car']['speed_kmh']) * 60) + 5

    options = []
    
    modes_to_evaluate = ['walking', 'bicycle', 'metro', 'bus', 'ev', 'car']
    
    for mode_key in modes_to_evaluate:
        info = meta[mode_key]
        speed = info['speed_kmh']
        co2_factor = factors.get(mode_key if mode_key in factors else ('petrol_car' if mode_key == 'car' else 'cng_bus'), 0.0)
        
        # Calculate time (minutes)
        transit_buffer = 4 if mode_key in ['bus', 'metro'] else (2 if mode_key == 'ev' else 0)
        est_time_min = round((distance_km / speed) * 60) + transit_buffer
        
        # Calculate fare (INR)
        fare = round(info['base_fare'] + (distance_km * info['per_km']), 2)
        
        # Calculate emissions in kg
        co2_emitted_kg = round((distance_km * co2_factor) / 1000.0, 3)
        
        # Calculate carbon saved compared to private car
        co2_saved_kg = round(max(0.0, baseline_car_co2_kg - co2_emitted_kg), 3)
        
        # Calorie burn for active mobility
        calories = 0
        if mode_key == 'walking':
            calories = round(distance_km * 65)  # ~65 kcal per km
        elif mode_key == 'bicycle':
            calories = round(distance_km * 38)  # ~38 kcal per km
            
        is_recommended = False
        options.append({
            'mode_key': mode_key,
            'mode_name': info['name'],
            'icon': info['icon'],
            'time_min': est_time_min,
            'cost': fare,
            'co2_emitted_kg': co2_emitted_kg,
            'co2_saved_kg': co2_saved_kg,
            'co2_saving_pct': round((co2_saved_kg / max(0.001, baseline_car_co2_kg)) * 100, 1),
            'calories_burned': calories,
            'is_recommended': False,
            'badges': []
        })

    # Add smart recommendation badges
    # 1. Most Eco-friendly (lowest emissions, ignoring car)
    non_car_options = [o for o in options if o['mode_key'] != 'car']
    
    # Check distance suitable for walking or cycling
    if distance_km <= 2.5:
        # Strongly highlight walking or cycling
        for o in options:
            if o['mode_key'] == 'walking' and distance_km <= 1.5:
                o['badges'].append({'text': 'Best for Health & Zero Carbon', 'color': 'success'})
                o['is_recommended'] = True
            elif o['mode_key'] == 'bicycle':
                o['badges'].append({'text': 'Fastest Eco-Choice', 'color': 'success'})
                if distance_km > 1.5:
                    o['is_recommended'] = True
    else:
        # Distance > 2.5 km: recommend Metro or Bus
        for o in options:
            if o['mode_key'] == 'metro':
                o['badges'].append({'text': 'Fastest Clean Transit', 'color': 'primary'})
                o['is_recommended'] = True
            elif o['mode_key'] == 'bus':
                o['badges'].append({'text': 'Most Affordable Transit', 'color': 'info'})

    # Identify lowest cost and lowest time
    min_cost = min(o['cost'] for o in non_car_options)
    min_time = min(o['time_min'] for o in non_car_options)
    
    for o in options:
        if o['mode_key'] != 'car':
            if o['cost'] == min_cost and not any(b['text'] == 'Lowest Fare' for b in o['badges']):
                o['badges'].append({'text': 'Lowest Fare', 'color': 'teal'})
            if o['time_min'] == min_time and not any('Fastest' in b['text'] for b in o['badges']):
                o['badges'].append({'text': 'Quickest', 'color': 'indigo'})

    return {
        'distance_km': distance_km,
        'baseline_car': {
            'co2_emitted_kg': round(baseline_car_co2_kg, 3),
            'cost': baseline_car_fare,
            'time_min': baseline_car_time
        },
        'options': options
    }


# ====================================================================
# MAIN APPLICATION ROUTES
# ====================================================================

@app.route('/')
def index():
    """Home landing page with interactive summary and live statistics."""
    try:
        # Aggregate statistics
        total_routes = query_db("SELECT COUNT(*) as c FROM routes WHERE is_active = 1", one=True)['c']
        total_stops = query_db("SELECT COUNT(*) as c FROM stops WHERE is_active = 1", one=True)['c']
        total_ev = query_db("SELECT COUNT(*) as c FROM ev_charging_stations WHERE status = 'Available'", one=True)['c']
        total_journeys = query_db("SELECT COUNT(*) as c, COALESCE(SUM(co2_saved_kg), 0) as saved FROM journeys", one=True)
        
        # Featured clean routes
        featured_routes = query_db("""
            SELECT r.*, COUNT(rs.id) as stop_count 
            FROM routes r 
            LEFT JOIN route_stops rs ON r.id = rs.route_id 
            WHERE r.is_active = 1 
            GROUP BY r.id 
            ORDER BY r.distance_km ASC 
            LIMIT 4
        """)
        
        # Recent high ratings
        reviews = query_db("""
            SELECT name, rating, comment, category, created_at 
            FROM feedback 
            WHERE rating >= 4 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        
        # Stops for quick search dropdown
        stops = query_db("SELECT id, stop_code, stop_name, city_zone FROM stops WHERE is_active = 1 ORDER BY stop_name ASC")
        
        stats = {
            'routes': total_routes,
            'stops': total_stops,
            'ev_stations': total_ev,
            'journeys_planned': total_journeys['c'],
            'co2_saved_kg': round(total_journeys['saved'], 1)
        }
    except Exception as e:
        print(f"[ERROR in index]: {e}")
        stats = {'routes': 7, 'stops': 12, 'ev_stations': 8, 'journeys_planned': 24, 'co2_saved_kg': 58.4}
        featured_routes = []
        reviews = []
        stops = []

    return render_template('index.html', stats=stats, featured_routes=featured_routes, reviews=reviews, stops=stops)


# ====================================================================
# USER AUTHENTICATION ROUTES
# ====================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route with secure password hashing."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        phone = request.form.get('phone', '').strip()

        # Validation
        if not full_name or not email or not password:
            flash('Please fill in all mandatory fields.', 'warning')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'danger')
            return render_template('register.html')

        # Check existing email
        existing_user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
        if existing_user:
            flash('An account with this email address already exists. Please log in.', 'info')
            return redirect(url_for('login'))

        # Insert user
        password_hash = generate_password_hash(password)
        try:
            res = query_db(
                "INSERT INTO users (full_name, email, password_hash, phone, role) VALUES (%s, %s, %s, %s, 'user')",
                (full_name, email, password_hash, phone),
                commit=True
            )
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Registration error: {e}', 'danger')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User and Administrator login route."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        next_url = request.args.get('next')

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('login.html')

        user = query_db("SELECT * FROM users WHERE email = %s", (email,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            session['role'] = user['role']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session and log user out."""
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('index'))


# ====================================================================
# USER DASHBOARD
# ====================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Personalized user dashboard displaying travel logs and green statistics."""
    user_id = session['user_id']
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
    
    # User's saved journeys
    journeys = query_db("""
        SELECT * FROM journeys 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 10
    """, (user_id,))
    
    # Aggregated user impact
    user_stats = query_db("""
        SELECT 
            COUNT(*) as total_trips,
            COALESCE(SUM(distance_km), 0) as total_distance,
            COALESCE(SUM(co2_saved_kg), 0) as total_co2_saved,
            COALESCE(SUM(travel_cost), 0) as total_spent
        FROM journeys 
        WHERE user_id = %s
    """, (user_id,), one=True)
    
    # Calculate trees equivalent (1 tree absorbs ~21.7 kg CO2/year)
    trees_equivalent = round(user_stats['total_co2_saved'] / 21.7, 2)
    
    # User's submitted feedback
    user_feedbacks = query_db("""
        SELECT * FROM feedback 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 5
    """, (user_id,))

    return render_template(
        'dashboard.html',
        user=user,
        journeys=journeys,
        stats=user_stats,
        trees_equivalent=trees_equivalent,
        feedbacks=user_feedbacks
    )


# ====================================================================
# SMART JOURNEY PLANNER
# ====================================================================

@app.route('/journey-planner')
def journey_planner():
    """Interactive Smart Journey Planner view."""
    stops = query_db("SELECT * FROM stops WHERE is_active = 1 ORDER BY stop_name ASC")
    transport_modes = query_db("SELECT * FROM transport_modes ORDER BY id ASC")
    return render_template('journey_planner.html', stops=stops, transport_modes=transport_modes)


@app.route('/api/plan-journey', methods=['POST'])
def api_plan_journey():
    """
    API endpoint calculating multi-modal travel options, distance, duration,
    cost, emissions, and smart clean recommendations.
    """
    data = request.get_json() or request.form
    origin_id = data.get('origin_id')
    destination_id = data.get('destination_id')
    custom_distance = data.get('custom_distance')

    origin_stop = None
    dest_stop = None
    distance_km = 0.0

    if origin_id and destination_id:
        if str(origin_id) == str(destination_id):
            return jsonify({'error': 'Origin and Destination must be different transit stops.'}), 400
        
        origin_stop = query_db("SELECT * FROM stops WHERE id = %s", (origin_id,), one=True)
        dest_stop = query_db("SELECT * FROM stops WHERE id = %s", (destination_id,), one=True)
        
        if not origin_stop or not dest_stop:
            return jsonify({'error': 'Selected transit stops were not found.'}), 404
            
        distance_km = haversine_distance(
            float(origin_stop['latitude']), float(origin_stop['longitude']),
            float(dest_stop['latitude']), float(dest_stop['longitude'])
        )
    elif custom_distance:
        try:
            distance_km = float(custom_distance)
            if distance_km <= 0 or distance_km > 200:
                return jsonify({'error': 'Please provide a realistic distance between 0.5 km and 200 km.'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid distance value.'}), 400
    else:
        return jsonify({'error': 'Please select origin and destination stops or specify a distance.'}), 400

    metrics = compute_trip_metrics(distance_km)
    
    # Relevant EV charging stations near origin/destination
    nearby_ev = []
    if origin_stop:
        nearby_ev = query_db("""
            SELECT id, station_name, operator, address, latitude, longitude, 
                   power_rating, available_ports, total_ports, price_per_kwh, status 
            FROM ev_charging_stations 
            WHERE status != 'Maintenance' 
            LIMIT 5
        """)

    # Relevant bus or metro direct routes
    direct_routes = []
    if origin_stop and dest_stop:
        direct_routes = query_db("""
            SELECT DISTINCT r.* 
            FROM routes r 
            JOIN route_stops rs1 ON r.id = rs1.route_id AND rs1.stop_id = %s
            JOIN route_stops rs2 ON r.id = rs2.route_id AND rs2.stop_id = %s
            WHERE rs1.stop_sequence < rs2.stop_sequence AND r.is_active = 1
        """, (origin_stop['id'], dest_stop['id']))

    response = {
        'success': True,
        'distance_km': distance_km,
        'origin': origin_stop,
        'destination': dest_stop,
        'options': metrics['options'],
        'baseline_car': metrics['baseline_car'],
        'direct_routes': direct_routes,
        'nearby_ev_stations': nearby_ev
    }
    return jsonify(response)


@app.route('/api/save-journey', methods=['POST'])
@login_required
def api_save_journey():
    """Save a planned journey to the logged-in user's profile."""
    data = request.get_json() or request.form
    user_id = session['user_id']
    origin = data.get('origin', 'Custom Origin')
    destination = data.get('destination', 'Custom Destination')
    distance_km = float(data.get('distance_km', 0.0))
    selected_mode = data.get('selected_mode', 'bus')
    travel_time_min = int(data.get('travel_time_min', 0))
    travel_cost = float(data.get('travel_cost', 0.0))
    co2_emitted_kg = float(data.get('co2_emitted_kg', 0.0))
    co2_saved_kg = float(data.get('co2_saved_kg', 0.0))

    if distance_km <= 0:
        return jsonify({'error': 'Invalid journey distance.'}), 400

    query_db("""
        INSERT INTO journeys (user_id, origin, destination, distance_km, selected_mode, 
                              travel_time_min, travel_cost, co2_emitted_kg, co2_saved_kg)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (user_id, origin, destination, distance_km, selected_mode,
          travel_time_min, travel_cost, co2_emitted_kg, co2_saved_kg), commit=True)

    return jsonify({'success': True, 'message': 'Journey saved to your profile history!'})


# ====================================================================
# PUBLIC TRANSPORT ROUTES
# ====================================================================

@app.route('/transport-routes')
def transport_routes():
    """Browse public transit bus, metro, and EV routes."""
    mode_filter = request.args.get('mode', 'all')
    search_query = request.args.get('q', '').strip()
    
    sql = "SELECT * FROM routes WHERE is_active = 1"
    params = []

    if mode_filter != 'all':
        sql += " AND mode_type = %s"
        params.append(mode_filter)

    if search_query:
        sql += " AND (route_number LIKE %s OR route_name LIKE %s OR origin LIKE %s OR destination LIKE %s)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term, like_term])

    sql += " ORDER BY mode_type DESC, route_number ASC"
    routes = query_db(sql, tuple(params))
    
    # Attach stops count and next schedule for each route
    current_time_str = datetime.now().strftime('%H:%M:%S')
    for r in routes:
        stops_list = query_db("""
            SELECT s.id, s.stop_name, s.stop_code, s.latitude, s.longitude, rs.stop_sequence, rs.time_from_origin_min, rs.fare_from_origin
            FROM route_stops rs
            JOIN stops s ON rs.stop_id = s.id
            WHERE rs.route_id = %s
            ORDER BY rs.stop_sequence ASC
        """, (r['id'],))
        r['stops'] = stops_list
        r['stop_count'] = len(stops_list)
        
        # Next upcoming schedule
        next_sch = query_db("""
            SELECT departure_time, vehicle_number 
            FROM schedules 
            WHERE route_id = %s AND departure_time >= %s AND is_active = 1
            ORDER BY departure_time ASC 
            LIMIT 1
        """, (r['id'], current_time_str), one=True)
        
        if not next_sch:
            # Wrap around to earliest schedule of the day
            next_sch = query_db("""
                SELECT departure_time, vehicle_number 
                FROM schedules 
                WHERE route_id = %s AND is_active = 1
                ORDER BY departure_time ASC 
                LIMIT 1
            """, (r['id'],), one=True)
            
        r['next_schedule'] = next_sch

    all_stops = query_db("SELECT * FROM stops WHERE is_active = 1 ORDER BY stop_name ASC")

    return render_template(
        'transport_routes.html',
        routes=routes,
        all_stops=all_stops,
        current_filter=mode_filter,
        search_query=search_query
    )


@app.route('/api/route/<int:route_id>/details')
def api_route_details(route_id):
    """Retrieve detailed route stops, schedules, and GPS coordinates for map plotting."""
    route = query_db("SELECT * FROM routes WHERE id = %s", (route_id,), one=True)
    if not route:
        return jsonify({'error': 'Route not found'}), 404

    stops = query_db("""
        SELECT s.id, s.stop_code, s.stop_name, s.latitude, s.longitude, s.stop_type, s.city_zone,
               rs.stop_sequence, rs.time_from_origin_min, rs.fare_from_origin
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.id
        WHERE rs.route_id = %s
        ORDER BY rs.stop_sequence ASC
    """, (route_id,))

    schedules = query_db("""
        SELECT * FROM schedules 
        WHERE route_id = %s AND is_active = 1 
        ORDER BY departure_time ASC
    """, (route_id,))

    return jsonify({
        'route': route,
        'stops': stops,
        'schedules': schedules
    })


# ====================================================================
# CLEAN MOBILITY & EV RECOMMENDATIONS
# ====================================================================

@app.route('/clean-mobility')
def clean_mobility():
    """Clean mobility hub highlighting active transport, EV charging directory, and eco benefits."""
    operator_filter = request.args.get('operator', 'all')
    status_filter = request.args.get('status', 'all')
    
    sql = "SELECT * FROM ev_charging_stations WHERE 1=1"
    params = []

    if operator_filter != 'all':
        sql += " AND operator = %s"
        params.append(operator_filter)

    if status_filter != 'all':
        sql += " AND status = %s"
        params.append(status_filter)

    sql += " ORDER BY status ASC, station_name ASC"
    stations = query_db(sql, tuple(params))
    
    operators = query_db("SELECT DISTINCT operator FROM ev_charging_stations ORDER BY operator ASC")

    return render_template(
        'clean_mobility.html',
        stations=stations,
        operators=operators,
        selected_operator=operator_filter,
        selected_status=status_filter
    )


@app.route('/api/ev-stations')
def api_ev_stations():
    """Return JSON list of all EV charging stations for Leaflet map markers."""
    stations = query_db("SELECT * FROM ev_charging_stations")
    return jsonify({'stations': stations})


# ====================================================================
# CARBON EMISSION CALCULATOR
# ====================================================================

@app.route('/carbon-calculator')
def carbon_calculator():
    """Interactive carbon footprint comparison tool and environmental analytics."""
    factors = Config.EMISSION_FACTORS
    return render_template('carbon_calculator.html', factors=factors)


@app.route('/api/calculate-emissions', methods=['POST'])
def api_calculate_emissions():
    """
    API endpoint calculating emissions across all transit modes for single,
    daily, monthly, or annual commutes.
    """
    data = request.get_json() or request.form
    try:
        distance_km = float(data.get('distance_km', 10.0))
        trips_per_day = int(data.get('trips_per_day', 2)) # Commute round-trip = 2
        period = data.get('period', 'annual') # 'single', 'weekly', 'monthly', 'annual'
    except ValueError:
        return jsonify({'error': 'Invalid calculation inputs.'}), 400

    # Multipliers
    period_days = {
        'single': 1,
        'weekly': 5,
        'monthly': 22,
        'annual': 250
    }.get(period, 250)
    
    total_km = distance_km * trips_per_day * period_days
    
    factors = Config.EMISSION_FACTORS
    
    results = {}
    baseline_car_kg = (total_km * factors['petrol_car']) / 1000.0

    mode_list = [
        {'key': 'walking', 'name': 'Walking', 'factor': factors['walking'], 'icon': 'fa-person-walking', 'color': '#10b981'},
        {'key': 'bicycle', 'name': 'Bicycle / E-Bike', 'factor': factors['bicycle'], 'icon': 'fa-bicycle', 'color': '#059669'},
        {'key': 'metro', 'name': 'Electric Metro Rail', 'factor': factors['metro'], 'icon': 'fa-train-subway', 'color': '#0284c7'},
        {'key': 'electric_bus', 'name': 'Clean Electric Bus', 'factor': factors['electric_bus'], 'icon': 'fa-bus-simple', 'color': '#06b6d4'},
        {'key': 'cng_bus', 'name': 'Eco CNG Bus', 'factor': factors['cng_bus'], 'icon': 'fa-bus', 'color': '#f59e0b'},
        {'key': 'electric_car', 'name': 'Shared Electric Car (EV)', 'factor': factors['electric_car'], 'icon': 'fa-bolt', 'color': '#8b5cf6'},
        {'key': 'petrol_car', 'name': 'Private Petrol Car (Baseline)', 'factor': factors['petrol_car'], 'icon': 'fa-car', 'color': '#ef4444'}
    ]

    breakdown = []
    for m in mode_list:
        emitted_kg = round((total_km * m['factor']) / 1000.0, 2)
        saved_kg = round(max(0.0, baseline_car_kg - emitted_kg), 2)
        pct_saved = round((saved_kg / max(0.001, baseline_car_kg)) * 100, 1)
        trees_needed = round(emitted_kg / 21.7, 1) # 1 tree absorbs ~21.7 kg CO2/year
        
        breakdown.append({
            'mode_key': m['key'],
            'name': m['name'],
            'icon': m['icon'],
            'color': m['color'],
            'emitted_kg': emitted_kg,
            'saved_kg': saved_kg,
            'pct_saved': pct_saved,
            'trees_needed': trees_needed
        })

    # Fuel cost estimation saved: Assuming petrol cost ₹102/L and average mileage 14 km/L -> ~₹7.3/km
    fuel_cost_car = round(total_km * 7.28, 2)
    metro_fare = round(total_km * 2.80, 2)
    bus_fare = round(total_km * 2.00, 2)
    money_saved_metro = round(max(0.0, fuel_cost_car - metro_fare), 2)

    return jsonify({
        'total_km': total_km,
        'distance_km': distance_km,
        'trips_per_day': trips_per_day,
        'period_days': period_days,
        'period': period,
        'baseline_car_kg': round(baseline_car_kg, 2),
        'breakdown': breakdown,
        'fuel_cost_car': fuel_cost_car,
        'money_saved_metro': money_saved_metro
    })


# ====================================================================
# USER FEEDBACK SYSTEM
# ====================================================================

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """Feedback submission and community testimonials feed."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        category = request.form.get('category', 'General Suggestion')
        rating = request.form.get('rating', '5')
        comment = request.form.get('comment', '').strip()
        user_id = session.get('user_id')

        # Use session info if logged in and fields are blank
        if user_id:
            if not name:
                name = session.get('user_name', 'Verified Commuter')
            if not email:
                email = session.get('user_email', '')

        if not name or not email or not comment:
            flash('Please fill in your name, email, and feedback message.', 'warning')
            return redirect(url_for('feedback'))

        try:
            rating_int = max(1, min(5, int(rating)))
        except ValueError:
            rating_int = 5

        query_db("""
            INSERT INTO feedback (user_id, name, email, category, rating, comment, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Reviewed')
        """, (user_id, name, email, category, rating_int, comment), commit=True)

        flash('Thank you! Your feedback and ratings have been recorded.', 'success')
        return redirect(url_for('feedback'))

    # Load all feedback for community display
    feedbacks = query_db("SELECT * FROM feedback ORDER BY created_at DESC LIMIT 20")
    
    # Rating statistics
    rating_stats = query_db("""
        SELECT 
            COUNT(*) as total_count,
            COALESCE(AVG(rating), 5.0) as avg_rating,
            SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as stars_5,
            SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as stars_4,
            SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as stars_3,
            SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as stars_2,
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as stars_1
        FROM feedback
    """, one=True)

    return render_template('feedback.html', feedbacks=feedbacks, rating_stats=rating_stats)


# ====================================================================
# ADMINISTRATOR DASHBOARD & MANAGEMENT (CRUD)
# ====================================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Administrator control center with real-time analytics and CRUD tables."""
    # System statistics
    users_count = query_db("SELECT COUNT(*) as c FROM users", one=True)['c']
    routes_count = query_db("SELECT COUNT(*) as c FROM routes", one=True)['c']
    stops_count = query_db("SELECT COUNT(*) as c FROM stops", one=True)['c']
    ev_count = query_db("SELECT COUNT(*) as c FROM ev_charging_stations", one=True)['c']
    journeys_stat = query_db("""
        SELECT COUNT(*) as c, COALESCE(SUM(co2_saved_kg), 0) as saved, COALESCE(SUM(distance_km), 0) as km 
        FROM journeys
    """, one=True)
    feedback_stat = query_db("SELECT COUNT(*) as c, COALESCE(AVG(rating), 5.0) as avg_r FROM feedback", one=True)

    # Management table data
    routes = query_db("SELECT * FROM routes ORDER BY id DESC")
    stops = query_db("SELECT * FROM stops ORDER BY id DESC")
    ev_stations = query_db("SELECT * FROM ev_charging_stations ORDER BY id DESC")
    all_users = query_db("SELECT id, full_name, email, phone, role, created_at FROM users ORDER BY created_at DESC")
    feedbacks = query_db("SELECT * FROM feedback ORDER BY created_at DESC")

    # Analytics for charts
    # 1. Journeys by mode
    mode_counts = query_db("""
        SELECT selected_mode, COUNT(*) as trip_count, COALESCE(SUM(co2_saved_kg), 0) as saved_kg 
        FROM journeys 
        GROUP BY selected_mode
    """)
    
    # 2. Top routes
    top_routes = query_db("SELECT route_number, route_name, distance_km, status FROM routes LIMIT 5")

    analytics = {
        'users_count': users_count,
        'routes_count': routes_count,
        'stops_count': stops_count,
        'ev_count': ev_count,
        'journeys_count': journeys_stat['c'],
        'total_co2_saved_kg': round(journeys_stat['saved'], 1),
        'total_km_planned': round(journeys_stat['km'], 1),
        'feedback_count': feedback_stat['c'],
        'avg_rating': round(feedback_stat['avg_r'], 1),
        'mode_counts': mode_counts,
        'top_routes': top_routes
    }

    return render_template(
        'admin_dashboard.html',
        analytics=analytics,
        routes=routes,
        stops=stops,
        ev_stations=ev_stations,
        users=all_users,
        feedbacks=feedbacks
    )


# Admin CRUD: Routes
@app.route('/admin/routes/add', methods=['POST'])
@admin_required
def admin_add_route():
    route_number = request.form.get('route_number', '').strip().upper()
    route_name = request.form.get('route_name', '').strip()
    mode_type = request.form.get('mode_type', 'bus')
    origin = request.form.get('origin', '').strip()
    destination = request.form.get('destination', '').strip()
    distance_km = float(request.form.get('distance_km', 10.0))
    estimated_time_min = int(request.form.get('estimated_time_min', 20))
    standard_fare = float(request.form.get('standard_fare', 25.0))
    frequency_min = int(request.form.get('frequency_min', 15))
    status = request.form.get('status', 'On Time')

    if not route_number or not route_name or not origin or not destination:
        flash('Please fill in all route required fields.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        query_db("""
            INSERT INTO routes (route_number, route_name, mode_type, origin, destination, 
                                distance_km, estimated_time_min, standard_fare, frequency_min, status, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, (route_number, route_name, mode_type, origin, destination,
              distance_km, estimated_time_min, standard_fare, frequency_min, status), commit=True)
        flash(f'Transit route {route_number} added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding route: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/routes/edit/<int:route_id>', methods=['POST'])
@admin_required
def admin_edit_route(route_id):
    route_name = request.form.get('route_name', '').strip()
    mode_type = request.form.get('mode_type', 'bus')
    origin = request.form.get('origin', '').strip()
    destination = request.form.get('destination', '').strip()
    distance_km = float(request.form.get('distance_km', 10.0))
    estimated_time_min = int(request.form.get('estimated_time_min', 20))
    standard_fare = float(request.form.get('standard_fare', 25.0))
    frequency_min = int(request.form.get('frequency_min', 15))
    status = request.form.get('status', 'On Time')
    is_active = 1 if request.form.get('is_active') == '1' else 0

    try:
        query_db("""
            UPDATE routes 
            SET route_name=%s, mode_type=%s, origin=%s, destination=%s, distance_km=%s,
                estimated_time_min=%s, standard_fare=%s, frequency_min=%s, status=%s, is_active=%s
            WHERE id = %s
        """, (route_name, mode_type, origin, destination, distance_km,
              estimated_time_min, standard_fare, frequency_min, status, is_active, route_id), commit=True)
        flash('Route updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating route: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/routes/delete/<int:route_id>', methods=['POST'])
@admin_required
def admin_delete_route(route_id):
    try:
        query_db("DELETE FROM routes WHERE id = %s", (route_id,), commit=True)
        flash('Route removed successfully.', 'info')
    except Exception as e:
        flash(f'Error deleting route: {e}', 'danger')
    return redirect(url_for('admin_dashboard'))


# Admin CRUD: Stops
@app.route('/admin/stops/add', methods=['POST'])
@admin_required
def admin_add_stop():
    stop_code = request.form.get('stop_code', '').strip().upper()
    stop_name = request.form.get('stop_name', '').strip()
    latitude = float(request.form.get('latitude', 28.6139))
    longitude = float(request.form.get('longitude', 77.2090))
    city_zone = request.form.get('city_zone', 'Central Zone')
    stop_type = request.form.get('stop_type', 'bus_stop')

    if not stop_code or not stop_name:
        flash('Stop code and stop name are mandatory.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        query_db("""
            INSERT INTO stops (stop_code, stop_name, latitude, longitude, city_zone, stop_type, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """, (stop_code, stop_name, latitude, longitude, city_zone, stop_type), commit=True)
        flash(f'Transit stop {stop_name} added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding stop: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/stops/edit/<int:stop_id>', methods=['POST'])
@admin_required
def admin_edit_stop(stop_id):
    stop_name = request.form.get('stop_name', '').strip()
    latitude = float(request.form.get('latitude', 28.6139))
    longitude = float(request.form.get('longitude', 77.2090))
    city_zone = request.form.get('city_zone', 'Central Zone')
    stop_type = request.form.get('stop_type', 'bus_stop')
    is_active = 1 if request.form.get('is_active') == '1' else 0

    try:
        query_db("""
            UPDATE stops 
            SET stop_name=%s, latitude=%s, longitude=%s, city_zone=%s, stop_type=%s, is_active=%s
            WHERE id = %s
        """, (stop_name, latitude, longitude, city_zone, stop_type, is_active, stop_id), commit=True)
        flash('Stop updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating stop: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/stops/delete/<int:stop_id>', methods=['POST'])
@admin_required
def admin_delete_stop(stop_id):
    try:
        query_db("DELETE FROM stops WHERE id = %s", (stop_id,), commit=True)
        flash('Stop deleted successfully.', 'info')
    except Exception as e:
        flash(f'Error deleting stop: {e}', 'danger')
    return redirect(url_for('admin_dashboard'))


# Admin CRUD: EV Charging Stations
@app.route('/admin/ev-stations/add', methods=['POST'])
@admin_required
def admin_add_ev_station():
    station_name = request.form.get('station_name', '').strip()
    operator = request.form.get('operator', '').strip()
    address = request.form.get('address', '').strip()
    latitude = float(request.form.get('latitude', 28.6139))
    longitude = float(request.form.get('longitude', 77.2090))
    connector_types = request.form.get('connector_types', 'CCS-2, Type-2')
    power_rating = request.form.get('power_rating', '60 kW Fast DC')
    total_ports = int(request.form.get('total_ports', 4))
    available_ports = int(request.form.get('available_ports', 2))
    price_per_kwh = float(request.form.get('price_per_kwh', 14.50))
    status = request.form.get('status', 'Available')

    if not station_name or not operator or not address:
        flash('Station name, operator, and address are mandatory.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        query_db("""
            INSERT INTO ev_charging_stations (station_name, operator, address, latitude, longitude, 
                                              connector_types, power_rating, total_ports, available_ports, 
                                              price_per_kwh, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (station_name, operator, address, latitude, longitude, connector_types,
              power_rating, total_ports, available_ports, price_per_kwh, status), commit=True)
        flash(f'EV Charging Station "{station_name}" added!', 'success')
    except Exception as e:
        flash(f'Error adding station: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/ev-stations/edit/<int:station_id>', methods=['POST'])
@admin_required
def admin_edit_ev_station(station_id):
    station_name = request.form.get('station_name', '').strip()
    operator = request.form.get('operator', '').strip()
    address = request.form.get('address', '').strip()
    latitude = float(request.form.get('latitude', 28.6139))
    longitude = float(request.form.get('longitude', 77.2090))
    connector_types = request.form.get('connector_types', 'CCS-2, Type-2')
    power_rating = request.form.get('power_rating', '60 kW Fast DC')
    total_ports = int(request.form.get('total_ports', 4))
    available_ports = int(request.form.get('available_ports', 2))
    price_per_kwh = float(request.form.get('price_per_kwh', 14.50))
    status = request.form.get('status', 'Available')

    try:
        query_db("""
            UPDATE ev_charging_stations 
            SET station_name=%s, operator=%s, address=%s, latitude=%s, longitude=%s,
                connector_types=%s, power_rating=%s, total_ports=%s, available_ports=%s,
                price_per_kwh=%s, status=%s
            WHERE id = %s
        """, (station_name, operator, address, latitude, longitude, connector_types,
              power_rating, total_ports, available_ports, price_per_kwh, status, station_id), commit=True)
        flash('EV Charging Station updated!', 'success')
    except Exception as e:
        flash(f'Error updating station: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/ev-stations/delete/<int:station_id>', methods=['POST'])
@admin_required
def admin_delete_ev_station(station_id):
    try:
        query_db("DELETE FROM ev_charging_stations WHERE id = %s", (station_id,), commit=True)
        flash('EV Charging Station removed.', 'info')
    except Exception as e:
        flash(f'Error deleting EV station: {e}', 'danger')
    return redirect(url_for('admin_dashboard'))


# Admin CRUD: Feedback status & delete
@app.route('/admin/feedback/status/<int:feedback_id>', methods=['POST'])
@admin_required
def admin_update_feedback_status(feedback_id):
    new_status = request.form.get('status', 'Reviewed')
    try:
        query_db("UPDATE feedback SET status = %s WHERE id = %s", (new_status, feedback_id), commit=True)
        flash('Feedback status updated.', 'success')
    except Exception as e:
        flash(f'Error updating feedback: {e}', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/feedback/delete/<int:feedback_id>', methods=['POST'])
@admin_required
def admin_delete_feedback(feedback_id):
    try:
        query_db("DELETE FROM feedback WHERE id = %s", (feedback_id,), commit=True)
        flash('Feedback item deleted.', 'info')
    except Exception as e:
        flash(f'Error deleting feedback: {e}', 'danger')
    return redirect(url_for('admin_dashboard'))


# ====================================================================
# ERROR HANDLERS
# ====================================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html', custom_body="""
        <div class="container py-5 text-center">
            <div class="py-5">
                <i class="fa-solid fa-triangle-exclamation text-warning display-1 mb-3"></i>
                <h1 class="fw-bold">404 - Page Not Found</h1>
                <p class="lead text-muted">The transit hub or page you are looking for does not exist.</p>
                <a href="/" class="btn btn-primary px-4 py-2 mt-3"><i class="fa-solid fa-house me-2"></i>Return Home</a>
            </div>
        </div>
    """), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('base.html', custom_body="""
        <div class="container py-5 text-center">
            <div class="py-5">
                <i class="fa-solid fa-server text-danger display-1 mb-3"></i>
                <h1 class="fw-bold">500 - Internal Server Error</h1>
                <p class="lead text-muted">An unexpected error occurred while processing the mobility service request.</p>
                <a href="/" class="btn btn-primary px-4 py-2 mt-3"><i class="fa-solid fa-house me-2"></i>Return Home</a>
            </div>
        </div>
    """), 500


# ====================================================================
# APPLICATION ENTRYPOINT
# ====================================================================

if __name__ == '__main__':
    # Automatically ensure database exists and is seeded if needed
    try:
        determine_active_db()
        test_user = query_db("SELECT id FROM users LIMIT 1", one=True)
        if not test_user:
            from db import init_db
            init_db()
    except Exception as e:
        print(f"[STARTUP NOTE] Auto-initializing database: {e}")
        from db import init_db
        init_db()

    print("\n" + "=" * 60)
    print(" Smart Public Transport & Clean Mobility System")
    print(" Running on: http://127.0.0.1:5000")
    print(" Database Engine: " + determine_active_db().upper())
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
