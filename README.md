# ✦ GRWM — GET READY WITH ME

> **Personal Wardrobe & AI Outfit Styling Web Application**  
> Built with Python, Flask, SQLite, and Vanilla HTML5/CSS3/JavaScript.

---

## 🌸 Overview

**GRWM (Get Ready With Me)** is a full-stack fashion web application designed to help you curate your personal wardrobe, upload actual photos of your clothing pieces, manage style preferences, and receive intelligent, explainable outfit recommendations tailored to specific occasions, vibes, and weather.

### 💖 Key Features
- **Authentication**: Secure account registration and login with Werkzeug password hashing, session cookies, and route protection.
- **My Wardrobe (CRUD & Photo Uploads)**: Add, view, search, filter, edit, and delete clothing pieces with live photo previews and server-side image validation.
- **Profile & Personal Styling Space**: Update personal info, favorite styles, colors, fits, and occasions. Persistent profile photo uploads with instant live preview.
- **Smart "Style Me" Recommendation Engine**: Rule-based outfit matching engine that queries your personal wardrobe, balances tops, bottoms, dresses, outerwear, shoes, and accessories, and explains why items were paired together.
- **Saved Favorites**: Save your favorite generated looks to your personal collection with one click, with quick-access thumbnails and deletion capabilities.
- **Virtual Try-On Studio**: An authentic AI try-on interface powered by **IDM-VTON** (*Improving Diffusion Models for Authentic Virtual Try-On in the Wild*). Users can upload their own photo, upload clothing pieces or pick from their wardrobe, generate realistic try-on results, view them on-page, and download them — completely free with zero required API keys or paid tiers.
- **Consistent Visual Identity**: Signature GRWM aesthetic with `#8b5cf6` (purple) and `#ec4899` (pink) gradients, soft background blobs, Playfair Display and DM Sans typography, rounded cards, and responsive layouts across mobile, tablet, and desktop.

---

## 📁 Project Structure

```text
GRWM/
│
├── app.py                      # Flask backend entry point and route controllers
├── config.py                   # App configuration & environment loading
├── recommendation_engine.py    # Curated outfit matching algorithms
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment configuration file
├── .gitignore                  # Git ignore rules for virtualenvs, DB, uploads
├── README.md                   # Complete documentation and setup guide
│
├── database/
│   ├── db.py                   # SQLite connection helpers and query functions
│   ├── schema.sql              # Database table definitions and indexes
│   └── grwm.db                 # Auto-generated SQLite database file
│
├── templates/
│   ├── base.html               # Shared layout, navbar, blobs, and toast container
│   ├── login.html              # Login screen with fit-check card
│   ├── signup.html             # Signup screen with password strength meter
│   ├── dashboard.html          # Dashboard with live wardrobe counter and shortcuts
│   ├── profile.html            # Profile info, photo upload, and Virtual Try-On
│   ├── wardrobe.html           # Wardrobe manager, item cards, and edit modal
│   ├── recommendation.html     # Style Me form for occasion, vibe, and weather
│   ├── result.html             # Recommendation results with wardrobe item cards
│   └── favorites.html          # Saved outfit collection
│
├── static/
│   ├── css/
│   │   └── style.css           # Unified stylesheet preserving GRWM design system
│   ├── js/
│   │   └── file.js             # Shared frontend JavaScript (validation, previews, modals)
│   ├── images/
│   │   └── default-profile.png # Default fallback avatar
│   └── uploads/
│       ├── profiles/           # Uploaded user profile photos
│       └── wardrobe/           # Uploaded user clothing photos
│
└── tests/
    └── test_app.py             # Automated unit and integration test suite
```

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript (no external heavy frontend frameworks).
- **Backend**: Python 3.10+, Flask 3.1.3, Jinja2, Werkzeug.
- **Database**: SQLite3 with foreign-key enforcement (`PRAGMA foreign_keys = ON;`).
- **Image Processing**: Pillow (PIL) for image content verification and dimensions.
- **Security**: Werkzeug secure password hashing (`generate_password_hash`), secure filenames, UUID uniqueness prefixes, and MIME validation.

---

## 🚀 Beginner-Friendly Setup Guide (Windows PowerShell)

Follow these step-by-step instructions in Windows PowerShell to set up and run GRWM on your computer.

### Step 1: Open the Project Folder
Open Windows PowerShell and navigate to the project directory:
```powershell
cd c:\Users\User\Desktop\GRWM
```

### Step 2: Create a Python Virtual Environment
A virtual environment ensures the project dependencies don't interfere with your global Python installation:
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
On Windows PowerShell, activate the virtual environment by running:
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If you see an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once, then re-run the activation script).*

