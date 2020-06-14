import os
import requests

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["POST","GET"])
def index():
    if request.method == "GET":
        return render_template("login.html", message=None)
    else:
        hashed = db.execute("SELECT * FROM users WHERE username = :username",
        {"username" : request.form.get("username")}).fetchone()
        if hashed == None:
            return render_template("login.html", message="Username not found")
        else:
            if check_password_hash(hashed.hash, request.form.get("password")):
                return render_template("login.html", message = "Success!")
            else:
                return render_template("login.html", message = "Error: Password didn't match")
        
@app.route("/Registration", methods=["POST","GET"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        passhash = generate_password_hash(request.form.get("password"))
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchall():
            return render_template("error.html", message = "username already exists", past = "/Registration")
     
        db.execute("INSERT INTO users(username, hash) VALUES (:username, :hash)",
        {"username" : username, "hash" : passhash})
        db.commit()
        return render_template("login.html", message = "Registered!")