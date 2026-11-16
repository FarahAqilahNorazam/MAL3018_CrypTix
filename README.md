# 🎟️ CrypTix

## 🔐 Overview

CrypTix is a cryptographically secured web-based e-ticketing platform designed to mitigate concert ticket scalping, ticket forgery, unauthorized ticket sharing, and ownership abuse.

The system introduces security-focused mechanisms to improve ticket authenticity, strengthen ticket ownership verification, and provide a safer ticket purchasing experience for both event organizers and attendees.

CrypTix is developed as part of the MAL3018 Computing Project.

---

## 🎯 Objectives

- Reduce ticket scalping and unauthorized ticket resale.
- Improve ticket ownership verification.
- Protect sensitive user information through cryptographic techniques.
- Strengthen ticket authenticity and validation processes.
- Provide a secure and user-friendly web-based ticketing platform.

---

## ✨ Core Features

### 👤 User Management

- User Registration
- User Authentication
- Role-Based Access Control (RBAC)
- Administrator and Customer Accounts
- Secure Session Management

### 🎫 Ticket Management

- Event Discovery and Browsing
- Ticket Purchasing
- Ticket Ownership Tracking
- Automatic Seat Assignment
- Personal Ticket Dashboard

### 🏟️ Event Management

- Event Creation
- Event Administration
- Ticket Inventory Tracking
- Event Listing and Details

### 🔒 Security Features

- BCrypt Password Hashing
- JSON Web Token (JWT) Authentication
- Secure Session Cookies
- Access Control Enforcement

---

## 🔬 Planned Security Enhancements

### SHA-256 Identity Tokenization

User identity information will be tokenized using SHA-256 hashing to support privacy-preserving ownership verification.

### ECDSA Digital Signatures

Digital signatures will be used to verify ticket authenticity and prevent ticket tampering.

### Dynamic QR Authentication

Time-based QR codes will reduce the risk of screenshot sharing and replay attacks.

### Ticket Validation Scanner

A QR validation module will verify ticket integrity, ownership status, and access permissions during entry.

### Closed-Loop Resale Pool

The platform will provide a controlled ticket resale mechanism to reduce unauthorized ticket transfers and scalping activities.

---

## 🏗️ System Architecture

CrypTix follows a three-tier architecture:

### Presentation Layer

- HTML5
- CSS3
- Bootstrap 5
- JavaScript

### Application Layer

- Python Flask

### Data Layer

- SQLite (Development Environment)
- MySQL (Target Deployment Environment)

---

## 🛠️ Technology Stack

### Frontend

- HTML5
- CSS3
- Bootstrap 5
- JavaScript

### Backend

- Python Flask

### Database

- SQLite
- MySQL

### Security Technologies

- BCrypt
- JSON Web Token (JWT)
- SHA-256
- ECDSA

---

## 📂 Project Structure

```text
CrypTix
├── database/
├── routes/
├── static/
├── templates/
├── tests/
├── utils/
├── app.py
├── config.py
├── requirements.txt
├── seed_admin.py
└── README.md
```

---

## 🚀 Installation

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
py app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 📚 Academic Information

**Project Title**

*CrypTix: A Cryptographically Secured E-Ticketing Web Application for Concert Scalping Mitigation Using SHA-256, ECDSA and Dynamic QR Authentication*

**Module**

MAL3018 Computing Project

**Author**

Farah Aqilah Norazam

---

## ⚠️ Disclaimer

This project is developed for academic and educational purposes as part of a Final Year Computing Project. Commercial deployment would require additional security reviews, infrastructure hardening, compliance assessments, and production-grade testing.
