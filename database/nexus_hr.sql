CREATE DATABASE IF NOT EXISTS hr_management;
USE hr_management;

-- 1. Core Employees Table
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    dept VARCHAR(50) NOT NULL,
    role VARCHAR(100) NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    username VARCHAR(150) UNIQUE,
    password_hash VARCHAR(255) DEFAULT 'matrix2026',
    user_role VARCHAR(50) DEFAULT 'EMPLOYEE',
    photo_url VARCHAR(255) DEFAULT 'https://api.dicebear.com/7.x/bottts/svg?seed=nexus'
);

-- 2. Login & System Audit Log Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Safely upgrade existing tables if already created
ALTER TABLE employees ADD COLUMN IF NOT EXISTS username VARCHAR(150) UNIQUE;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255) DEFAULT 'matrix2026';
ALTER TABLE employees ADD COLUMN IF NOT EXISTS user_role VARCHAR(50) DEFAULT 'EMPLOYEE';
ALTER TABLE employees ADD COLUMN IF NOT EXISTS photo_url VARCHAR(255) DEFAULT 'https://api.dicebear.com/7.x/bottts/svg?seed=nexus';

-- 4. Seed Initial Operatives (Skips if already inserted)
INSERT IGNORE INTO employees (code, name, dept, role, salary, status, username, user_role) VALUES 
('NX-001', 'Thomas Anderson', 'CyberSec', 'Lead Penetration Architect', 6200.00, 'ACTIVE', 'admin@nexus.corp', 'HR_ADMIN'),
('NX-002', 'Trinity Moss', 'NetOps', 'Systems Infiltration Lead', 5800.00, 'ACTIVE', 'trinity@nexus.corp', 'EMPLOYEE'),
('NX-003', 'Motoko Kusanagi', 'AI_Core', 'Neural Defense Commander', 6500.00, 'ON_LEAVE', 'motoko@nexus.corp', 'EMPLOYEE'),
('NX-004', 'David Martinez', 'NetOps', 'Edge Runner Technician', 3900.00, 'ACTIVE', 'david@nexus.corp', 'EMPLOYEE');