# cs50wproject1
Project 1 - Books for Harvard CS50W

Video screencast demonstration: https://youtu.be/rHf5J9lrO3U

For this project I was instructed to create a basic book review website similar to goodReads. Once you reach the home screen, you are prompted to log in. From the login page you can login if you have a username or password or you can navigate to the registration page to create an account. The passwords are stored as encrypted text in the database and are not just plain text. After logging in, you are able to search books by isbn, title, or author. You can select the book you're searching for and view its previous reviews as well as it's average score pulled form goodReads' api. There is a button to create a new review which you can rate the book and leave a message. Once posted, your review will immediately appear on the book's page for people to see.

The site also has a basici api functionality as well. If you navigate to /api/<isbn> it will return a json response with information on the book from the requested isbn. 

The backend of the wbsite is all run through Flask and code is located inteh application.py file. This is where all the postgreSQL communication with the externally hosted database (hosted by Heroku) happens as well. All of the html files are located in the templates folder. base.html contains the main template for each page and then all of the other html files inherit the base code through flask's jinja2 integration. I used bootstrap for a lot of the CSS work but there is also custom CSS contained in the /static/styles directory. It is written as SASS in styles.scss and then rendered to CSS instyles.css
