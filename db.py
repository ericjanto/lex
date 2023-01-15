import os
import mysql.connector

from dotenv import load_dotenv

load_dotenv()

config = {
    "user": os.getenv("USERNAME"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST"),
    "database": os.getenv("DATABASE"),
    "ssl_verify_identity": True,
    "ssl_ca": "/etc/ssl/cert.pem",
}


cnx = mysql.connector.connect(**config)
cnx.close()

print("Successfully connected to PlanetScale!")
