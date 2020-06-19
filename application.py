import os
import requests

from myclasses import Review
from flask import Flask, session, render_template, request, redirect, url_for, jsonify, abort
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
app.config['JSON_SORT_KEYS'] = False
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

    return render_template("index.html")

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
                return redirect(url_for('index'))
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
             "username already exists", past = url_for('register'))

        # Inserts to table otherwise
        db.execute("INSERT INTO users(username, hash) VALUES (:username, :hash)",
        {"username": username, "hash": passhash})
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

    results = db.execute("SELECT * FROM books WHERE isbn = :isbn OR " + 
                        "title LIKE :title OR author LIKE :author OR year = :year",
                        {"isbn": request.form.get("isbn"), "title": title, 
                        "author": author, "year": year }).fetchall()

    return render_template("results.html", results=results)

# Returns a page with all of the books
@app.route("/books")
def books():
    results = db.execute("SELECT * FROM books").fetchall()
    return render_template("results.html", results=results)

# Returns a page that includes the details of the selected book
@app.route("/books/<string:isbn>", methods=["POST", "GET"])
def book(isbn):

    # Refer to line 29
    if not 'user_id' in session:
        return redirect("/")

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": os.getenv("API_KEY"), "isbns": isbn})
    
    if request.method == "GET":
        result = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                            {"isbn": isbn}).fetchone()
        table = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn",
                            {"isbn": isbn}).fetchall()
        reviews = []
        reviewed = False
        for row in table:
            # Checks if the book's already reviewed by the user
            if int(session['user_id']) == int(row.user_id):
                reviewed = True

            name = db.execute("SELECT * FROM users WHERE id = :user_id",
                                {"user_id": row.user_id}).fetchone()
            print(int(row.score))
            review = Review(int(row.user_id), name.username,
                            int(isbn),  int(row.score), row.review)
            reviews.append(review)
            
        if result:
            return render_template("book.html", book = result, data=res.json(),
            reviews = reviews, user=session["user_id"], reviewed=reviewed)
        else:
            return render_template("error.html", message="Book didn't exist", 
            past=url_for('search'))

# Posts form input to the reviews table
@app.route("/post/<int:user_id>/<string:isbn>", methods=["POST"])
def post(user_id, isbn):

    # Refer to line 29
    if not 'user_id' in session:
        return redirect("/")

    try:
        score = int(request.form.get("review_score"))
    except:
        return render_template("error.html", message="Data Type input error", 
        past=url_for('books', isbn=isbn))

    if request.form.get("review") == '':
        text = None
    else:
        text = request.form.get("review")

    name = db.execute("SELECT * FROM users WHERE id = :user_id",
                        {"user_id": user_id}).fetchone()

    posted = Review(user_id, name.username, isbn, score, text)
    reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn",
                        {"isbn": isbn}).fetchall()

    reviewed = False

    # Checks if the book's already reviewed by the user
    for review in reviews:
        if review.user_id == posted.user_id:
            reviewed = True

    # If already reviewed, update the table
    if reviewed:
        db.execute("UPDATE reviews SET score = :score, review = :text " 
                    + "WHERE book_isbn = :isbn AND user_id = :user_id",
                    {'score': posted.user_score, 'text': posted.user_review, 'isbn': posted.book_isbn,
                    'user_id': posted.user_id})
        
    
    # If not insert into the table instead
    else:
        db.execute("INSERT INTO reviews (user_id, book_isbn, score, review) " +
                    "VALUES (:user_id, :isbn, :score, :review)",
                    {'user_id': posted.user_id, 'isbn': posted.book_isbn,
                    'score': posted.user_score, 'review': posted.user_review})
    
    # Commits and redirects to the book
    db.commit()
    return redirect(url_for('book', isbn=isbn))

@app.route("/api/<string:isbn>")
def api(isbn):
    book_data = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                           {'isbn': isbn}).fetchone()

    # Returns a 404 if book not found
    if not book_data:
        abort(404)

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": os.getenv("API_KEY"), "isbns": isbn})
    goodreads_data = res.json()
    goodreads_data = goodreads_data['books'][0]

    # Returns a JSON as response
    return jsonify({
        "title": book_data.title,
        "author": book_data.author,
        "year": book_data.year,
        "isbn": isbn,
        "review_count": int(goodreads_data['reviews_count']),
        "average_score": float(goodreads_data['average_rating'])
    })
