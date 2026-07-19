-- Database schema for DeForestNet

-- Table: users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Admin', 'Researcher', 'Authority')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: regions_of_interest
CREATE TABLE IF NOT EXISTS regions_of_interest (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    geometry TEXT NOT NULL, -- GeoJSON string representing the boundary polygon
    contact_email TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: alerts
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id INTEGER,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    area_ha REAL NOT NULL,
    ndvi_before REAL,
    ndvi_after REAL,
    ndvi_diff REAL,
    status TEXT NOT NULL CHECK (status IN ('Pending', 'Verified', 'False Positive', 'Reported')) DEFAULT 'Pending',
    risk_level TEXT CHECK (risk_level IN ('Low', 'Medium', 'High', 'Critical')) DEFAULT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imagery_before_path TEXT,
    imagery_after_path TEXT,
    details TEXT, -- JSON string for additional context
    FOREIGN KEY (region_id) REFERENCES regions_of_interest(id)
);

-- Table: reports
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    narrative_summary TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    recipient_email TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK (status IN ('Pending', 'Sent', 'Failed')) DEFAULT 'Pending',
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);
