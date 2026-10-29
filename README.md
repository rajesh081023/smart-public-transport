# Smart Public Transport and Clean Mobility System 🚌🌱⚡

A complete, full-stack, smart-city web application designed for B.Tech CSE / IT capstone projects. The system provides intelligent multi-modal journey planning, real-time public transit schedules, electric vehicle (EV) charging station discovery, and comprehensive carbon emission calculations.

---

## 📌 Project Overview

Rapid urban expansion has led to severe traffic congestion and air pollution. The **Smart Public Transport and Clean Mobility System** empowers commuters to make sustainable travel choices by comparing time, cost, and greenhouse gas emissions across multiple transit modes:

- 🚇 **City Metro Rail** (Rapid transit, electrified)
- 🚌 **Clean Transit Bus** (CNG & Electric fleets)
- ⚡ **Electric Vehicles (EV)** (Shared electric cabs & charging stations)
- 🚲 **Public Bicycle Sharing / E-Bikes** (Zero-carbon active travel)
- 🚶 **Walking** (Cardiovascular health & zero emissions)
- 🚗 **Private Petrol Car** (Baseline for carbon comparison)

---

## 🚀 Key Features

### 1. User Authentication & Role-Based Access
- Commuter registration, login, and secure session management.
- Cryptographic password hashing using `scrypt` (via `Werkzeug`).
- Role-based authorization (`user` vs `admin`).
- Personalized Commuter Dashboard tracking saved trips, personal carbon offset (kg CO₂), and eco-badges.

### 2. Smart Journey Planner
- Select origin and destination from mapped smart-city transit hubs.
- Automatic computation of road network distance using the **Haversine formula**.
- Side-by-side comparison of fare (₹), estimated duration (mins), CO₂ emitted (kg), and calories burned.
- Smart recommendation engine highlighting the **Most Eco-Friendly**, **Most Affordable**, and **Fastest** route.
- Interactive **Leaflet.js** map rendering custom transit route polylines and nearby EV charging points.
- One-click "Save Journey" to user profile.

### 3. Public Transport Corridors & Timetables
- Search and filter bus and metro lines by mode, route number, or terminal stop.
- Dynamic upcoming departure times (e.g., *Next departure in 8 mins*).
- Interactive Modal showing ordered stop sequences and timetable schedules.

### 4. Clean Mobility & EV Infrastructure Hub
- Guidance for active transport (walking and cycling benefits for short journeys < 2.5 km).
- Interactive Leaflet map displaying EV Charging Stations with live port availability (Available vs Busy).
- Filter by charging operator (*Tata Power*, *Jio-bp pulse*, *Ather Grid*, *Fortum*, *Shell*) and connector type (*CCS-2*, *Type-2*, *GB/T*).

### 5. Carbon Footprint & Savings Calculator
- Interactive commute distance slider (1 km to 60 km).
- Multi-timeframe projections: Single Trip, Monthly (22 workdays), and Annual (250 workdays).
- Interactive **Chart.js** bar and doughnut charts comparing emissions and savings.
- Scientific calculation standards citing **IPCC**, **CPCB**, and **DEFRA** emission factors.
- Real-world equivalents: Tree absorption offset (~21.7 kg CO₂/tree/yr) and fuel cost savings in ₹.

### 6. Feedback & Community Testimonials
- Star rating system (1 to 5 stars) and category tagging.
- Transparent review moderation by administrators.

### 7. Administrator Control Center (CRUD)
- System metrics: total users, active routes, stops, EV stations, and total kg CO₂ prevented.
- Complete CRUD operations:
  - Add / Edit / Delete Transit Routes
  - Add / Edit / Delete Stops & Stations
  - Add / Edit / Delete EV Charging Points
  - Moderate Commuter Feedback
  - View Registered Users
- Interactive analytics charts powered by Chart.js.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3.3, Font Awesome 6.5.1 |
| **Backend** | Python 3.10+, Flask 3.x |
| **Database** | MySQL (`smart_mobility_db`) with automatic local SQLite fallback |
| **Mapping** | Leaflet.js with OpenStreetMap |
| **Data Visuals** | Chart.js 4.4.2 |
| **Security** | Werkzeug Security (Scrypt Hashing), Parameterized SQL Queries |

---

## 📂 Project Structure

