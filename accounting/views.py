# You will probably need more methods from flask but this one is a good start.
import sqlite3
from flask import render_template
from flask import g

# Import things from Flask that we need.
from accounting import app, db

# Import our models
from models import Contact, Invoice, Policy

# P10: Trying to connect to the database
DATABASE = 'accounting.sqlite'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Routing for the server.
@app.route("/")
def index():
    cur = get_db().cursor()
    return render_template('index.html')

# P10: Trying to write a query for the database
db.row_factory = sqlite3.Row

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


