# You will probably need more methods from flask but this one is a good start.
from flask import render_template, request

# Import things from Flask that we need.
from accounting import app, db

# Import our models
from models import Contact, Invoice, Policy, Payment

from tools import PolicyAccounting

# Routing for the server.
@app.route("/", methods=['GET', 'POST'])
def index():
    # You will need to serve something up here.
    if request.method == 'POST':
        policy_num = request.form['policy_num']
        date_cursor = request.form['date']
        policy = Policy.query.filter(Policy.policy_number == policy_num).one()
        invoices = Invoice.query.filter_by(policy_id = policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .all()
        payments = Payment.query.filter_by(policy_id = policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .all()
        
        pa = PolicyAccounting(policy.id)
        amt = pa.return_account_balance(date_cursor)
        return render_template('index.html', policy_number=policy_num, date_posted=date_cursor, invoices=invoices, payments=payments, balance=amt)
    else:
        return render_template('index.html', invoices = [], payments = [])

