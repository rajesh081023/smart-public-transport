-- ====================================================================
-- Smart Public Transport and Clean Mobility System
-- Database Schema for MySQL
-- Database Name: smart_mobility_db
-- ====================================================================

CREATE DATABASE IF NOT EXISTS smart_mobility_db;
USE smart_mobility_db;

-- 1. Users Table
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS journeys;
DROP TABLE IF EXISTS schedules;
DROP TABLE IF EXISTS route_stops;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS stops;
DROP TABLE IF EXISTS ev_charging_stations;
DROP TABLE IF EXISTS transport_modes;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'user', -- 'user' or 'admin'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Transport Modes Reference Table
CREATE TABLE transport_modes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mode_code VARCHAR(30) NOT NULL UNIQUE,
    mode_name VARCHAR(60) NOT NULL,
    category VARCHAR(30) NOT NULL, -- 'active', 'public_transit', 'electric', 'private'
    base_fare DECIMAL(8,2) DEFAULT 0.00,
    per_km_rate DECIMAL(8,2) DEFAULT 0.00,
    co2_per_km DECIMAL(8,2) DEFAULT 0.00, -- in grams of CO2 per passenger-km
    average_speed_kmh DECIMAL(5,1) DEFAULT 25.0,
    icon VARCHAR(50) DEFAULT 'fa-bus',
    description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Transit Stops & Stations Table
