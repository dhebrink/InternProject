# You will probably need more methods from flask but this one is a good start.
from flask import render_template, request

# Import things from Flask that we need.
from accounting import app, db

from datetime import datetime, date

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
                                .filter(Invoice.deleted == False)\
                                .all()
        payments = Payment.query.filter_by(policy_id = policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .all()
        
        pa = PolicyAccounting(policy.id)
        amt = pa.return_account_balance(date_cursor)
        return render_template('index.html', policy_number=policy_num, date_posted=date_cursor, invoices=invoices, payments=payments, balance=amt)
    else:
        return render_template('index.html', invoices = [], payments = [])

@app.route("/policies", methods=['GET'])
def get_policies():
    policies = Policy.query.all()
    return render_template('policies.html', policies = policies)

@app.route("/getinvoices/<p_id>", methods=['GET'])
def get_invoices(p_id):
    invoices = Invoice.query.filter_by(policy_id = p_id).all()
    payments = Payment.query.filter_by(policy_id = p_id).all()
    pa = PolicyAccounting(p_id)
    date_cursor = invoices[len(invoices)-1].cancel_date
    amt = pa.return_account_balance(date_cursor)
    return render_template('index.html', invoices=invoices, payments=payments, balance=amt)

'''
@app.route("/makepayment", methods=['GET', 'POST'])
def make_payment():
    if request.method == 'GET':
        return render_template('payment.html')
    else:
        p_num = request.form['policy_num']
        amt = request.form['amount']
        try:
            policy = Policy.query.filter(Policy.policy_number == p_num).one()
            pa = PolicyAccounting(policy.id)
            pa.make_payment(amount=amt)
            return redirect(url_for('getinvoices', p_id=policy.id))
        except:
            return render_template('payment.html', policy_num=p_num, amount=amt)
'''

@app.route("/newpolicy", methods=['GET', 'POST'])
def make_policy():
    schedules = ["Annual", "Two-Pay", "Quarterly", "Monthly"]
    i_contacts = Contact.query.filter(Contact.role == "Named Insured").all()
    a_contacts = Contact.query.filter(Contact.role == "Agent").all()

    if request.method == "POST":
        #try:
        p_num = request.form['policy_num']
        eff_date = request.form['date']
        bill_schedule = request.form['bill_schedule']
        premium = request.form['premium']
        policy = Policy(p_num, eff_date, premium)

        policy.billing_schedule = bill_schedule

        insured = request.form['insured']
        if insured > 0: # If a 'Named Insured' was selected, tie to policy
            policy.named_insured = insured
        
        agent = request.form['agent']
        policy.agent = agent

        db.session.add(policy)
        db.session.commit()

        # make PolicyAccounting object to initialize invoices
        pa = PolicyAccounting(policy.id)

        return redirect(url_for('getinvoices', p_id=policy.id))

#        except:
#           return render_template('create.html', schedules=schedules, insured_list=i_contacts, agent_list=a_contacts)

    else:
        return render_template('create.html', schedules=schedules, insured_list=i_contacts, agent_list=a_contacts)








