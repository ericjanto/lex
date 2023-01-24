import os
import mysql.connector

from datetime import datetime
from dotenv import load_dotenv


class LexDB:
    def __init__(self) -> None:
        load_dotenv()
        config = {
            "user": os.getenv("USERNAME"),
            "password": os.getenv("PASSWORD"),
            "host": os.getenv("HOST"),
            "database": os.getenv("DATABASE"),
            "ssl_verify_identity": True,
            "ssl_ca": "/etc/ssl/cert.pem",
        }
        self.db = mysql.connector.connect(**config)

    def add_book(self, book_title: str, author: str, language: str) -> int:
        sql = "INSERT INTO books (title, author, language) VALUES (%s, %s, %s)"
        val = (book_title, author, language)

        mycursor = self.db.cursor()
        mycursor.execute(sql, val)
        self.db.commit()

    def add_context(
        self, context: str, token_id: str, inflected_token: str, book_id: str
    ):
        created_at = datetime.now()
        sql = "INSERT INTO context (created_at, context, token_id, inflected_token, book_id) VALUES (%s, %s, %s)"
        val = (created_at, context, token_id, inflected_token, book_id)

        mycursor = self.db.cursor()
        mycursor.execute(sql, val)
        self.db.commit()

    def add_token_if_new(self, token: str, tag: str) -> int:
        if not self.token_exists(token, tag):
            pass
        else:
            return -1

    def token_exists(self, token: str, tag: str) -> bool:
        # Check $token and $tag fields
        sql = "SELECT EXISTS(SELECT 1 FROM vocabulary WHERE token = %s AND tag = %s)"
        mycursor = self.db.cursor()
        mycursor.execute(sql, (token, tag))
        self.db.commit()


    def book_exists(self, book_title: str) -> bool:
        pass

    def shutdown(self) -> None:
        self.db.close()


if __name__ == "__main__":
    lexdb = LexDB()
    # lexdb.add_book('testbook', 'testtitle', 'en')
    print(lexdb.token_exists('testtoken', 'testtag'))
    lexdb.shutdown()
