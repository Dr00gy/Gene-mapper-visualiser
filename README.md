# Technologies
This project is a PyQT6 app that runs on postgreSQL. I developed it on Windows using PyCharm Community Edition and pgAdmin 4 (because my obsolete psycopg2 was gaslighting me in the terminal).

# Setup
See requirements.txt for dependencies.
The project is modularised and each file has the neccesary imports.
The database.py has the connections already figured out on localhost and the port 5432. Change it to your liking.

1. Start the postgres service / server (be it on your machine or Docker)
2. Navigate to the project directory where all files are on the same "level" (no need for a complicated file structure afterall)
3. Enter the neccesary commands and configure inside postgres (via commands or pgAdmin 4)
4. Run main.py

# Commands inside project directory
`python -m venv venv` <br /> <br />
`venv\Scripts\activate` <br /> <br />
`pip install psycopg2` <br /> <br />
`sql -U postgres`

Feel free to switch to pgAdmin 4 here, as I did.

# Commands inside postgres
`CREATE USER <username> WITH PASSWORD '<password>';` <br /> <br />
`CREATE DATABASE <database_name>;` <br /> <br />
`GRANT ALL PRIVILEGES ON DATABASE <database_name> TO <username>;`

Make sure to match the username, password and database_name to the config inside database.py and to the password you chose for postgres. The database was created in the public schema on my machine.

VARCHAR == character varying

# SQL query for creating the table (or create in pgAdmin 4)
```
CREATE TABLE genes (
    id SERIAL PRIMARY KEY,
    chromosome VARCHAR(255),
    region VARCHAR(255),
    gene_name VARCHAR(255),
    gene_text TEXT,
    methylation_prone BOOLEAN,
    radiation_prone BOOLEAN
);
```
