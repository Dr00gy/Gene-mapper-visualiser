import psycopg2
import sys

def connect_to_database():
    try:
        connection = psycopg2.connect(
            user="kokos",
            password="kokos",
            host="127.0.0.1",
            port="5432",
            database="based"
        )
        cursor = connection.cursor()
        print("Connected to PostgreSQL")
        return connection, cursor
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        sys.exit(1)
