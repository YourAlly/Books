import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    with open("books.csv") as file:
        books = csv.reader(file)
        start = True
        for isbn, title, author, year in books:
            print(isbn)
            if not start:
                db.execute("INSERT INTO books(isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                {"isbn":isbn, "title":title, "author":author, "year": int(year) })
            else:
                start = False

        db.commit()
        print("DONE!")


if __name__ == '__main__':
    main()