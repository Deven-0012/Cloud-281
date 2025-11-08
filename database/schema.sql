-- Smart Car Audio Surveillance Platform - PostgreSQL Schema
-- Database: smart_car_surveillance

-- Create database
CREATE DATABASE smart_car_surveillance;

\c smart_car_surveillance;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tenant table
CREATE TABLE tenant (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenant(tenant_id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'iot_team', 'admin')),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Vehicle table
CREATE TABLE vehicle (
    vehicle_id VARCHAR(50) PRIMARY KEY,
    tenant_id UUID REFERENCES tenant(tenant_id),
    owner_id UUID REFERENCES users(user_id),
    make VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    vin VARCHAR(17) UNIQUE,
    license_plate VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- IoT Device table
CREATE TABLE iot_device (
    device_id VARCHAR(50) PRIMARY KEY,
    vehicle_id VARCHAR(50) REFERENCES vehicle(vehicle_id),
    device_type VARCHAR(50) NOT NULL CHECK (device_type IN ('microphone', 'camera', 'sensor')),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    firmware_version VARCHAR(50),
    status VARCHAR(20) DEFAULT 'online' CHECK (status IN ('online', 'offline', 'error')),
    last_heartbeat TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config JSONB
);

-- Ingestion Job table
CREATE TABLE ingestion_job (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id VARCHAR(50) REFERENCES vehicle(vehicle_id),
    device_id VARCHAR(50) REFERENCES iot_device(device_id),
    s3_bucket VARCHAR(255),
    s3_key TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    file_size BIGINT,
    duration FLOAT,
    sample_rate INTEGER,
    channels INTEGER,
    checksum VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Detection table
CREATE TABLE detection (
    detection_id VARCHAR(50) PRIMARY KEY,
    vehicle_id VARCHAR(50) REFERENCES vehicle(vehicle_id),
    sound_label VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    model_version VARCHAR(50),
    s3_key TEXT,
    timestamp TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    processing_time_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alert table
CREATE TABLE alert (
    alert_id VARCHAR(50) PRIMARY KEY,
    vehicle_id VARCHAR(50) REFERENCES vehicle(vehicle_id),
    detection_id VARCHAR(50),
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('emergency', 'safety', 'mechanical', 'security', 'maintenance')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    sound_label VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4),
    message TEXT,
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'under_review', 'acknowledged', 'escalated', 'closed')),
    notified_owner BOOLEAN DEFAULT FALSE,
    notified_service BOOLEAN DEFAULT FALSE,
    acknowledged_by UUID REFERENCES users(user_id),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location POINT,
    metadata JSONB
);

-- Rule table
CREATE TABLE rule (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenant(tenant_id),
    rule_name VARCHAR(255) NOT NULL,
    sound_label VARCHAR(100) NOT NULL,
    threshold DECIMAL(5,4) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    notify_owner BOOLEAN DEFAULT TRUE,
    notify_service BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config JSONB
);

-- Model Deployment table
CREATE TABLE model_deployment (
    deployment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    s3_path TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'deprecated')),
    accuracy DECIMAL(5,4),
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployed_by UUID REFERENCES users(user_id),
    metadata JSONB
);

-- Notification table
CREATE TABLE notification (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id VARCHAR(50) REFERENCES alert(alert_id),
    user_id UUID REFERENCES users(user_id),
    channel VARCHAR(20) CHECK (channel IN ('email', 'sms', 'push', 'webhook')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'read')),
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscription table
CREATE TABLE subscription (
    subscription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenant(tenant_id),
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled')),
    max_vehicles INTEGER,
    max_devices INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    auto_renew BOOLEAN DEFAULT TRUE
);

-- Create indexes for better query performance
CREATE INDEX idx_vehicle_tenant ON vehicle(tenant_id);
CREATE INDEX idx_vehicle_owner ON vehicle(owner_id);
CREATE INDEX idx_iot_device_vehicle ON iot_device(vehicle_id);
CREATE INDEX idx_detection_vehicle ON detection(vehicle_id);
CREATE INDEX idx_detection_status ON detection(status);
CREATE INDEX idx_detection_created ON detection(created_at);
CREATE INDEX idx_alert_vehicle ON alert(vehicle_id);
CREATE INDEX idx_alert_status ON alert(status);
CREATE INDEX idx_alert_created ON alert(created_at);
CREATE INDEX idx_ingestion_vehicle ON ingestion_job(vehicle_id);
CREATE INDEX idx_ingestion_status ON ingestion_job(status);
CREATE INDEX idx_notification_user ON notification(user_id);
CREATE INDEX idx_notification_alert ON notification(alert_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables
CREATE TRIGGER update_tenant_updated_at BEFORE UPDATE ON tenant 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_vehicle_updated_at BEFORE UPDATE ON vehicle 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_rule_updated_at BEFORE UPDATE ON rule 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO tenant (name, email) VALUES 
    ('Tesla Fleet Management', 'admin@tesla-fleet.com'),
    ('Waymo Autonomous', 'admin@waymo.com');

INSERT INTO users (tenant_id, email, password_hash, full_name, role) 
SELECT tenant_id, 'admin@tesla-fleet.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eidpJt2yzUYa', 'Admin User', 'admin'
FROM tenant WHERE email = 'admin@tesla-fleet.com';

INSERT INTO vehicle (vehicle_id, tenant_id, make, model, year, vin, license_plate, status)
SELECT 'CAR-A1234', tenant_id, 'Tesla', 'Model S', 2024, '1HGBH41JXMN109186', 'ABC-1234', 'active'
FROM tenant WHERE email = 'admin@tesla-fleet.com';

-- Sample rules
INSERT INTO rule (tenant_id, rule_name, sound_label, threshold, severity, alert_type, notify_owner, notify_service)
SELECT 
    tenant_id, 
    'Engine Fault Detection', 
    'engine_fault', 
    0.85, 
    'high', 
    'mechanical', 
    TRUE, 
    TRUE
FROM tenant WHERE email = 'admin@tesla-fleet.com';

COMMIT;