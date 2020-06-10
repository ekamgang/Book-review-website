import os
from flask import Flask, session, render_template,request, jsonify
import requests
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not "postgres://lxudxptnziobze:9e365131439c1dc6d39e41d321c1165a67c904ad7a4606c088caf0634bd91e54@ec2-52-207-25-133.compute-1.amazonaws.com:5432/daqdr6tifnmvef":
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://lxudxptnziobze:9e365131439c1dc6d39e41d321c1165a67c904ad7a4606c088caf0634bd91e54@ec2-52-207-25-133.compute-1.amazonaws.com:5432/daqdr6tifnmvef")
db = scoped_session(sessionmaker(bind=engine))
#db.execute("CREATE TABLE user_info (id serial PRIMARY KEY,fname VARCHAR NOT NULL,lname VARCHAR NOT NULL, username VARCHAR UNIQUE, password VARCHAR NOT NULL) ") # execute this SQL command and return all of the results
sessionUname=""


@app.route("/")
def proj1RegistrationPage():
      return render_template("proj1RegistrationPage.html")

@app.route("/register", methods=["POST"])
def register():
    fname = request.form.get("fname")
    lname = request.form.get("lname")
    username = request.form.get("username")
    password = request.form.get("password")
    if db.execute("SELECT * FROM user_info WHERE username = :username", {"username": username}).rowcount != 0:
                return "This username is not available."
    db.execute("INSERT INTO user_info (fname, lname,username, password) VALUES (:fname, :lname,:username, :password)",{"fname": fname,"lname":lname,"username": username, "password": password})
    db.commit()
    return render_template("proj1LoginPage.html")

@app.route("/login", methods=["POST"])
def login():
        username = request.form.get("username")
        global sessionUname
        sessionUname=username
        print(sessionUname)
        password = request.form.get("password")
        if db.execute("SELECT * FROM user_info WHERE username = :username and password = :password", {"username": username, "password":password}).rowcount == 0:
            return render_template("noUser.html")
        return render_template("proj1BookSearchPage.html")


@app.route("/bookSearch", methods=["POST"])
def bookSearch():
        isbn = request.form.get("isbn")
        isbn= str(isbn)
        author = request.form.get("author")
        title = request.form.get("title")
        books=db.execute("SELECT id, isbn,Author, Title, year FROM book_info WHERE isbn = :isbn or Author = :Author or Title =:Title", {"isbn": isbn, "Author":author, "Title":title}).fetchall()
        if len(books)==0:
                    books=db.execute("SELECT * FROM book_info WHERE isbn LIKE :isbn or Author LIKE :Author or Title LIKE :Title", {"isbn": isbn, "Author":author, "Title":title}).fetchall()
                    if len(books)==0:
                        return "no such book. Please try again"
        return render_template("proj1BookSearchPage.html", books=books)

@app.route("/bookSearch/<int:book_id>")
def books(book_id):
    Book = db.execute("SELECT * FROM book_info WHERE id = :id", {"id": book_id}).fetchone()
    review = db.execute("SELECT * FROM reviews WHERE book_id = :id", {"id": book_id}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "Wblwf1OVPpYyCk3r9R0Aw", "isbns": Book.isbn})
    data = res.json()
    ratingCount=data["books"][0]["work_ratings_count"]
    ratingAvg=data["books"][0]["average_rating"]
    return render_template("book.html", Book=Book,ratingAvg=ratingAvg,ratingCount=ratingCount, review=review)


@app.route("/reviewSubmission/<int:book_id>", methods= ["POST"])
def reviewSubmission(book_id):
    scale=request.form.get("scale")
    scale=int(scale)
    text=request.form.get("text_review")
    global sessionUname
    if db.execute("SELECT * FROM reviews WHERE user_name = :username and book_id=:book_id", {"username": sessionUname, "book_id":book_id}).rowcount != 0:
        return "You cannot submit two reviews for the same book"
    db.execute("INSERT INTO reviews(scale, text, book_id, user_name) VALUES(:scale, :text, :book_id, :user_name)",{"scale": scale,"text":text,"book_id": book_id, "user_name": sessionUname})
    db.commit()
    print(sessionUname)
    return render_template("success.html")


@app.route("/api/<isbn>")
def book_api(isbn):
    """Return details about a single book."""
    Book = db.execute("SELECT * FROM book_info WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if Book is None:
          return jsonify({"error": "Invalid isbn"}), 422

      # Get all passengers.
    ID=Book.id
    #fix getting count and avg
    reviewCount=db.execute("SELECT COUNT (book_id) FROM reviews WHERE book_id=:ID", {"ID": ID}).fetchone()
    reviewCount=reviewCount[0]
    print(reviewCount)
    reviewAvg=db.execute("SELECT AVG (scale) FROM reviews WHERE book_id=:ID", {"ID": ID}).fetchone()
    reviewAvg=reviewAvg[0]
    reviewAvg=round(reviewAvg, 2)
    reviewAvg=str(reviewAvg)
    print(reviewAvg)
    return jsonify({
              "title": Book.title,
              "author": Book.author,
              "year": Book.year,
              "isbn": Book.isbn,
              "review_count": reviewCount,
              "average_score":reviewAvg
     })





    #logout, LIKE matching search
