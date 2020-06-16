import os

from flask import Flask, session, render_template, redirect, url_for, request, abort, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt

import requests

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

@app.route("/")
def index():
    #goes home and clears user session variables if logout button pushed
    if(request.args.get("logout")):
            session["failedlogin"] = False
            session["loggedin"] = False
            session["user"] = None
            return redirect(url_for('index'))
    
    return render_template("index.html")

@app.route("/user/")
def user():
    return render_template("user.html")

@app.route("/login/", methods=["GET", "POST"])
def login():

    #login mechanics triggered when form login button pushed
    if(request.method =="POST"):
        #get username and password from form
        username = request.form.get("username")
        password = request.form.get("password")
        
        # query database for username
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).first()
        try:
            # if password is incorrect
            if sha256_crypt.verify(password, user.password) is True:
                session["loggedin"] = True
                session["user"] = username
                return redirect(url_for('index'))
            #if login is successful
            else:
                session["loggedin"] = False
                session["user"] = None
                return render_template("login.html", failedlogin=True)
        #if user does not exists
        except AttributeError:
            session["failedlogin"] = True
            session["loggedin"] = False
            session["user"] = None
            return render_template("login.html", failedlogin=True)


    return render_template("login.html", userexists=request.args.get("userexists"))

@app.route("/register/", methods=["GET", "POST"])
def register():
    
    #register mechanids triggered on form register button
    if(request.method == "POST"):
        
        #get form information
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        username = request.form.get("username")
        #encrypts entered password using sha256 encryption
        password = sha256_crypt.encrypt(request.form.get("password"))

        if(firstname == None or firstname == "" or lastname == None or lastname == "" or username == None or  username == ""):
            return redirect(url_for('register', unfilled=True))


        #checks for already existing user and redirects if needed
        if(db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount > 0):
            return redirect(url_for('login', userexists=True))
        
        #adds new user to database
        db.execute("INSERT INTO users (username, password, firstname, lastname) VALUES (:username, :password, :firstname, :lastname)",
            {"username":username, "password":password, "firstname":firstname, "lastname":lastname})
        db.commit()

        #logs in new user
        session["loggedin"] = True
        session["user"] = username

        #goes home
        return redirect(url_for('index'))

    return render_template("register.html", unfilled=request.args.get("unfilled"))

@app.route("/search/", methods=["GET", "POST"])
def search():

    #redirects to login page if user is not logged in 
    if session["loggedin"] is False:
       return redirect(url_for("login"))

    #gets GET request arguments for search query
    isbn=request.args.get("isbn")
    title=request.args.get("title")
    author=request.args.get("author")

    #queries databse depending on search tpe and renders page with results
    if isbn is not None:
        books = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn", {"isbn":f"%{isbn}%"}).fetchall()
        return render_template("search.html", books=books, results=True)

    if author is not None:
        books = db.execute("SELECT * FROM books WHERE author LIKE :author", {"author":f"%{author}%"}).fetchall()
        return render_template("search.html", books=books, results=True)

    if title is not None:
        books = db.execute("SELECT * FROM books WHERE title LIKE :title", {"title":f"%{title}%"}).fetchall()
        return render_template("search.html", books=books, results=True)
    

    return render_template("search.html")


#redirects to search if book path is entered without an isbn
@app.route("/book/")
def bookredir():

    #redirects to login page if user is not logged in 
    if session["loggedin"] is False:
       return redirect(url_for("login"))

    return redirect(url_for("search"))


@app.route("/book/<string:isbn>", methods=["GET"])
def book(isbn):

    #redirects to login page if user is not logged in 
    if session["loggedin"] is False:
       return redirect(url_for("login"))

    #get book info from db
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).first()

    #throw 404 error if isbn does not exist in the database
    if book is None:
       abort(404)

    #get rating info from goodreads
    grjson = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": 'gbjpeSJgvTVrtvncXhNzdg', 'isbns':[isbn]})
    grdata = grjson.json()

    #organize info into dictionary
    info = {
    'isbn':isbn,
    'title': book['title'],
    'author': book['author'],
    'year': book['year'],
    'grrate': grdata['books'][0]['average_rating'],
    'grnumbers': grdata['books'][0]['ratings_count']
    }

    #get reviews from database and build dict of reviews
    dbreviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    reviews = {}
    for review in dbreviews:
        #pull user who published review to get their username
        user = db.execute("SELECT * FROM users WHERE user_id = :user_id", {"user_id": review['user_id']}).first()
        reviews[f"{review['user_id']}"] = {
            'isbn': review['isbn'],
            'username': user['username'],
            'rating': review['rating'],
            'review': review['review'].replace("\'\'", "\'"),
        }

    return render_template("book.html", info=info, reviews=reviews, cantreview=request.args.get("cantreview"), reviewsuccess=request.args.get("reviewsuccess"))

@app.route("/newreview/<string:isbn>", methods=["GET", "POST"])
def newreview(isbn):

    #get title of the book
    book = db.execute("SELECT * FROM BOOKS WHERE isbn = :isbn", {"isbn": isbn}).first()
    if book is not None:
        title = book['title']
    else:
        abort(404)

    #get user_id of logged in user
    user_id = db.execute("SELECT user_id FROM users WHERE username = :username", {"username":session["user"]}).first()
    
    #check if user already has published a review and redirect to book page if so
    rdone = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND user_id = :user_id ", {"isbn": isbn, "user_id":user_id[0]}).first()
    if rdone:
        return redirect(url_for('book', isbn=isbn, cantreview=True))

    #get review info from form and publish review
    if(request.method == "POST"):
        rating = int(request.form.get("rating"))
        reviewtext = request.form.get("reviewtext")
        #fix single ' in review text to avoid sql upload issues
        reviewtext = reviewtext.replace("\'", "\'\'")

        db.execute("INSERT INTO reviews (isbn, user_id, rating, review) VALUES (:isbn, :user_id, :rating, :review)", {"isbn":str(isbn), "user_id":int(user_id[0]), "rating":int(rating), "review":str(reviewtext)})
        db.commit()
        
        return redirect(url_for('book', isbn=isbn, reviewsuccess=True))


    return render_template("newreview.html", isbn=isbn ,booktitle=title)

@app.route("/api/<isbn>")
def api(isbn):

    #make sure book exists and gets info
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).first()
    #return error if book does not exist
    if book is None:
        return jsonify({"error": "Invalid isbn"}), 404

    #get rating info from goodreads
    grjson = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": 'gbjpeSJgvTVrtvncXhNzdg', 'isbns':[isbn]})
    grdata = grjson.json()

    #get review count
    dbreviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    reviewcount = 0
    for review in dbreviews:
        reviewcount = reviewcount + 1
    print(reviewcount)



    #organize info into dictionary
    info = {
    'isbn':isbn,
    'title': book['title'],
    'author': book['author'],
    'year': book['year'],
    'average_score': grdata['books'][0]['average_rating'],
    'reviewcount': reviewcount
    }

    return jsonify({
        "title": info['title'],
        "author": info['author'],
        "year": int(info['year']),
        "isbn": info['isbn'],
        "review_count": int(info['reviewcount']),
        "average_score": float(info['average_score'])
    })
    


    



#404 error handler
@app.errorhandler(404)
def page_not_found(error):
   return render_template('404.html', title = '404'), 404


    