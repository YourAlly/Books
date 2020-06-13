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
        check = db.execute("SELECT id FROM users WHERE username = :username AND hash = :password",
        {"username" : request.form.get("username"), "hash":request.form.get("password")})
        if check.id is not None:
            pass
        

@app.route("/Registration", methods=["POST","GET"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        check = db.execute("SELECT id FROM users WHERE username = :username",
        {"username":username}).fetchone
        if check is not None:
            return render_template("error.html", message="Username already Taken", past="'register'")
        else:
            passhash = generate_password_hash(request.form.get("password"))
            db.execute("INSERT INTO users(username, hash) VALUES (:username, :hash)",
            {"username" : username, "hash" : passhash})
            return render_template("login.html", message = "Registered!")
    
