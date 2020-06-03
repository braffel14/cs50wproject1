import os

from flask import Flask, session, render_template, redirect, url_for, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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

@app.route("/user")
def user():
    return render_template("user.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    #login mechanics triggered when form login button pushed
    if(request.method =="POST"):
        #get username and password from form
        username = request.form.get("username")
        password = request.form.get("password")
        
        # query database for username
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).first()
        try:
            #if password is incorrect
            if(user.password == password):
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

@app.route("/register", methods=["GET", "POST"])
def register():
    
    #register mechanids triggered on form register button
    if(request.method == "POST"):
        
        #get form information
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        username = request.form.get("username")
        password = request.form.get("password")

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

@app.route("/search", methods=["GET", "POST"])
def search():

    if session["loggedin"] is False:
       return redirect(url_for("login"))

    isbn=request.args.get("isbn")
    title=request.args.get("title")
    author=request.args.get("author")

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
