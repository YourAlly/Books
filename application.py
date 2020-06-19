import os
import requests

from myclasses import Review
from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Check for environment variables
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

if not os.getenv("API_KEY"):
    raise RuntimeError("API_KEY is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Index
@app.route("/")
def index():

    # Redirects to /login if the user's not logged in
    if not 'user_id' in session:
        return redirect("/login")

    return render_template("index.html", name = None)

# Checks if form input exists in the table
@app.route("/login", methods=["POST", "GET"])
def login():

    # Checks if it's a get request and treats it as post otherwise
    if request.method == "GET":
        return render_template("login.html", message=None)
    else:
        # Checks if the username exists
        hashed = db.execute("SELECT * FROM users WHERE username = :username",
                            {"username": request.form.get("username")}).fetchone()
        if hashed == None:
            return render_template("login.html", message="Username not found")
        else:
            # Checks if the password matches
            if check_password_hash(hashed.hash, request.form.get("password")):
                session["user_id"] = hashed.id
                return render_template("index.html", name=request.form.get("username"))
            else:
                return render_template("login.html", message="Error: Password didn't match")

# Adds a row to the users table
@app.route("/Registration", methods=["POST","GET"])
def register():

    # Refer to line 45
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        passhash = generate_password_hash(request.form.get("password"))

        # Checks if username already exists, and redirects to an error if it does
        if db.execute("SELECT * FROM users WHERE username = :username",
        {"username": username}).fetchall():
            return render_template("error.html", message =
             "username already exists", past = "/Registration")

        # Inserts to table otherwise
        db.execute("INSERT INTO users(username, hash) VALUES (:username, :hash)",
        {"username" : username, "hash" : passhash})
        db.commit()
        return render_template("login.html", message = "Registered!")

# Clears the session
@app.route("/logout")
def logout():

    # Refer to line 29
    if not 'user_id' in session:
        return redirect("/login")

    # Clears the session and redirects the user back to the homepage
    session.clear()

    return redirect("/")

# Returns either a rendered template of "search.html" and posts to /results
@app.route("/search")
def search():

    # Refer to line 29
    if not 'user_id' in session:
        return redirect("/")

    # Refer to line 45
    if request.method == "GET":
        return render_template("search.html")

# Returns a rendered template of results.html
@app.route("/results", methods=["POST", "GET"])
def results():
    if request.method == "GET":
        return redirect("/search")
    # Refer to line 29
    if not 'user_id' in session:
        return redirect("/")

    # Changes form values to None if input is equal to ''
    if request.form.get("title") == '':
        title = None
    else:
        title = "%" + request.form.get("title") + "%"

    if request.form.get("author") == '':
        author = None
    else:
        author = "%" + request.form.get("author") + "%"

    year = request.form.get("year")
    if year == '':
        year = None
    try:
        year = int(year)
    except:
        year = None

    results = db.execute("SELECT * FROM books WHERE " +
    "isbn = :isbn OR title LIKE :title OR author LIKE :author OR year = :year",
    {"isbn" : request.form.get("isbn"), "title": title,
    "author" : author, "year" : year }).fetchall()

    return render_template("results.html", results= results)

# Returns a page with all of the books
@app.route("/books")
def books():
    results = db.execute("SELECT * FROM books").fetchall()
    return render_template("results.html", results= results)

# Returns a page that includes the details of the selected book
@app.route("/books/<string:isbn>", methods=["POST", "GET"])
def book(isbn):
    result = db.execute("SELECT * FROM books WHERE isbn = :isbn",
    {"isbn" : isbn}).fetchone()
    table = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn",
    {"isbn" : isbn}).fetchall()
    reviews = []
    for row in table:
        name = db.execute("SELECT * FROM users WHERE id = :user_id",
        {"user_id" : row.user_id}).fetchone()
        print(int(row.score))
        review = Review(name.username, row.review, int(row.score))
        reviews.append(review)
    if result:
        return render_template("book.html", book = result, reviews = reviews)
    else:
        return render_template("error.html", message="Book didn't exist", past="index.html")
