import os
import requests

from cs50 import SQL
from dotenv import load_dotenv
from flask import Flask, Response, redirect, render_template, request, session
from flask_session import Session
from openai import OpenAI
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('request_count', 'Number of HTTP requests')

# DeepSeek ai
load_dotenv()
url = "https://api.deepseek.com/v1/chat/completions"
client = OpenAI(
    api_key = os.getenv("DEEPSEEK_API_KEY"),
    base_url = url)
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {client.api_key}"
}


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# SQL
db_path = "WebGenerate.db"
db_exists = os.path.exists(db_path)

db = SQL(f"sqlite:///{db_path}")

if not db_exists:
    # Create users table
    db.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL
    )
    """)

    # Create histories table
    db.execute("""
    CREATE TABLE histories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        pattern TEXT NOT NULL,
        input TEXT NOT NULL,
        result TEXT NOT NULL,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

PATTERNS = {
    "business_email": "Generate the following content in the format of business email:",
    "product_description": "Write the following content in the tone of a product introduction:",
    "summary": "Summarize the following content:",
    "work_report": "Generate the following content in the format of a work report:",
    "grammar_check": "Check the grammar of the following content and provide suggestions:",
}

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""

    # Prometheus request count
    try:
        REQUEST_COUNT.inc()
    except Exception:
        pass
    
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Index
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    requirement = request.form.get("requirement")
    pattern = request.form.get("pattern")

    if request.method == "POST":
        # Requirement NULL?
        if not requirement:
            return apology("must provide requirement", 400)

        # Is pattern NULL/INVALID?
        if not pattern:
            message = requirement
        elif pattern not in PATTERNS:
            return apology("invalid pattern", 400)
        else:
            message = f"{PATTERNS[pattern]}\n\n{requirement}"



        # Generate and post result in /generate
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            response = response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            return apology(f"API failed: {e}", 400)

        session["last_pattern"] = pattern
        session["last_requirement"] = requirement
        session["last_message"] = message
        session["last_response"] = response

        # Save history
        db.execute("INSERT INTO histories (user_id, pattern, input, result) VALUES (?, ?, ?, ?)",
                   session["user_id"], pattern, requirement, response)

        return render_template("generate.html", response=response)

    else:
        return render_template("index.html")

# Generate
@app.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    # Regenerate
    if request.method == "POST":

        pattern = session["last_pattern"]
        requirement = session["last_requirement"]
        message = session["last_message"]

        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            response = response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            return apology(f"API failed: {e}", 400)

        session["last_response"] = response
        # Save history
        db.execute("INSERT INTO histories (user_id, pattern, input, result) VALUES (?, ?, ?, ?)",
                   session["user_id"], pattern, requirement, response)

        return render_template("generate.html", response=response)

    else:
        response = session["last_response"]
        return render_template("generate.html", response = response)

# History
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    # Search
    if request.method == "POST":
        requirement = request.form.get("requirement")

        if not requirement:
            return apology("must provide keyword", 400)

        # Select in database
        requirement = f"%{requirement}%"
        results = db.execute("SELECT pattern, input, result, time FROM histories WHERE user_id = ? AND input LIKE ?",
                               session["user_id"], requirement)

        return render_template("result.html", results=results)

    histories = db.execute("SELECT pattern, input, result, time FROM histories WHERE user_id = ?",
                        session["user_id"])
    return render_template("history.html", histories=histories)

# Result
@app.route("/result")
@login_required
def result():
    return render_template("result.html")

# Log in
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# Log out
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        if not password:
            return apology("must provide password", 400)

        if not confirmation or confirmation != password:
            return apology("passwords don't match", 400)

        # Check if username already exists
        exist = db.execute("SELECT username FROM users WHERE username = ?", username)
        if len(exist) > 0:
            return apology("username exists", 400)

        # Add new user information
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                   username, generate_password_hash(password))

        # Auto log in
        user_id = db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = user_id[0]["id"]

        return redirect("/")

    else:
        return render_template("register.html")
    
@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)