```
smart-public-transport/
│
├── app.py                  # Main Flask application with routes and API endpoints
├── config.py               # Environment configuration and emission factor constants
├── db.py                   # Dual-engine database adapter (MySQL + SQLite fallback)
├── init_db.py              # CLI database initialization and seed data verification
├── requirements.txt        # Python backend dependencies
├── .env.example            # Environment variables configuration template
├── .env                    # Active local environment settings
├── schema.sql              # MySQL database schema and sample records
├── README.md               # Complete setup, documentation, and viva notes
│
├── static/
│   ├── css/
│   │   └── style.css       # Smart-city eco design system (green, blue, navy)
│   └── js/
│       ├── main.js         # UI interactions, counter animations, and toast alerts
│       ├── map.js          # Leaflet.js custom markers, polylines, and popups
│       └── charts.js       # Chart.js renderers for emissions and admin analytics
│
└── templates/
    ├── base.html           # Master layout with responsive navbar, footer, and CDN links
    ├── index.html          # Landing page with hero banner and quick trip widget
    ├── login.html          # User and administrator sign-in
    ├── register.html       # User registration
    ├── dashboard.html      # Commuter dashboard with saved journeys and eco-badges
    ├── journey_planner.html# Multi-modal planner with map and mode comparison cards
    ├── transport_routes.html# Public transit route explorer and timetable modals
    ├── clean_mobility.html # Clean mobility advice and interactive EV locator map
    ├── carbon_calculator.html# Carbon footprint calculator with Chart.js visualizer
    ├── feedback.html       # User feedback form and community ratings feed
    └── admin_dashboard.html# Admin CRUD control center and system analytics
```

---

## ⚙️ Installation & Setup Instructions

### Prerequisites
- **Python**: Version 3.10 or higher.
- **MySQL**: (Optional / Recommended) MySQL Server, XAMPP, or MariaDB.
  *(Note: If MySQL is not running on your machine, the system automatically runs on local SQLite without any manual configuration!)*

---

### Step 1: Open the Project Directory
Open your terminal (PowerShell or Command Prompt) and navigate to the project directory:
```powershell
cd c:\Users\USER\Desktop\smart-public-transport
```

---

### Step 2: (Optional) Create a Python Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

---

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables
A `.env` file has already been prepared. If you want to connect to a local MySQL server:
1. Open `.env` in any text editor.
2. Ensure your MySQL credentials are set:
```env
DB_TYPE=auto
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=smart_mobility_db
```
> **Tip on `DB_TYPE=auto`:** If MySQL is installed and running, the app automatically connects to MySQL. If MySQL is offline, it seamlessly runs on SQLite (`smart_mobility.db`) so you can run and present immediately!

---

### Step 5: Initialize the Database & Seed Records
Run the initialization script:
```powershell
python init_db.py
```
This creates all 9 relational tables and populates realistic transit corridors, stops, EV stations, users, and feedback records.

#### Manual MySQL Import (Alternative):
If using MySQL Workbench or XAMPP phpMyAdmin:
```bash
mysql -u root -p < schema.sql
```

---

### Step 6: Start the Flask Application
```powershell
python app.py
```
You will see:
```text
============================================================
 Smart Public Transport & Clean Mobility System
 Running on: http://127.0.0.1:5000
 Database Engine: SQLITE (or MYSQL)
============================================================
```

---

### Step 7: Access the Application
Open your web browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Default Login Credentials

| Role | Email | Password |
|---|---|---|
| **Administrator** | `admin@smartmobility.com` | `Admin@123` |
| **Commuter (User)** | `rahul.sharma@example.com` | `User@123` |
| **Commuter (User)** | `priya.patel@example.com` | `User@123` |

*(New accounts can also be created instantly via the Register page.)*

---

## 🎓 B.Tech Project Viva & Defense Guide

### 1. How is distance calculated between transit stops?
The system implements the **Haversine Formula**:
$$d = 2R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
where $\phi$ is latitude and $\lambda$ is longitude in radians, with $R = 6371\text{ km}$. We apply an urban road curvature factor ($1.28\times$) to convert geodesic distances into realistic road transit distances.

### 2. How are carbon emissions calculated?
Emissions are calculated per passenger-kilometer using standards from the **Central Pollution Control Board (CPCB)** and **IPCC**:
$$\text{Emission (kg)} = \frac{\text{Distance (km)} \times \text{Emission Factor (g CO}_2\text{/pax-km)}}{1000}$$
- **Private Petrol Car**: $171.0\text{ g/km}$
- **City Metro**: $16.0\text{ g/km}$
- **Electric Bus**: $22.0\text{ g/km}$
- **CNG Bus**: $58.0\text{ g/km}$
- **Walking / Biking**: $0.0\text{ g/km}$

### 3. How does the system prevent SQL Injection?
All queries in `db.py` use **parameterized queries** with placeholder binding (`%s` / `?`). User input is never concatenated directly into SQL strings.

### 4. How are passwords secured?
Passwords are hashed using `werkzeug.security.generate_password_hash` utilizing the **Scrypt** key derivation function with unique cryptographic salts. Raw passwords are never stored in the database.

---

## 🛡️ License & Academic Integrity
Developed as a capstone software engineering project for B.Tech CSE / IT. Free to use and demonstrate for academic purposes.
