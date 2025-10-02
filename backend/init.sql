-- Initial database setup for GGnet Diskless Server
-- This script creates the database and initial admin user

-- Create database (if using PostgreSQL)
-- Note: This will only run if the database doesn't exist

-- Create extensions (PostgreSQL specific)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create initial admin user (will be handled by application migration)
-- This is just a placeholder for manual setup if needed

-- Insert default admin user
-- Password: admin123 (hashed with bcrypt)
-- Note: Change this password immediately after first login!

INSERT INTO users (
    username, 
    email, 
    full_name, 
    hashed_password, 
    role, 
    status, 
    is_active,
    created_at,
    updated_at
) VALUES (
    'admin',
    'admin@ggnet.local',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO5S7ZOdS', -- admin123
    'admin',
    'active',
    true,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

CREATE INDEX IF NOT EXISTS idx_images_name ON images(name);
CREATE INDEX IF NOT EXISTS idx_images_status ON images(status);
CREATE INDEX IF NOT EXISTS idx_images_format ON images(format);
CREATE INDEX IF NOT EXISTS idx_images_created_by ON images(created_by);

CREATE INDEX IF NOT EXISTS idx_machines_mac_address ON machines(mac_address);
CREATE INDEX IF NOT EXISTS idx_machines_ip_address ON machines(ip_address);
CREATE INDEX IF NOT EXISTS idx_machines_hostname ON machines(hostname);
CREATE INDEX IF NOT EXISTS idx_machines_status ON machines(status);

CREATE INDEX IF NOT EXISTS idx_targets_iqn ON targets(iqn);
CREATE INDEX IF NOT EXISTS idx_targets_machine_id ON targets(machine_id);
CREATE INDEX IF NOT EXISTS idx_targets_status ON targets(status);

CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_machine_id ON sessions(machine_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_severity ON audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);

