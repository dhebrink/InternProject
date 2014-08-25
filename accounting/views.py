# You will probably need more methods from flask but this one is a good start.
from flask import render_template, request

# Import things from Flask that we need.
from accounting import app, db

# Import our models
from models import Contact, Invoice, Policy

# Routing for the server.
@app.route("/", methods=['GET', 'POST'])
def index():
    # You will need to serve something up here.
    policy_num = request.form['policy_number']
    date_cursor = request.form['date']
    policy = Policy.query.filter(policy_number = policy_num).one()
    invoices = Invoice.query.filter_by(policy_id = policy.id)\
                            .filter(Invoice.bill_date <= date_cursor)\
                            .all()
    payments = Payment.query.filter_by(policy_id = policy.id)\
                            .filter(Payment.transaction_date <= date_cursor)\
                            .all()
    return render_template('index.html', invoices = invoices, payments = payments)

@app.route("/search", methods=['GET','POST'])
def search():
    policy_num = request.form['policy_number']
    date_cursor = request.form['date']
    policy = Policy.query.filter(policy_number = policy_num).one()
    invoices = Invoice.query.filter_by(policy_id = policy.id)\
                            .filter(Invoice.bill_date <= date_cursor)\
                            .all()
    return redirect(url_for('index'))




