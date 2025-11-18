# app.py (fixed)
from flask import Flask, render_template, request, redirect, session, flash
from pymongo import MongoClient, errors
from bson.objectid import ObjectId
import os
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mysecret")

# MongoDB connection (short timeout so worker doesn't hang)
MONGO_URL = os.getenv("MONGO_URL")
client = None
db = None
users = None

try:
    if not MONGO_URL:
        raise ValueError("MONGO_URL is not set in environment variables.")

    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    # Force a quick server selection to surface connection errors now
    client.admin.command("ping")
    db = client["student_app"]
    users = db["users"]
    logging.info("Connected to MongoDB Atlas successfully.")
except (errors.ServerSelectionTimeoutError, ValueError) as e:
    logging.error("Could not connect to MongoDB: %s", e)
    # users remains None; routes will handle the missing DB gracefully


@app.route('/')
def index():
    return redirect('/login')


# --------------- REGISTER ----------------
@app.route('/register', methods=["GET", "POST"])
def register():
    if users is None:
        flash("Database connection error. Try again later.", "danger")
        return render_template("register.html")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill all required fields.", "warning")
            return render_template("register.html")

        if users.find_one({"email": email}):
            flash("Email already registered. Please login.", "warning")
            return redirect('/login')

        new_user = {
            "name": name,
            "email": email,
            "password": password  # For production, hash passwords (bcrypt)
        }

        inserted = users.insert_one(new_user)
        flash("Account created. Please login.", "success")
        return redirect('/login')

    return render_template("register.html")


# --------------- LOGIN ----------------
@app.route('/login', methods=["GET", "POST"])
def login():
    if users is None:
        flash("Database connection error. Try again later.", "danger")
        return render_template("login.html")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter email and password.", "warning")
            return render_template("login.html")

        user = users.find_one({"email": email, "password": password})
        if user:
            # FIX: store the ObjectId as a string in session (JSON-serializable)
            session["user_id"] = str(user["_id"])
            session["user_email"] = user.get("email")
            flash("Logged in successfully.", "success")
            return redirect('/dashboard')

        flash("Invalid credentials.", "danger")
        return render_template("login.html")

    return render_template("login.html")


# --------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect('/login')

    if users is None:
        flash("Database connection error. Try again later.", "danger")
        return redirect('/login')

    try:
        # Convert the stored string id back to ObjectId for queries
        user = users.find_one({"_id": ObjectId(session["user_id"])})
    except Exception as e:
        logging.exception("Error loading user from DB: %s", e)
        flash("Session error. Please login again.", "danger")
        session.clear()
        return redirect('/login')

    if not user:
        flash("User not found. Please register.", "warning")
        session.clear()
        return redirect('/register')

    name = user.get("name", "Student")

    # Sample Courses to show on dashboard (replace with real data later)
    courses = [
        {"code": "CSE101", "title": "Introduction to Computer Science", "instructor": "Dr. Smith",
         "credits": 3, "schedule": "Mon/Wed 10:00–11:30"},
        {"code": "MAT102", "title": "Calculus I", "instructor": "Prof. Johnson",
         "credits": 4, "schedule": "Tue/Thu 09:00–10:30"},
        {"code": "PHY103", "title": "Physics I", "instructor": "Dr. Williams",
         "credits": 3, "schedule": "Mon/Wed 14:00–15:30"}
    ]

    return render_template("dashboard.html", name=name, courses=courses)


# --------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect('/login')


if __name__ == '__main__':
    # Only enable debug locally
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