### Step 4: Install Dependencies
Install all required libraries specified in `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Copy the example environment configuration to create your local `.env` file:
```powershell
Copy-Item .env.example .env
```
You can open `.env` in any text editor (like Notepad or VS Code) to customize your `SECRET_KEY`.

### Step 6: Start the Flask Application
Run the Flask server:
```powershell
python app.py
```
You will see output similar to:
```text
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```
> **Note**: The SQLite database (`database/grwm.db`) and all required upload folders (`static/uploads/profiles/`, `static/uploads/wardrobe/`) are initialized automatically the first time you run the application.

### Step 7: Open in Your Browser
Open your favorite web browser and visit:
```text
http://127.0.0.1:5000
```

---

## 🧪 Testing and Verifying Features

### 1. Account Creation & Login
- Click **"Create an account"** on the login page.
- Enter your name, email, and password. Notice the live password strength meter in action.
- Accept the terms and click **"Create My Account ✨"**.
- Log in with your new email and password.

### 2. Add Wardrobe Items with Photos
- Navigate to **"Wardrobe"** in the top navigation bar.
- In the "Add a new piece" form, enter an item name (e.g., `Classic White Linen Shirt`), category (`Tops`), color (`White`), and style (`Minimal`).
- Choose an image from your computer (PNG, JPG, JPEG, or WebP under 5MB).
- Observe the live preview before submitting.
- Click **"+ Add to Wardrobe"**. The card will immediately display with your real uploaded photo!
- Try the live search bar and category filters to quickly find items.
- Click **"✏️ Edit"** on any item to modify details or replace its photo in the popup modal.
- Click **"🗑️ Delete"** to delete an item; a confirmation prompt will appear, and the file will be removed cleanly from disk.

### 3. Customize Your Profile & Photo
- Go to **"Profile"**.
- Click **"📷 Upload / Change Photo"** and select a photo of yourself. The photo is validated, uploaded, and saved to your account.
- Refresh the page or log out and back in: your profile photo persists!
- Fill in your preferred style (e.g., `Trendy`), favorite color (`Lavender`), fit preference, and occasion, and click **"Save Preferences"**.

### 4. Style Me (Outfit Recommendations)
- Click **"Style Me"** in the navigation bar (or use any occasion shortcut on the Dashboard, like 🎓 College or 🎉 Party).
- Select your occasion, vibe, and current weather.
- Click **"✨ Create My Look"**.
- On the **Result Page**, GRWM will display an outfit coordinated from your actual wardrobe pieces with image thumbnails, category breakdowns, and a helpful styling note explaining the pairing.
- Click **"💖 Save to Favorites"** to store the outfit in your saved collection.

### 5. View Favorites
- Go to **"Favorites"** to see your curated looks.
- You can review saved looks anytime or remove them with the **"🗑️ Remove"** button.

### 6. Virtual Try-On Studio (IDM-VTON)
- In your **Profile**, scroll down to the **IDM-VTON Virtual Try-On Studio**.
- **Personal Photo**: Use your saved profile photo or upload a fresh photo for this try-on session.
- **Clothing Piece**: Either choose an outfit/garment from your wardrobe or select **"Upload Clothing"** to upload an image and choose the clothing category (`Tops`, `Bottoms`, `Dresses`, `Outerwear`).
- Read and check the **User Consent** box.
- Click **"✨ Generate My Look"**.
- Watch the live loading indicator while IDM-VTON diffusion models process your photo and garment on Hugging Face ZeroGPU.
- View the generated realistic try-on image right on the same page.
- Click **"⬇️ Download Result"** to save the generated image to your computer.

---

## 🤖 IDM-VTON Virtual Try-On Architecture

GRWM uses **IDM-VTON** (*Improving Diffusion Models for Authentic Virtual Try-On in the Wild* — [yisol/IDM-VTON](https://github.com/yisol/IDM-VTON)):
1. **Genuinely Free & Non-Commercial**:
   - Zero required API keys, zero paid tiers, and zero credit cards.
   - Ideal for student, academic, and non-commercial portfolio projects.
   - Communicates directly with the official public Space `yisol/IDM-VTON` powered by Hugging Face ZeroGPU.
2. **Privacy & Security**:
   - Requires explicit user consent before processing images.
   - Temporary personal photos uploaded strictly for a try-on session are immediately removed from server storage once inference completes.
3. **Optional HF_TOKEN**:
   - If you have a free personal Hugging Face account and token, you can add it to `.env` (`HF_TOKEN=your_token_here`) for personal rate limit allocation, but it is **not** required.

---

## 🧪 Running the Automated Test Suite

GRWM includes a test suite covering authentication, session protection, database isolation, CRUD operations, image validation, recommendations, and persistence:

```powershell
python -m unittest tests/test_app.py -v
```

All 13 automated test cases will execute and verify the system end-to-end.

---

## ❓ Troubleshooting Common Issues

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Script execution is disabled` in PowerShell | PowerShell execution policy restriction | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `ModuleNotFoundError: No module named 'flask'` | Virtual environment not activated | Activate via `.\.venv\Scripts\Activate.ps1` and run `pip install -r requirements.txt` |
| `File too large (413 Request Entity Too Large)` | Image upload exceeds 5 MB | Compress the photo or upload an image smaller than 5 MB |
| `Port 5000 is already in use` | Another process is listening on port 5000 | Run on a different port: `python -c "from app import app; app.run(port=5001)"` |
| Database locked error | Multiple simultaneous locks on SQLite | SQLite handles concurrent reads automatically; restart the dev server if a connection was held open during debugging |

---

## 🌸 Congratulations!
Your **GRWM — Get Ready With Me** application is fully configured, tested, and ready to serve fashion looks! ✨
