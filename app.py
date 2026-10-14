import os
import uuid
import json
import re
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g, abort, current_app
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import base64
from gradio_client import Client, handle_file
from config import Config
from database.db import get_db, close_db, init_db, query_db, execute_db
from recommendation_engine import generate_recommendation

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure required directories exist
    os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['WARDROBE_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config.get('TRYON_UPLOAD_FOLDER', os.path.join(app.config['UPLOAD_FOLDER'], 'tryon_results')), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)

    # Teardown database connection
    app.teardown_appcontext(close_db)

    # Initialize SQLite database tables safely on startup
    with app.app_context():
        init_db(app)

    # Register all routes on the application
    register_routes(app)

    return app

# ========================================================
# Helper Functions & Decorators
# ========================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # For AJAX / fetch requests (API routes), return JSON 401 instead of
            # an HTML redirect — which causes response.json() to throw SyntaxError
            # in the browser and show "Connection Error".
            is_api = (
                request.path.startswith('/api/')
                or request.is_json
                or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or 'application/json' in request.headers.get('Accept', '')
            )
            if is_api:
                return jsonify({
                    'success': False,
                    'error': 'Session expired. Please log in again to use Virtual Try-On.',
                    'redirect': url_for('login')
                }), 401
            flash("Please log in to access this page.", "info")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def validate_and_save_image(file_storage, target_folder, relative_subpath):
    """
    Validates file extension and actual image contents using Pillow,
    saves the file with a secure unique filename, and returns the relative path.
    """
    if not file_storage or file_storage.filename == '':
        return None

    if not allowed_file(file_storage.filename):
        return False

    unique_name = f"{uuid.uuid4().hex}_{secure_filename(file_storage.filename)}"
    destination_path = os.path.join(target_folder, unique_name)

    try:
        file_storage.seek(0)
        img = Image.open(file_storage)
        img.verify()
        file_storage.seek(0)
        file_storage.save(destination_path)
    except Exception as e:
        current_app.logger.error(f"Image validation/save failed: {e}")
        return False

    return f"uploads/{relative_subpath}/{unique_name}"

def safe_delete_upload(relative_path):
    """Safely deletes an obsolete upload from disk if it exists."""
    if not relative_path:
        return
    full_path = os.path.join(current_app.root_path, 'static', relative_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        try:
            os.remove(full_path)
        except OSError as e:
            current_app.logger.warning(f"Could not remove old file {full_path}: {e}")

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)

def get_current_profile(user_id):
    profile = query_db("SELECT * FROM profiles WHERE user_id = ?", (user_id,), one=True)
    if not profile:
        execute_db("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
        profile = query_db("SELECT * FROM profiles WHERE user_id = ?", (user_id,), one=True)
    return profile

def register_routes(app):
    # ========================================================
    # Authentication Routes
    # ========================================================

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            if request.is_json:
                data = request.get_json() or {}
                email = data.get('email', '').strip().lower()
                password = data.get('password', '')
                remember = bool(data.get('remember'))
            else:
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password', '')
                remember = bool(request.form.get('remember'))

            if not email or not password:
                msg = "Please enter both email and password."
                if request.is_json:
                    return jsonify({'success': False, 'error': msg}), 400
                flash(msg, "danger")
                return render_template('login.html', email=email)

            try:
                user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
            except Exception as e:
                current_app.logger.error(f"Database error during login: {e}")
                msg = "A database error occurred. Please try again."
                if request.is_json:
                    return jsonify({'success': False, 'error': msg}), 500
                flash(msg, "danger")
                return render_template('login.html', email=email)

            if user and check_password_hash(user['password_hash'], password):
                session.clear()
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['user_email'] = user['email']
                if remember:
                    session.permanent = True

                flash(f"Welcome back, {user['full_name']}! ✨", "success")
                next_url = request.args.get('next')
                target = next_url or url_for('dashboard')
                if request.is_json:
                    return jsonify({'success': True, 'redirect': target})
                return redirect(target)
            else:
                msg = "Invalid email or password. Please try again."
                if request.is_json:
                    return jsonify({'success': False, 'error': msg}), 401
                flash(msg, "danger")
                return render_template('login.html', email=email)

        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    @app.route('/register', methods=['GET', 'POST'])
    def signup():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            if request.is_json:
                data = request.get_json() or {}
                name = data.get('name', '').strip()
                email = data.get('email', '').strip().lower()
                password = data.get('password', '')
                confirm_password = data.get('confirm_password') or data.get('confirmPassword') or ''
                terms = data.get('terms')
            else:
                name = request.form.get('name', '').strip()
                email = request.form.get('email', '').strip().lower()
                password = request.form.get('password', '')
                confirm_password = request.form.get('confirm_password') or request.form.get('confirmPassword') or ''
                terms = request.form.get('terms')

            if not name or not email or not password or not confirm_password:
                msg = "All fields are required."
                if request.is_json:
                    return jsonify({'success': False, 'error': msg}), 400
                flash(msg, "danger")
                return render_template('signup.html', name=name, email=email)

            if not is_valid_email(email):
                msg = "Please enter a valid email address."
                if request.is_json:
                    return jsonify({'success': False, 'error': msg}), 400
                flash(msg, "danger")
                return render_template('signup.html', name=name, email=email)

            if len(password) < 6:
                msg = "Password must be at least 6 characters long."
                if request.is_json:
                    return jsonify({'success': False, 'error': msg}), 400
                flash(msg, "danger")
                return render_template('signup.html', name=name, email=email)

            if password != confirm_password:
                msg = "Passwords do not match."
                if request.is_json:
                    return jsonify({'success': False, 'error': msg}), 400
                flash(msg, "danger")
                return render_template('signup.html', name=name, email=email)

            if not terms:
                msg = "You must agree to the terms and conditions."
                if request.is_json:
                    return jsonify({'success': False, 'error': msg}), 400
                flash(msg, "danger")
                return render_template('signup.html', name=name, email=email)

            try:
                existing_user = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
                if existing_user:
                    msg = "An account with this email address already exists. Please log in."
                    if request.is_json:
                        return jsonify({'success': False, 'error': msg}), 409
                    flash(msg, "danger")
                    return render_template('signup.html', name=name, email=email)

                password_hash = generate_password_hash(password)
                user_id = execute_db(
                    "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, password_hash)
                )

                # Create corresponding profile record
                execute_db("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))

                flash("Account created successfully! Please log in to get started ✨", "success")
                if request.is_json:
                    return jsonify({'success': True, 'redirect': url_for('login')})
                return redirect(url_for('login'))

            except Exception as e:
                current_app.logger.error(f"Registration error: {e}")
                msg = "A database error occurred during registration. Please try again."
                if request.is_json:
                    return jsonify({'success': False, 'error': msg}), 500
                flash(msg, "danger")
                return render_template('signup.html', name=name, email=email)

        return render_template('signup.html')

    @app.route('/login.html')
    def login_html_alias():
        return redirect(url_for('login'))

    @app.route('/signup.html')
    @app.route('/register.html')
    def signup_html_alias():
        return redirect(url_for('signup'))

    @app.route('/logout', methods=['GET', 'POST'])
    def logout():
        session.clear()
        flash("You have been successfully logged out.", "info")
        return redirect(url_for('login'))

    # ========================================================
    # Dashboard
    # ========================================================

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user = get_current_user()
        if not user:
            session.clear()
            return redirect(url_for('login'))

        profile = get_current_profile(user['id'])

        wardrobe_count_row = query_db(
            "SELECT COUNT(*) as count FROM wardrobe_items WHERE user_id = ?",
            (user['id'],),
            one=True
        )
        wardrobe_count = wardrobe_count_row['count'] if wardrobe_count_row else 0

        favorites_count_row = query_db(
            "SELECT COUNT(*) as count FROM favorites WHERE user_id = ?",
            (user['id'],),
            one=True
        )
        favorites_count = favorites_count_row['count'] if favorites_count_row else 0

        return render_template(
            'dashboard.html',
            user=user,
            profile=profile,
            wardrobe_count=wardrobe_count,
            favorites_count=favorites_count
        )

    # ========================================================
    # Wardrobe Management
    # ========================================================

    @app.route('/wardrobe')
    @login_required
    def wardrobe():
        user_id = session['user_id']
        items = query_db(
            "SELECT * FROM wardrobe_items WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return render_template('wardrobe.html', items=items)

    @app.route('/wardrobe/add', methods=['POST'])
    @login_required
    def add_wardrobe_item():
        user_id = session['user_id']
        item_name = request.form.get('item_name', '').strip()
        category = request.form.get('category', '').strip()
        color = request.form.get('color', '').strip()
        style = request.form.get('style', '').strip()
        description = request.form.get('description', '').strip()
        photo_file = request.files.get('photo')

        if not item_name or not category or not color or not style:
            flash("Please fill in all required clothing fields.", "danger")
            return redirect(url_for('wardrobe'))

        image_path = ""
        if photo_file and photo_file.filename != '':
            saved = validate_and_save_image(
                photo_file,
                current_app.config['WARDROBE_UPLOAD_FOLDER'],
                'wardrobe'
            )
            if saved is False:
                flash("Invalid photo format or corrupt image file (Allowed: PNG, JPG, JPEG, WebP < 5MB).", "danger")
                return redirect(url_for('wardrobe'))
            elif saved:
                image_path = saved

        execute_db(
            """INSERT INTO wardrobe_items 
               (user_id, item_name, category, color, style, description, image_path) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, item_name, category, color, style, description, image_path)
        )

        flash(f"'{item_name}' was added to your closet! ✨", "success")
        return redirect(url_for('wardrobe'))

    @app.route('/wardrobe/<int:item_id>/edit', methods=['POST'])
    @login_required
    def edit_wardrobe_item(item_id):
        user_id = session['user_id']
        item = query_db(
            "SELECT * FROM wardrobe_items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
            one=True
        )
        if not item:
            flash("Clothing item not found or unauthorized.", "danger")
            return redirect(url_for('wardrobe'))

        item_name = request.form.get('item_name', '').strip()
        category = request.form.get('category', '').strip()
        color = request.form.get('color', '').strip()
        style = request.form.get('style', '').strip()
        description = request.form.get('description', '').strip()
        photo_file = request.files.get('photo')

        if not item_name or not category or not color or not style:
            flash("Please provide all required fields.", "danger")
            return redirect(url_for('wardrobe'))

        image_path = item['image_path']
        if photo_file and photo_file.filename != '':
            saved = validate_and_save_image(
                photo_file,
                current_app.config['WARDROBE_UPLOAD_FOLDER'],
                'wardrobe'
            )
            if saved is False:
                flash("Invalid photo format or corrupt file.", "danger")
                return redirect(url_for('wardrobe'))
            elif saved:
                safe_delete_upload(item['image_path'])
                image_path = saved

        execute_db(
            """UPDATE wardrobe_items 
               SET item_name = ?, category = ?, color = ?, style = ?, description = ?, image_path = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ? AND user_id = ?""",
            (item_name, category, color, style, description, image_path, item_id, user_id)
        )

        flash(f"'{item_name}' has been updated successfully! ✨", "success")
        return redirect(url_for('wardrobe'))

    @app.route('/wardrobe/<int:item_id>/delete', methods=['POST'])
    @login_required
    def delete_wardrobe_item(item_id):
        user_id = session['user_id']
        item = query_db(
            "SELECT * FROM wardrobe_items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
            one=True
        )
        if not item:
            flash("Item not found or unauthorized.", "danger")
            return redirect(url_for('wardrobe'))

        safe_delete_upload(item['image_path'])
        execute_db("DELETE FROM wardrobe_items WHERE id = ? AND user_id = ?", (item_id, user_id))
        flash(f"'{item['item_name']}' was removed from your wardrobe.", "info")
        return redirect(url_for('wardrobe'))

    # ========================================================
    # Profile & Photo Management
    # ========================================================

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        user_id = user['id']
        user_profile = get_current_profile(user_id)

        if request.method == 'POST':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            age_val = request.form.get('age', '').strip()
            age = int(age_val) if age_val and age_val.isdigit() else None

            if not full_name or not email:
                flash("Full name and email cannot be empty.", "danger")
                return redirect(url_for('profile'))

            if not is_valid_email(email):
                flash("Invalid email address format.", "danger")
                return redirect(url_for('profile'))

            if email != user['email']:
                conflict = query_db("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id), one=True)
                if conflict:
                    flash("This email is already in use by another account.", "danger")
                    return redirect(url_for('profile'))

            execute_db("UPDATE users SET full_name = ?, email = ? WHERE id = ?", (full_name, email, user_id))
            execute_db("UPDATE profiles SET age = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (age, user_id))
            session['user_name'] = full_name
            session['user_email'] = email

            flash("Profile personal details updated successfully! ✨", "success")
            return redirect(url_for('profile'))

        favorites = query_db("SELECT * FROM favorites WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        wardrobe_items = query_db("SELECT * FROM wardrobe_items WHERE user_id = ?", (user_id,))

        return render_template(
            'profile.html',
            user=user,
            profile=user_profile,
            favorites=favorites,
            wardrobe_items=wardrobe_items
        )

    @app.route('/profile/photo', methods=['POST'])
    @login_required
    def update_profile_photo():
        user_id = session['user_id']
        profile = get_current_profile(user_id)
        photo_file = request.files.get('profile_photo')

        if not photo_file or photo_file.filename == '':
            flash("No photo selected.", "danger")
            return redirect(url_for('profile'))

        saved_path = validate_and_save_image(
            photo_file,
            current_app.config['PROFILE_UPLOAD_FOLDER'],
            'profiles'
        )

        if saved_path is False:
            flash("Invalid image format or corrupt photo (Allowed: PNG, JPG, JPEG, WebP < 5MB).", "danger")
            return redirect(url_for('profile'))
        elif saved_path:
            if profile and profile['profile_photo']:
                safe_delete_upload(profile['profile_photo'])

            execute_db(
                "UPDATE profiles SET profile_photo = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (saved_path, user_id)
            )
            flash("Profile photo updated successfully! 📸✨", "success")

        return redirect(url_for('profile'))

    @app.route('/profile/photo/remove', methods=['POST'])
    @login_required
    def remove_profile_photo():
        user_id = session['user_id']
        profile = get_current_profile(user_id)

        if profile and profile['profile_photo']:
            safe_delete_upload(profile['profile_photo'])
            execute_db(
                "UPDATE profiles SET profile_photo = '', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            flash("Profile photo removed.", "info")

        return redirect(url_for('profile'))

    @app.route('/profile/preferences', methods=['POST'])
    @login_required
    def update_preferences():
        user_id = session['user_id']
        preferred_style = request.form.get('preferred_style', '').strip()
        preferred_color = request.form.get('preferred_color', '').strip()
        preferred_fit = request.form.get('preferred_fit', '').strip()
        favorite_occasion = request.form.get('favorite_occasion', '').strip()

        execute_db(
            """UPDATE profiles 
               SET preferred_style = ?, preferred_color = ?, preferred_fit = ?, favorite_occasion = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE user_id = ?""",
            (preferred_style, preferred_color, preferred_fit, favorite_occasion, user_id)
        )

        flash("Style preferences saved! 💜", "success")
        return redirect(url_for('profile'))

    # ========================================================
    # Style Me / Recommendation & Results
    # ========================================================

    @app.route('/recommendation', methods=['GET', 'POST'])
    @app.route('/recomend', methods=['GET', 'POST'])
    @app.route('/style', methods=['GET', 'POST'])
    def recommendation():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user_id = session['user_id']
        profile = get_current_profile(user_id)

        if request.method == 'POST':
            occasion = request.form.get('occasion', 'Casual').strip()
            style = request.form.get('style', 'Trendy').strip()
            weather = request.form.get('weather', 'Sunny').strip()
            color = request.form.get('color', 'Any').strip()
            notes = request.form.get('notes', '').strip()

            wardrobe_items = query_db("SELECT * FROM wardrobe_items WHERE user_id = ?", (user_id,))

            outfit_result = generate_recommendation(
                wardrobe_items,
                occasion=occasion,
                style=style,
                weather=weather,
                preferred_color=color,
                notes=notes
            )

            rec_json = json.dumps(outfit_result, default=str)
            rec_id = execute_db(
                """INSERT INTO recommendations 
                   (user_id, occasion, style, weather, recommendation_data) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, occasion, style, weather, rec_json)
            )

            return redirect(url_for('result', rec_id=rec_id))

        selected_occasion = request.args.get('occasion', '')
        return render_template('recommendation.html', profile=profile, selected_occasion=selected_occasion)

    @app.route('/result')
    @app.route('/result/<int:rec_id>')
    @login_required
    def result(rec_id=None):
        user_id = session['user_id']

        if rec_id:
            rec = query_db(
                "SELECT * FROM recommendations WHERE id = ? AND user_id = ?",
                (rec_id, user_id),
                one=True
            )
        else:
            rec = query_db(
                "SELECT * FROM recommendations WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,),
                one=True
            )

        if not rec:
            flash("No recommendations generated yet. Tell us your plan first!", "info")
            return redirect(url_for('recommendation'))

        try:
            outfit_data = json.loads(rec['recommendation_data'])
        except Exception:
            outfit_data = {}

        return render_template('result.html', rec=rec, outfit=outfit_data)

    # ========================================================
    # Favorites
    # ========================================================

    @app.route('/favorites')
    @login_required
    def favorites():
        user_id = session['user_id']
        favs = query_db(
            "SELECT * FROM favorites WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )

        parsed_favs = []
        for f in favs:
            item_dict = dict(f)
            try:
                item_dict['data'] = json.loads(f['outfit_data'])
            except Exception:
                item_dict['data'] = {}
            parsed_favs.append(item_dict)

        return render_template('favorites.html', favorites=parsed_favs)

    @app.route('/favorites/save', methods=['POST'])
    @login_required
    def save_favorite():
        user_id = session['user_id']
        data = request.get_json() or {}
        rec_id = data.get('recommendation_id')

        if not rec_id:
            return jsonify({'success': False, 'error': 'Missing recommendation ID'}), 400

        rec = query_db(
            "SELECT * FROM recommendations WHERE id = ? AND user_id = ?",
            (rec_id, user_id),
            one=True
        )

        if not rec:
            return jsonify({'success': False, 'error': 'Recommendation not found'}), 404

        try:
            outfit_data = json.loads(rec['recommendation_data'])
            outfit_name = outfit_data.get('title', 'Curated Outfit')
        except Exception:
            outfit_name = 'Curated Outfit'

        existing = query_db(
            "SELECT id FROM favorites WHERE user_id = ? AND outfit_name = ? AND occasion = ?",
            (user_id, outfit_name, rec['occasion']),
            one=True
        )
        if existing:
            return jsonify({'success': True, 'message': 'Already in favorites!'})

        execute_db(
            "INSERT INTO favorites (user_id, outfit_name, occasion, outfit_data) VALUES (?, ?, ?, ?)",
            (user_id, outfit_name, rec['occasion'], rec['recommendation_data'])
        )

        return jsonify({'success': True, 'message': 'Outfit saved to favorites!'})

    @app.route('/favorites/<int:fav_id>/delete', methods=['POST'])
    @login_required
    def delete_favorite(fav_id):
        user_id = session['user_id']
        fav = query_db("SELECT * FROM favorites WHERE id = ? AND user_id = ?", (fav_id, user_id), one=True)
        if not fav:
            flash("Favorite not found or unauthorized.", "danger")
            return redirect(url_for('favorites'))

        execute_db("DELETE FROM favorites WHERE id = ? AND user_id = ?", (fav_id, user_id))
        flash("Outfit removed from your favorites.", "info")
        return redirect(url_for('favorites'))

    # ========================================================
    # Virtual Try-On API (IDM-VTON Integration)
    # ========================================================

    @app.route('/api/virtual-tryon', methods=['POST'])
    @login_required
    def api_virtual_tryon():
        import time
        import shutil

        user_id = session['user_id']

        # Determine if request is multipart/form-data or application/json
        is_multipart = request.content_type and 'multipart/form-data' in request.content_type
        if is_multipart:
            data = request.form
        else:
            data = request.get_json() or {}

        # ── 1. Check User Consent ──────────────────────────────────────
        consent_raw = data.get('consent_given')
        consent_given = consent_raw in (True, 'true', 'True', '1', 'on')

        if not consent_given:
            return jsonify({
                'success': False,
                'error': 'User consent is required before processing photographs for Virtual Try-On.'
            }), 400

        temp_files_to_cleanup = []

        try:
            # ── 2. Resolve Person Photo ─────────────────────────────────
            # Priority A: Directly uploaded person photo in this request
            person_file = request.files.get('person_image') if is_multipart else None
            person_photo_path = None

            if person_file and person_file.filename != '':
                if not allowed_file(person_file.filename):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid person photo format. Allowed: PNG, JPG, JPEG, WebP.'
                    }), 400
                temp_person_name = f"temp_person_{uuid.uuid4().hex}_{secure_filename(person_file.filename)}"
                temp_person_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_person_name)
                try:
                    person_file.seek(0)
                    img = Image.open(person_file)
                    img.verify()
                    person_file.seek(0)
                    person_file.save(temp_person_path)
                    person_photo_path = temp_person_path
                    temp_files_to_cleanup.append(temp_person_path)
                except Exception as e:
                    current_app.logger.error(f"Invalid uploaded person photo: {e}")
                    return jsonify({
                        'success': False,
                        'error': 'Uploaded person photo is corrupt or unreadable. Please choose a valid image.'
                    }), 400

            # Priority B: Profile photo from user profile in database
            if not person_photo_path:
                profile = get_current_profile(user_id)
                if not profile or not profile['profile_photo']:
                    return jsonify({
                        'success': False,
                        'error': 'No personal photo found. Please upload a photo or set your profile photo first.'
                    }), 400

                rel_part = profile['profile_photo'].replace('uploads/', '', 1) if profile['profile_photo'].startswith('uploads/') else profile['profile_photo']
                candidate_path = os.path.join(current_app.config['UPLOAD_FOLDER'], rel_part)
                if not os.path.isfile(candidate_path):
                    candidate_path = os.path.join(current_app.root_path, 'static', profile['profile_photo'])

                if not os.path.isfile(candidate_path):
                    return jsonify({
                        'success': False,
                        'error': 'Your profile photo file is missing from the server. Please re-upload it.'
                    }), 400
                person_photo_path = candidate_path

            # ── 3. Resolve Clothing Item & Image ───────────────────────
            clothing_file = request.files.get('garment_image') if is_multipart else None
            clothing_image_path = None
            garment_name = None
            garment_category = None

            if clothing_file and clothing_file.filename != '':
                if not allowed_file(clothing_file.filename):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid clothing image format. Allowed: PNG, JPG, JPEG, WebP.'
                    }), 400
                temp_garment_name = f"temp_garment_{uuid.uuid4().hex}_{secure_filename(clothing_file.filename)}"
                temp_garment_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_garment_name)
                try:
                    clothing_file.seek(0)
                    img = Image.open(clothing_file)
                    img.verify()
                    clothing_file.seek(0)
                    clothing_file.save(temp_garment_path)
                    clothing_image_path = temp_garment_path
                    temp_files_to_cleanup.append(temp_garment_path)
                except Exception as e:
                    current_app.logger.error(f"Invalid uploaded garment photo: {e}")
                    return jsonify({
                        'success': False,
                        'error': 'Uploaded clothing image is corrupt or unreadable. Please choose a valid image.'
                    }), 400

                garment_category = (data.get('category') or 'upper_body').strip()
                garment_name = (data.get('garment_description') or 'Custom Garment').strip()

            if not clothing_image_path:
                # Resolve clothing item from wardrobe or favorites
                outfit_id = data.get('outfit_id', '')
                item_ids = data.get('item_ids', [])
                clothing_item = None

                if item_ids:
                    first_id = int(item_ids[0])
                    row = query_db(
                        "SELECT * FROM wardrobe_items WHERE id = ? AND user_id = ?",
                        (first_id, user_id), one=True
                    )
                    clothing_item = dict(row) if row else None
                elif outfit_id and outfit_id.startswith('item_'):
                    try:
                        item_db_id = int(outfit_id.replace('item_', ''))
                        row = query_db(
                            "SELECT * FROM wardrobe_items WHERE id = ? AND user_id = ?",
                            (item_db_id, user_id), one=True
                        )
                        clothing_item = dict(row) if row else None
                    except ValueError:
                        pass
                elif outfit_id and outfit_id.startswith('fav_'):
                    try:
                        fav_db_id = int(outfit_id.replace('fav_', ''))
                        fav = query_db(
                            "SELECT * FROM favorites WHERE id = ? AND user_id = ?",
                            (fav_db_id, user_id), one=True
                        )
                        if fav:
                            try:
                                fav_data = json.loads(fav['outfit_data'])
                                clothing_items_list = fav_data.get('clothing_items') or fav_data.get('items', [])
                                if clothing_items_list:
                                    first_ci = clothing_items_list[0]
                                    if isinstance(first_ci, dict):
                                        ci_id = first_ci.get('id')
                                        if ci_id:
                                            row = query_db(
                                                "SELECT * FROM wardrobe_items WHERE id = ? AND user_id = ?",
                                                (int(ci_id), user_id), one=True
                                            )
                                            clothing_item = dict(row) if row else None
                            except Exception:
                                pass
                    except ValueError:
                        pass
                else:
                    all_items = query_db(
                        "SELECT * FROM wardrobe_items WHERE user_id = ? AND image_path IS NOT NULL AND image_path != '' LIMIT 1",
                        (user_id,)
                    )
                    if all_items:
                        clothing_item = dict(all_items[0])

                if not clothing_item or not clothing_item.get('image_path'):
                    return jsonify({
                        'success': False,
                        'error': (
                            'No clothing item with an image found. '
                            'Please upload a clothing photo or select an item from your Wardrobe.'
                        )
                    }), 400

                rel_cloth = clothing_item['image_path'].replace('uploads/', '', 1) if clothing_item['image_path'].startswith('uploads/') else clothing_item['image_path']
                candidate_cloth = os.path.join(current_app.config['UPLOAD_FOLDER'], rel_cloth)
                if not os.path.isfile(candidate_cloth):
                    candidate_cloth = os.path.join(current_app.root_path, 'static', clothing_item['image_path'])

                if not os.path.isfile(candidate_cloth):
                    return jsonify({
                        'success': False,
                        'error': f'Clothing image file for "{clothing_item["item_name"]}" is missing. Please re-upload the item.'
                    }), 400
                clothing_image_path = candidate_cloth

                garment_name = clothing_item['item_name']
                garment_category = clothing_item.get('category', '')

            # ── 4. Call IDM-VTON via Gradio Client ──────────────────────
            # Genuinely free: connects to official public Space yisol/IDM-VTON.
            # Optional HF_TOKEN can be used if provided in env, but is not required.
            hf_token = (os.getenv('HF_TOKEN') or '').strip() or None

            try:
                client = Client("yisol/IDM-VTON", token=hf_token, httpx_kwargs={"timeout": 120.0})

                garment_desc = garment_name or garment_category or 'clothing'

                person_dict = {
                    "background": handle_file(person_photo_path),
                    "layers": [],
                    "composite": handle_file(person_photo_path),
                }
                garment_file = handle_file(clothing_image_path)

                job = client.submit(
                    person_dict,
                    garment_file,
                    garment_desc,
                    True,   # is_checked (auto mask)
                    False,  # is_checked_crop
                    30,     # denoise_steps
                    42,     # seed
                    api_name="/tryon",
                )

                max_wait_seconds = 180
                start_wait = time.time()
                while not job.done():
                    if time.time() - start_wait > max_wait_seconds:
                        try:
                            job.cancel()
                        except Exception:
                            pass
                        raise TimeoutError(
                            "The IDM-VTON model request timed out waiting in the generation queue. "
                            "Please try again in a moment."
                        )
                    time.sleep(3)

                result = job.result()

                if not result or not isinstance(result, (list, tuple)) or len(result) == 0:
                    return jsonify({
                        'success': False,
                        'error': 'IDM-VTON returned an empty or invalid response. Please try again.'
                    }), 502

                generated_tmp_path = result[0]
                if isinstance(generated_tmp_path, dict):
                    generated_tmp_path = generated_tmp_path.get('path') or generated_tmp_path.get('url') or ''

                if not generated_tmp_path or not os.path.isfile(str(generated_tmp_path)):
                    return jsonify({
                        'success': False,
                        'error': 'IDM-VTON did not return a valid output image. Please try again.'
                    }), 502

                # Save final try-on result to static uploads
                tryon_results_dir = current_app.config.get(
                    'TRYON_UPLOAD_FOLDER',
                    os.path.join(current_app.root_path, 'static', 'uploads', 'tryon_results')
                )
                os.makedirs(tryon_results_dir, exist_ok=True)
                result_filename = f"{uuid.uuid4().hex}_tryon.png"
                result_save_path = os.path.join(tryon_results_dir, result_filename)

                shutil.copy2(str(generated_tmp_path), result_save_path)

                relative_path = f'uploads/tryon_results/{result_filename}'
                generated_image_url = url_for('static', filename=relative_path)

                return jsonify({
                    'success': True,
                    'generated_image': generated_image_url,
                    'clothing_item': garment_name,
                    'category': garment_category,
                    'message': f'Virtual Try-On complete! Wearing: {garment_name} ✨'
                })

            except TimeoutError as te:
                current_app.logger.warning(f"[Virtual Try-On] Timeout: {te}")
                return jsonify({
                    'success': False,
                    'error': str(te)
                }), 504
            except Exception as exc:
                err_str = str(exc)
                current_app.logger.error(f"[Virtual Try-On] IDM-VTON error: {exc}", exc_info=True)

                if 'queue' in err_str.lower() or 'busy' in err_str.lower():
                    friendly = 'The IDM-VTON service queue is currently busy. Please try again in a few moments.'
                elif 'gpu' in err_str.lower() or 'quota' in err_str.lower():
                    friendly = 'The free ZeroGPU allocation is temporarily refreshed. Please try again shortly.'
                elif 'timeout' in err_str.lower():
                    friendly = 'The IDM-VTON request timed out. Please try again.'
                elif '401' in err_str or 'unauthorized' in err_str.lower():
                    friendly = 'Authentication error with Hugging Face. Check your HF_TOKEN if configured, or leave it blank for free access.'
                elif 'IndexError' in err_str:
                    friendly = 'IDM-VTON could not detect a person silhouette in the provided photo. Please ensure your photo clearly shows your upper body/face.'
                else:
                    friendly = f'IDM-VTON Virtual Try-On failed: {err_str}'

                return jsonify({
                    'success': False,
                    'error': friendly
                }), 502

        finally:
            # Clean up temporary uploaded files so personal images are not kept permanently
            for temp_p in temp_files_to_cleanup:
                try:
                    if os.path.exists(temp_p):
                        os.remove(temp_p)
                except Exception as e:
                    current_app.logger.warning(f"Could not remove temp try-on file {temp_p}: {e}")


    # ========================================================
    # Error Handlers
    # ========================================================

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', content="<div class='page-container' style='text-align:center;'><h1>404</h1><p>Page not found.</p><a href='/'>Go Home</a></div>"), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        flash("The uploaded file is too large. Maximum allowed size is 5MB.", "danger")
        return redirect(request.referrer or url_for('dashboard'))

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', content="<div class='page-container' style='text-align:center;'><h1>500</h1><p>Something went wrong on our end.</p><a href='/'>Go Home</a></div>"), 500

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
