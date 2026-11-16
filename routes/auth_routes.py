from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, g
from config import Config
from database.db import get_user_by_email, get_user_by_mykad_hash, create_customer_user
from utils.auth_utils import hash_password, verify_password, generate_jwt_token, get_current_user_from_request
from utils.crypto_utils import validate_mykad, hash_mykad, mask_mykad

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User Registration (Phase 3):
    - Strictly forces new accounts to 'Customer' role (no role selector).
    - Requires Malaysian MyKad input and validates format (YYMMDD-PB-###G).
    - Requires mandatory PDPA 2010 consent checkbox.
    - Computes irreversible SHA-256 token digest and privacy-preserving masked IC (******-**-1234).
    - Discards raw MyKad: RAW IC IS NEVER STORED IN DATABASE OR LOGS.
    - Hashes password via BCrypt.
    """
    # If already logged in, redirect to dashboard
    if get_current_user_from_request():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        mykad = request.form.get('mykad', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        pdpa_consent = request.form.get('pdpa_consent')

        # 1. Mandatory PDPA 2010 Consent Validation
        if not pdpa_consent:
            flash('Registration failed: You must accept the mandatory PDPA 2010 Consent Checkbox to create an account.', 'danger')
            return render_template('register.html', name=name, email=email)

        # 2. Field Completeness Validation
        if not name or not email or not password or not mykad:
            flash('Please fill in all required fields including your Malaysian MyKad number.', 'danger')
            return render_template('register.html', name=name, email=email)

        # 3. Malaysian MyKad Format Validation
        is_valid_ic, normalized_ic, ic_err = validate_mykad(mykad)
        if not is_valid_ic:
            flash(f'Identity Validation Error: {ic_err}', 'danger')
            return render_template('register.html', name=name, email=email)

        # 4. Password Confirmation & Minimum Complexity
        if password != confirm_password:
            flash('Passwords do not match. Please re-enter your password.', 'danger')
            return render_template('register.html', name=name, email=email)

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('register.html', name=name, email=email)

        # 5. Email Uniqueness Check
        existing_user = get_user_by_email(email)
        if existing_user:
            flash('An account with this email address is already registered. Please sign in.', 'warning')
            return redirect(url_for('auth.login'))

        # 6. SHA-256 Tokenization & Identity Masking
        # Raw MyKad is immediately tokenized and discarded.
        mykad_hash = hash_mykad(normalized_ic)
        masked_ic = mask_mykad(normalized_ic)

        # Check if identity is already registered (anti-scalping 1 person = 1 account)
        existing_ic_user = get_user_by_mykad_hash(mykad_hash)
        if existing_ic_user:
            flash('An account is already registered with this Malaysian MyKad identity.', 'warning')
            return render_template('register.html', name=name, email=email)

        # 7. Cryptographic Password Hashing (BCrypt)
        hashed_pw = hash_password(password)

        # 8. Database Insertion - Role is STRICTLY Customer (No Admin creation allowed via register)
        # Raw MyKad is NEVER sent or stored!
        try:
            create_customer_user(
                name=name,
                email=email,
                password_hash=hashed_pw,
                mykad_hash=mykad_hash,
                masked_ic=masked_ic,
                pdpa_consent=True
            )
            flash(f'Registration successful! Identity tokenized ({masked_ic}) in compliance with PDPA 2010. Please sign in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred while creating your account: {str(e)}', 'danger')
            return render_template('register.html', name=name, email=email)

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User Login:
    - Authenticates credentials against BCrypt hash.
    - Issues signed JWT token in HTTP-only cookie.
    - Redirects Admin to /admin and Customer to /dashboard.
    """
    # If already logged in, redirect appropriately
    user = get_current_user_from_request()
    if user:
        if user.get('role') == 'Admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both your email and password.', 'warning')
            return render_template('login.html', email=email)

        user = get_user_by_email(email)

        # Verify existence and BCrypt password hash
        if user and verify_password(password, user['password_hash']):
            # Generate JWT Token containing user_id, email, name, role
            token = generate_jwt_token(user)

            # Determine destination based on role
            next_url = request.args.get('next')
            if not next_url:
                next_url = url_for('admin_dashboard') if user['role'] == 'Admin' else url_for('dashboard')

            response = make_response(redirect(next_url))

            # Store JWT in secure HTTP-only cookie
            response.set_cookie(
                key=Config.JWT_COOKIE_NAME,
                value=token,
                httponly=Config.JWT_COOKIE_HTTPONLY,
                secure=Config.JWT_COOKIE_SECURE,
                samesite=Config.JWT_COOKIE_SAMESITE,
                max_age=Config.JWT_EXPIRATION_HOURS * 3600
            )

            flash(f'Welcome back, {user["name"]}! Successfully authenticated as {user["role"]}.', 'success')
            return response
        else:
            flash('Invalid email address or password. Please try again.', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    User Logout:
    - Clears the JWT session cookie.
    - Redirects to login page with notification.
    """
    response = make_response(redirect(url_for('auth.login')))
    response.set_cookie(Config.JWT_COOKIE_NAME, '', expires=0, httponly=True)
    flash('You have been securely logged out.', 'info')
    return response
