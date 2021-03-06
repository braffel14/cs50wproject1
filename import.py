import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from dotenv import load_dotenv
load_dotenv() #load environment variables

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

'''
Book class acts as a book object with isbn, title, author, and year variables that can then be uploaded to the database using the todb method
'''
class Book():
    
    def __init__(self, isbn, title, author, year):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.year = year

    def __repr__(self):
        return f'<Title: {self.title}, isbn: {self.isbn}, author: {self.author}, year: {self.year}>'

    #execute SQL command to upload book to db
    def todb(self):
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
            {"isbn": self.isbn, "title": self.title, "author":self.author, "year":self.year})  
        print(f"Added {self} to db") 


def main():
    b = open("books.csv")
    reader = csv.reader(b)
    next(reader)#skips column title line in csv file
    for isbn, title, author, year in reader: #loops through each line of csv file and creates book object and uploads it to db
        book = Book(isbn=isbn, title=title, author=author, year=year)
        book.todb()
    db.commit() #commit db changes after all books have been uploaded
    

if __name__ == "__main__":
    main()

    