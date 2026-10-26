# CrypTix 🎟️🔐
**A Cryptographically Secured E-Ticketing & Access Control Prototype**

CrypTix is an advanced, localized e-ticketing prototype designed to eradicate ticket scalping and screenshot forgery in the Malaysian event ecosystem. Inspired by global standards like Ticketmaster SafeTix, CrypTix integrates time-sensitive Dynamic QR codes with local Malaysian Identity (MyKad) hashing to provide a zero-trust access control mechanism.

This project is developed as a Final Year Project (FYP) for a Degree in Cybersecurity.

---

## 🚀 Core Security Features

* **Dynamic QR Codes (60-Second TTL):** 
  Tickets are generated with a live timecode. The QR code expires and refreshes every 60 seconds, completely neutralizing screenshot sharing and duplication attacks.
* **Cryptographic Identity Binding (SHA-256):** 
  To comply with Malaysia's PDPA 2010, raw MyKad (IC) numbers are never stored in the QR code. They are securely hashed using SHA-256, permanently linking the digital ticket to a real human identity without exposing sensitive data.
* **ECDSA Digital Signatures:** 
  The ticket payload (Hashed MyKad + Timestamp + Ticket ID) is digitally signed using the Organizer's Elliptic Curve Digital Signature Algorithm (ECDSA) Private Key. Any tampering instantly breaks the signature.
* **Closed-Loop Resale Mechanism:** 
  Direct peer-to-peer (P2P) transfers are blocked at the architecture level. Buyers who cannot attend must surrender their ticket to the Official CrypTix Resale Pool, which revokes the old identity binding, issues a partial refund, and generates a new secure ticket for the secondary buyer.

---

## 🏗️ System Architecture (3-Tier)

1. **Tier 1: Client Layer**
   * Customer Portal & Admin Dashboard (HTML5 / Frontend Framework)
   * Unmanned Gate Kiosk Scanner (`HTML5-QRCode`)
2. **Tier 2: Security & Application Logic Layer**
   * API Gateway & Router (Python / Flask)
   * Cryptographic Engine (SHA-256 Hashing & ECDSA Signing Modules)
   * Dynamic QR Generator
3. **Tier 3: Data & Key Storage Layer**
   * Relational Database (MySQL) for User & Ticket Data
   * Secure Key Vault for ECDSA Private Keys

---

## 🛠️ Technology Stack
* **Backend:** Python, Flask
* **Frontend:** HTML5, CSS, JS (React / Bootstrap)
* **Database:** MySQL
* **Cryptography:** `hashlib` (SHA-256), `ecdsa` (Digital Signatures)
* **Scanning Module:** `html5-qrcode` (Browser-based scanner)

