from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mysecret")

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL")

client = MongoClient(MONGO_URL)
db = client["student_app"]
users = db["users"]


@app.route('/')
def index():
    return redirect('/login')


# ---------------- REGISTER ----------------
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if users.find_one({"email": email}):
            return "Email already registered!"

        users.insert_one({
            "name": name,
            "email": email,
            "password": password
        })

        return redirect('/login')

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users.find_one({"email": email, "password": password})

        if user:
            session["user_id"] = user["_id"]
            return redirect('/dashboard')     # ⭐ redirect to dashboard

        return "Invalid Credentials!"

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect('/login')

    user = users.find_one({"_id": ObjectId(session["user_id"])})
    name = user["name"]

    # Sample Courses
    courses = [
        {"code": "CSE101", "title": "Introduction to Computer Science", "instructor": "Dr. Smith",
         "credits": 3, "schedule": "Mon/Wed 10:00–11:30"},
        {"code": "MAT102", "title": "Calculus I", "instructor": "Prof. Johnson",
         "credits": 4, "schedule": "Tue/Thu 9:00–10:30"},
        {"code": "PHY103", "title": "Physics I", "instructor": "Dr. Williams",
         "credits": 3, "schedule": "Mon/Wed 14:00–15:30"}
    ]

    return render_template("dashboard.html", name=name, courses=courses)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