CREATE TABLE stops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stop_code VARCHAR(20) NOT NULL UNIQUE,
    stop_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    city_zone VARCHAR(50) DEFAULT 'Central Zone',
    stop_type VARCHAR(30) DEFAULT 'bus_stop', -- 'bus_stop', 'metro_station', 'interchange', 'bike_station'
    is_active TINYINT(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Transport Routes Table
CREATE TABLE routes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_number VARCHAR(30) NOT NULL UNIQUE,
    route_name VARCHAR(120) NOT NULL,
    mode_type VARCHAR(30) NOT NULL, -- 'bus', 'metro', 'electric_bus'
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    distance_km DECIMAL(6,2) NOT NULL,
    estimated_time_min INT NOT NULL,
    standard_fare DECIMAL(8,2) NOT NULL,
    frequency_min INT DEFAULT 15,
    status VARCHAR(40) DEFAULT 'On Time', -- 'On Time', 'Minor Delay', 'Normal Service', 'High Frequency'
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Route Stops Mapping Table
CREATE TABLE route_stops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL,
    stop_id INT NOT NULL,
    stop_sequence INT NOT NULL,
    time_from_origin_min INT DEFAULT 0,
    fare_from_origin DECIMAL(8,2) DEFAULT 0.00,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
    FOREIGN KEY (stop_id) REFERENCES stops(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Route Schedules Table
CREATE TABLE schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    days_of_week VARCHAR(50) DEFAULT 'Daily',
    vehicle_number VARCHAR(30),
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. EV Charging Stations Table
CREATE TABLE ev_charging_stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_name VARCHAR(120) NOT NULL,
    operator VARCHAR(80) NOT NULL,
    address VARCHAR(255) NOT NULL,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    connector_types VARCHAR(120) NOT NULL, -- e.g. 'CCS-2 (Fast DC), Type-2 AC, GB/T'
    power_rating VARCHAR(50) DEFAULT '60 kW Fast DC',
    total_ports INT DEFAULT 4,
    available_ports INT DEFAULT 2,
    price_per_kwh DECIMAL(8,2) DEFAULT 14.50,
    status VARCHAR(30) DEFAULT 'Available', -- 'Available', 'Busy', 'Maintenance'
    open_hours VARCHAR(50) DEFAULT '24/7',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. User Planned Journeys History Table
CREATE TABLE journeys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    origin VARCHAR(120) NOT NULL,
    destination VARCHAR(120) NOT NULL,
    distance_km DECIMAL(6,2) NOT NULL,
    selected_mode VARCHAR(40) NOT NULL,
    travel_time_min INT NOT NULL,
    travel_cost DECIMAL(8,2) NOT NULL,
    co2_emitted_kg DECIMAL(8,3) NOT NULL,
    co2_saved_kg DECIMAL(8,3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Feedback and Ratings Table
CREATE TABLE feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    category VARCHAR(50) DEFAULT 'General Suggestion',
    rating INT NOT NULL, -- 1 to 5 stars
    comment TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'Reviewed', -- 'Pending Review', 'Reviewed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ====================================================================
-- SEED DATA INSERTION
-- ====================================================================

-- Default Administrator (Password: Admin@123) and Test User (Password: User@123)
INSERT INTO users (full_name, email, password_hash, phone, role) VALUES
('System Administrator', 'admin@smartmobility.com', 'scrypt:32768:8:1$47om13hvFiFLxBc0$e341b2aef30f3a4c96d74423853044a7a7d292b332e909af809a3ed9ba3c68e75874c75b03f5552c73e6250a53fc5fab95fe5df630ab511629abf7c521e90fb0', '+91 98765 43210', 'admin'),
('Rahul Sharma', 'rahul.sharma@example.com', 'scrypt:32768:8:1$LqdKueZANAtsS1Fn$d635ed594a0e63b3cd55b13fcf3cb410d6b316fd077251f895d3fb342db335ed9ea249226d07b57dad918a44ecde83fff8d3f0e2dc8d79fec2d0e0aef608ece0', '+91 98112 34567', 'user'),
('Priya Patel', 'priya.patel@example.com', 'scrypt:32768:8:1$LqdKueZANAtsS1Fn$d635ed594a0e63b3cd55b13fcf3cb410d6b316fd077251f895d3fb342db335ed9ea249226d07b57dad918a44ecde83fff8d3f0e2dc8d79fec2d0e0aef608ece0', '+91 98223 45678', 'user');

-- Transport Modes
INSERT INTO transport_modes (mode_code, mode_name, category, base_fare, per_km_rate, co2_per_km, average_speed_kmh, icon, description) VALUES
('walking', 'Pedestrian Walking', 'active', 0.00, 0.00, 0.00, 4.5, 'fa-person-walking', 'Zero carbon, health-boosting active mobility ideal for trips under 2 km.'),
('bicycle', 'Public Bike Share / E-Bike', 'active', 5.00, 1.00, 0.00, 15.0, 'fa-bicycle', 'Zero emission, agile urban transport with dedicated green cycling corridors.'),
('metro', 'Smart Metro Rail', 'public_transit', 15.00, 2.80, 16.00, 42.0, 'fa-train-subway', 'Rapid electrified mass transit providing highest speed and ultra-low per-passenger emissions.'),
('bus', 'Clean Transit Bus (CNG / Electric)', 'public_transit', 10.00, 2.00, 35.00, 24.0, 'fa-bus', 'Affordable city-wide bus network with high accessibility and dedicated bus lanes.'),
('ev', 'Shared Electric Taxi / EV Cab', 'electric', 35.00, 12.00, 47.00, 32.0, 'fa-bolt', 'Comfortable door-to-door electric fleet with zero tailpipe pollution.'),
('car', 'Private Petrol Car (Baseline)', 'private', 40.00, 15.00, 171.00, 30.0, 'fa-car', 'High carbon footprint benchmark showing significant traffic and emission penalty.');

-- Key City Transit Stops & Hubs
INSERT INTO stops (stop_code, stop_name, latitude, longitude, city_zone, stop_type) VALUES
('ST-001', 'Central Hub (Rajiv Interchange)', 28.6328000, 77.2197000, 'Central Business District', 'interchange'),
('ST-002', 'Green Park Eco Station', 28.5589000, 77.2062000, 'South Green Zone', 'metro_station'),
('ST-003', 'Hauz Khas Heritage Terminal', 28.5431000, 77.2065000, 'South Zone', 'interchange'),
('ST-004', 'Cyber Tech City Corridor', 28.4985000, 77.0890000, 'IT & Innovation Hub', 'metro_station'),
('ST-005', 'Nehru Commercial Center', 28.5494000, 77.2536000, 'South-East Zone', 'metro_station'),
('ST-006', 'City University North Campus', 28.6890000, 77.2114000, 'University Enclave', 'bus_stop'),
('ST-007', 'International Airport T3 Express', 28.5562000, 77.0870000, 'Airport Corridor', 'interchange'),
('ST-008', 'Riverside Promenade & Docks', 28.6650000, 77.2340000, 'Riverfront Zone', 'bike_station'),
('ST-009', 'East Inter-State Bus Terminal', 28.6502000, 77.3150000, 'East Transit Gateway', 'interchange'),
('ST-010', 'AIIMS Medical & Research Center', 28.5672000, 77.2100000, 'Healthcare District', 'bus_stop'),
('ST-011', 'South Extension Market', 28.5732000, 77.2224000, 'Commercial Hub', 'bus_stop'),
('ST-012', 'Lajpat Nagar Central Market', 28.5684000, 77.2435000, 'Central Shopping Ring', 'bus_stop');

-- Public Transit Routes
INSERT INTO routes (route_number, route_name, mode_type, origin, destination, distance_km, estimated_time_min, standard_fare, frequency_min, status) VALUES
('METRO-BLUE', 'Express Metro: Central Hub to Cyber Tech City', 'metro', 'Central Hub (Rajiv Interchange)', 'Cyber Tech City Corridor', 24.50, 35, 55.00, 6, 'On Time'),
('METRO-GREEN', 'Green Line: University North to Green Park Eco', 'metro', 'City University North Campus', 'Green Park Eco Station', 16.20, 26, 40.00, 8, 'Normal Service'),
('METRO-AERO', 'Airport Express: Central Hub to Airport T3', 'metro', 'Central Hub (Rajiv Interchange)', 'International Airport T3 Express', 19.80, 22, 60.00, 10, 'On Time'),
('BUS-522-EV', 'Electric Bus: Central Hub to Nehru Commercial', 'electric_bus', 'Central Hub (Rajiv Interchange)', 'Nehru Commercial Center', 12.30, 32, 25.00, 10, 'High Frequency'),
('BUS-419-CNG', 'Eco CNG Route: East Terminal to Hauz Khas', 'bus', 'East Inter-State Bus Terminal', 'Hauz Khas Heritage Terminal', 21.00, 50, 30.00, 12, 'Minor Delay'),
('BUS-102-AC', 'Smart City Feeder: Green Park to AIIMS Medical', 'bus', 'Green Park Eco Station', 'AIIMS Medical & Research Center', 4.50, 14, 15.00, 7, 'On Time'),
('BUS-305-EV', 'Clean River Line: Riverside to Central Hub', 'electric_bus', 'Riverside Promenade & Docks', 'Central Hub (Rajiv Interchange)', 7.80, 20, 20.00, 15, 'Normal Service');

-- Route Stops Sequences
-- METRO-BLUE (Route 1)
INSERT INTO route_stops (route_id, stop_id, stop_sequence, time_from_origin_min, fare_from_origin) VALUES
(1, 1, 1, 0, 0.00),
(1, 2, 2, 12, 25.00),
(1, 3, 3, 18, 35.00),
(1, 4, 4, 35, 55.00);

-- METRO-GREEN (Route 2)
INSERT INTO route_stops (route_id, stop_id, stop_sequence, time_from_origin_min, fare_from_origin) VALUES
(2, 6, 1, 0, 0.00),
(2, 1, 2, 14, 25.00),
(2, 10, 3, 20, 35.00),
(2, 2, 4, 26, 40.00);

-- METRO-AERO (Route 3)
INSERT INTO route_stops (route_id, stop_id, stop_sequence, time_from_origin_min, fare_from_origin) VALUES
(3, 1, 1, 0, 0.00),
(3, 7, 2, 22, 60.00);

-- BUS-522-EV (Route 4)
INSERT INTO route_stops (route_id, stop_id, stop_sequence, time_from_origin_min, fare_from_origin) VALUES
(4, 1, 1, 0, 0.00),
(4, 11, 2, 12, 15.00),
(4, 12, 3, 20, 20.00),
(4, 5, 4, 32, 25.00);

-- BUS-419-CNG (Route 5)
INSERT INTO route_stops (route_id, stop_id, stop_sequence, time_from_origin_min, fare_from_origin) VALUES
(5, 9, 1, 0, 0.00),
(5, 5, 2, 24, 20.00),
(5, 12, 3, 35, 25.00),
(5, 3, 4, 50, 30.00);

-- BUS-102-AC (Route 6)
INSERT INTO route_stops (route_id, stop_id, stop_sequence, time_from_origin_min, fare_from_origin) VALUES
(6, 2, 1, 0, 0.00),
(6, 10, 2, 8, 10.00),
(6, 11, 3, 14, 15.00);

-- Route Schedules
INSERT INTO schedules (route_id, departure_time, arrival_time, days_of_week, vehicle_number) VALUES
(1, '06:00:00', '06:35:00', 'Daily', 'MET-B-101'),
(1, '06:15:00', '06:50:00', 'Daily', 'MET-B-102'),
(1, '06:30:00', '07:05:00', 'Daily', 'MET-B-103'),
(1, '07:00:00', '07:35:00', 'Daily', 'MET-B-104'),
(2, '06:10:00', '06:36:00', 'Daily', 'MET-G-201'),
(2, '06:30:00', '06:56:00', 'Daily', 'MET-G-202'),
(3, '05:30:00', '05:52:00', 'Daily', 'AERO-X-01'),
(3, '06:00:00', '06:22:00', 'Daily', 'AERO-X-02'),
(4, '07:00:00', '07:32:00', 'Daily', 'EV-BUS-501'),
(4, '07:20:00', '07:52:00', 'Daily', 'EV-BUS-502'),
(5, '06:45:00', '07:35:00', 'Daily', 'CNG-BUS-301');

-- EV Charging Stations
INSERT INTO ev_charging_stations (station_name, operator, address, latitude, longitude, connector_types, power_rating, total_ports, available_ports, price_per_kwh, status, open_hours) VALUES
('Tata EZ Charge - Central Connaught Hub', 'Tata Power', 'Regal Building Underground Parking, Connaught Circle', 28.6315000, 77.2185000, 'CCS-2 (Fast DC), Type-2 AC', '60 kW Fast DC', 6, 4, 14.50, 'Available', '24/7'),
('Jio-bp Pulse Green Station', 'Jio-bp pulse', 'Ring Road, Near Green Park Metro Exit 2', 28.5601000, 77.2080000, 'CCS-2, GB/T, Type-2', '120 kW Ultra-Fast', 8, 5, 15.00, 'Available', '24/7'),
('Ather Grid Cyber City Node', 'Ather Energy', 'Tower B Forecourt, Cyber City DLF', 28.4972000, 77.0881000, 'Ather Fast Grid, Type-2', '25 kW Fast DC', 4, 1, 12.00, 'Busy', '06:00 - 23:00'),
('Fortum Charge & Drive - Nehru Plaza', 'Fortum India', 'International Trade Tower, Nehru Place', 28.5488000, 77.2520000, 'CCS-2 (Fast DC), CHAdeMO', '50 kW Fast DC', 4, 3, 14.00, 'Available', '24/7'),
('Shell Recharge Hub - Airport Expressway', 'Shell EV Mobility', 'NH-48 Service Road, Terminal 3 Approach', 28.5520000, 77.0910000, 'CCS-2 Dual Gun 150 kW', '150 kW Ultra-Fast', 8, 6, 16.50, 'Available', '24/7'),
('Statiq EV Station - South Ext.', 'Statiq Power', 'Main Ring Road, South Extension Part 2', 28.5710000, 77.2240000, 'CCS-2, Type-2 AC', '30 kW DC', 4, 0, 13.50, 'Busy', '24/7'),
('EcoCharge Solar Station - University', 'Delhi Smart City Mission', 'North Campus Chhatra Marg Gate 1', 28.6875000, 77.2105000, 'Type-2 AC, 15A Smart Socket', '22 kW AC Solar', 6, 5, 11.00, 'Available', '07:00 - 21:00'),
('ElectreeFi Fast Hub - East Gateway', 'ElectreeFi', 'ISBT Anand Vihar Parking Lot A', 28.6495000, 77.3130000, 'CCS-2, GB/T Fast', '60 kW DC', 6, 2, 14.00, 'Available', '24/7');

-- Sample Completed Journeys
INSERT INTO journeys (user_id, origin, destination, distance_km, selected_mode, travel_time_min, travel_cost, co2_emitted_kg, co2_saved_kg) VALUES
(2, 'Central Hub (Rajiv Interchange)', 'Cyber Tech City Corridor', 24.50, 'metro', 35, 55.00, 0.392, 3.797),
(2, 'Green Park Eco Station', 'AIIMS Medical & Research Center', 4.50, 'bicycle', 18, 9.50, 0.000, 0.769),
(3, 'Central Hub (Rajiv Interchange)', 'Nehru Commercial Center', 12.30, 'electric_bus', 32, 25.00, 0.270, 1.833),
(3, 'City University North Campus', 'Green Park Eco Station', 16.20, 'metro', 26, 40.00, 0.259, 2.511);

-- Sample Community Feedback
INSERT INTO feedback (user_id, name, email, category, rating, comment, status) VALUES
(2, 'Rahul Sharma', 'rahul.sharma@example.com', 'Route Accuracy', 5, 'The Metro Blue line travel time and fare calculations were spot on! Saved me 40 minutes during peak hours and significantly cut down my carbon footprint.', 'Reviewed'),
(3, 'Priya Patel', 'priya.patel@example.com', 'Clean Mobility', 5, 'Loved the EV charging station finder. Found an open fast charger at Connaught Place within seconds. Great initiative for eco-friendly transit!', 'Reviewed'),
(NULL, 'Vikram Mehta', 'vikram.m@gmail.com', 'App Feature', 4, 'Very intuitive user interface. The carbon savings comparison chart really puts daily emissions into perspective. Would love to see live bus GPS tracking in future versions!', 'Reviewed'),
(NULL, 'Ananya Sen', 'ananya.sen@college.edu', 'General Suggestion', 5, 'Perfect project for smart urban planning! Walking and cycling prompts for trips under 2 km encourage healthier daily habits.', 'Reviewed');
