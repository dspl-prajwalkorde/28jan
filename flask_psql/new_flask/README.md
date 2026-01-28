Book Management API

A simple Flask application to manage books with CRUD operations, server-side pagination, sorting, and filtering. Uses PostgreSQL as the database and SQLAlchemy as ORM.

Features

Create, Read, Update, Delete (CRUD) books

Data validations:

Required fields (title and author)

Whitespace-only strings disallowed

Duplicate prevention (same title + author)

Server-side pagination, sorting, and filtering

RESTful API design

Unit tests using Python unittest

Tech Stack

Python 3.x

Flask

Flask-SQLAlchemy

PostgreSQL

Optional: HTML + JS for front-end

Database Schema

Table: books

Column	Type	    Constraints
id	    int	        Primary Key, Auto Increment
title	varchar	    Not Null, Max 100 chars
author	varchar	    Not Null, Max 100 chars

Setup Instructions
1. Clone the repository
git clone <repository-url>
cd <repository-folder>

2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows

3. Install dependencies
pip install -r requirements.txt

Requirements include:

Flask
Flask-SQLAlchemy
psycopg2-binary (for PostgreSQL)

4. Configure Database

Create a PostgreSQL database:
CREATE DATABASE testdb;
Update app.py database URI (optional, uses env var DATABASE_URL):
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/testdb'

5. Run the Application

python app.py
Server will run at http://127.0.0.1:5000/

Endpoints:
Endpoint	Method	Description
/books	POST	Create a new book
/books	GET	Get all books
/books/<id>	GET	Get book by ID
/books/<id>	PUT	Update book
/books/<id>	DELETE	Delete book

6. Test the Application

Run unit tests:
CREATE DATABASE testdb_test;
python -m unittest discover -s tests -p "test_app.py"
Uses a separate test database: testdb_test

Covers:
Positive CRUD flows
Negative cases (duplicate, missing data, invalid IDs)
Whitespace validation