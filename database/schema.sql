-- =====================================================================
-- CrypTix Database Schema
-- Phase 1: Authentication & User Table
-- Phase 2: Event Management & Ticket Purchasing
-- Phase 3: SHA-256 MyKad Tokenization & Identity Binding
-- =====================================================================

CREATE DATABASE IF NOT EXISTS cryptix_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE cryptix_db;

-- ---------------------------------------------------------------------
-- 1. USERS TABLE (Phase 1 & Phase 3)
-- Compliant with Malaysia's Personal Data Protection Act (PDPA) 2010.
-- Raw MyKad is NEVER stored. Only SHA-256 hash and masked format.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    mykad_hash VARCHAR(64) NOT NULL COMMENT 'Irreversible SHA-256 digest of MyKad',
    masked_ic VARCHAR(20) NOT NULL COMMENT 'Privacy-preserving masked string e.g. ******--1234',
    pdpa_consent TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Mandatory PDPA 2010 consent flag',
    role ENUM('Admin', 'Customer') NOT NULL DEFAULT 'Customer',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email),
    INDEX idx_user_mykad_hash (mykad_hash)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. EVENTS TABLE (Phase 2)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_title VARCHAR(150) NOT NULL,
    description TEXT NULL,
    event_date DATETIME NOT NULL,
    venue VARCHAR(150) NOT NULL,
    total_capacity INT NOT NULL,
    available_capacity INT NOT NULL,
    ticket_price DECIMAL(10, 2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_date (event_date)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. TICKETS TABLE (Phase 2 & Phase 3)
-- Associated with purchaser user_id and bound to mykad_hash
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    user_id INT NOT NULL,
    mykad_hash VARCHAR(64) NOT NULL COMMENT 'SHA-256 identity token binding',
    seat_number VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'SOLD',
    purchased_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tickets_event
        FOREIGN KEY (event_id) REFERENCES events (event_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_tickets_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE,
    INDEX idx_tickets_user_event (user_id, event_id),
    INDEX idx_tickets_mykad_hash (mykad_hash),
    INDEX idx_tickets_status (status)
) ENGINE=InnoDB;
