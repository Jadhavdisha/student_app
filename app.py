from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import os

app = Flask(__name__)

# Secret key for sessions
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# ------------------ MongoDB Connection ------------------
MONGO_URL = os.environ.get("MONGO_URL")

client = MongoClient(MONGO_URL)
db = client["studentdb"]         # database
users = db["users"]              # collection


# ------------------ ROUTES ------------------

@app.route("/")
def home():
    if "user_email" not in session:
        return redirect("/login")

    user = users.find_one({"email": session["user_email"]})
    return render_template("home.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"].lower()
        phone = request.form["phone"]
        password = request.form["password"]

        # Check if user exists
        if users.find_one({"email": email}):
            flash("Email already registered!", "danger")
            return redirect("/register")

        users.insert_one({
            "fullname": fullname,
            "email": email,
            "phone": phone,
            "password": password
        })

        flash("Registration successful! Please login.", "success")
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]

        user = users.find_one({"email": email, "password": password})

        if user:
            session["user_email"] = email
            flash("Login successful!", "success")
            return redirect("/")
        else:
            flash("Invalid email or password!", "danger")
            return redirect("/login")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
