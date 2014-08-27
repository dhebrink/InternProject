#!/user/bin/env python2.7

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from accounting import db
from models import Contact, Invoice, Payment, Policy

"""
#######################################################
This is the base code for the intern project.

If you have any questions, please contact Amanda at:
    amanda@britecore.com
#######################################################
"""

class PolicyAccounting(object):
    """
     Each policy has its own instance of accounting.
    """
    def __init__(self, policy_id):
        """
        Initialize self.policy by querying with policy_id
        """
        self.policy = Policy.query.filter_by(id=policy_id).one()

        # make sure self.policy.invoices is populated
        if not self.policy.invoices:
            self.make_invoices()

    def return_account_balance(self, date_cursor=None):
        """
        Returns the balance due after all payments entered before or on the date given.
        (date is defaulted to the current date)
        """

        # If a date was not specified when calling the function,
        # set the date to the current date.
        if not date_cursor:
            date_cursor = datetime.now().date()

        # Get all invoices tied to self.policy that are due before or on the date specifed.
        # Results are ordered by ascending bill_date
        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        # Sum the total amount due from invoices
        due_now = 0
        for invoice in invoices:
            due_now += invoice.amount_due

        # Get all payments that have been made toward the policy by the specified date.
        payments = Payment.query.filter_by(policy_id=self.policy.id)\
                                .filter(Payment.transaction_date <= date_cursor)\
                                .all()
        # Subtract payments from invoice total
        for payment in payments:
            due_now -= payment.amount_paid

        return due_now

    def make_payment(self, contact_id=None, date_cursor=None, amount=0):
        """
        Enter a Payment record tied to self.policy.
        Date will default to current date, contact will try to default to self.policy.named_insured.
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        # If contact_id not passed into the function, assign to self.policy.named_insured
        if not contact_id:
            try:
                if self.policy.named_insured:
                    contact_id = self.policy.named_insured
                else:
                    contact_id = self.policy.agent
            except:
                # Payment should always be assigned to named_insured?
                # Not sure if contact should be agent, or return error message.
                
                #contact_id = self.policy.agent
                #return "No named_insured assigned to this policy. Cannot make payment."
                pass

        payment = Payment(self.policy.id,
                          contact_id,
                          amount,
                          date_cursor)
        db.session.add(payment)
        db.session.commit()

        return payment

    def evaluate_cancellation_pending_due_to_non_pay(self, date_cursor=None):
        """
         If this function returns true, an invoice
         on a policy has passed the due date without
         being paid in full. However, it has not necessarily
         made it to the cancel_date yet.
        """
        # default date_cursor to current date if one is not passed in
        if not date_cursor:
            date_cursor = datetime.now().date()

        # Get invoice tied to self.policy that is in cancellation range
        invoice = Invoice.query.filter_by(policy_id = self.policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .filter(Invoice.cancel_date > date_cursor)\
                                .order_by(Invoice.bill_date).one()

        # If the account balance is 0 as of the day before the cancel date,
        # the policy is not pending cancellation.
        if not self.return_account_balance(invoice.cancel_date - relativedelta(days=1)):
            return False
        else:
            return True

    def evaluate_cancel(self, date_cursor=None):
        """
        Finds all invoices that are tied to self.policy and whose cancel date is before the date given.
        Prints a message that states if the policy should be canceled.
        """
        # If no date given, default to current date.
        if not date_cursor:
            date_cursor = datetime.now().date()

        invoices = Invoice.query.filter_by(policy_id=self.policy.id)\
                                .filter(Invoice.cancel_date <= date_cursor)\
                                .order_by(Invoice.bill_date)\
                                .all()

        for invoice in invoices:
            if not self.return_account_balance(invoice.cancel_date):
                continue
            else:
                print "THIS POLICY SHOULD HAVE CANCELED"
                break
        else:
            print "THIS POLICY SHOULD NOT CANCEL"


    def make_invoices(self):
        """
        Populates self.policy.invoices based on the selected billing schedule.
        Should have 1 if Annual, 2 if 2-Pay, 4 if quarterly, and 12 if Monthly.
        """
        # Clear what may currently be in the list of invoices to make sure there are no duplicates.
        for invoice in self.policy.invoices:
            invoice.delete()

        billing_schedules = {'Annual': None, 'Semi-Annual': 3, 'Quarterly': 4, 'Monthly': 12}

        invoices = []
        # First record to declare the overall premium of the policy
        first_invoice = Invoice(self.policy.id,
                                self.policy.effective_date, #bill_date
                                self.policy.effective_date + relativedelta(months=1), #due
                                self.policy.effective_date + relativedelta(months=1, days=14), #cancel
                                self.policy.annual_premium)
        invoices.append(first_invoice)

        # If billing schedule is Annual, no other invoices are needed
        if self.policy.billing_schedule == "Annual":
            pass
        elif self.policy.billing_schedule == "Two-Pay":
            # Put value in a variable to save hash table look-ups
            frequency = billing_schedules.get(self.policy.billing_schedule)
            # Alter first invoice's amount to reflect a 6-month payment
            first_invoice.amount_due = first_invoice.amount_due / frequency
            for i in range(1, frequency):
                # number of months to add to the invoices' bill_date
                months_after_eff_date = i*6	# multiply by 6 for Two-Pay
                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)
                invoice = Invoice(self.policy.id,
                                  bill_date,    # bill date
                                  bill_date + relativedelta(months=1),   # due date
                                  bill_date + relativedelta(months=1, days=14),   # cancel date
                                  self.policy.annual_premium / frequency)    # amount due
                invoices.append(invoice)
        elif self.policy.billing_schedule == "Quarterly":
            # Put value into variable to save hash table look-ups
            frequency = billing_schedules.get(self.policy.billing_schedule)
            # Alter first invoice's amount due to reflect a 3-month payment
            first_invoice.amount_due = first_invoice.amount_due / frequency
            for i in range(1, frequency):
                # number of months to add to invoices' bill_date
                months_after_eff_date = i*3	# multiply by 3 for Quarterly
                bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)
                invoice = Invoice(self.policy.id,
                                  bill_date,   # bill date
                                  bill_date + relativedelta(months=1),   # due date
                                  bill_date + relativedelta(months=1, days=14),   # cancel date
                                  self.policy.annual_premium / frequency)   # amount due
                invoices.append(invoice)
        elif self.policy.billing_schedule == "Monthly":
            # put value into variable to save hash table look-ups
            frequency = billing_schedules.get(self.policy.billing_schedule)
            # Alter the first invoice's amount due to reflect a monthly payment
            first_invoice.amount_due = first_invoice.amount_due / frequency
            for i in range(1, frequency):
                months_after_eff_date = i	# no multiple here for Monthly. "frequency" should be 12
	        bill_date = self.policy.effective_date + relativedelta(months=months_after_eff_date)
	        invoice = Invoice(self.policy.id,
		                  bill_date,   # bill date
		                  bill_date + relativedelta(months=1),  # due date
                                  bill_date + relativedelta(months=1, days=14),   # cancel date
                                  self.policy.annual_premium / frequency)   # amount due
	        invoices.append(invoice)
        else:
            print "You have chosen a bad billing schedule."

        for invoice in invoices:
            db.session.add(invoice)
        db.session.commit()


    def change_billing_schedule(self, billing_schedule, date_cursor=None):
        """
        Use this method to change a policy's billing schedule.
        
        """
        if not date_cursor:
            date_cursor = datetime.now().date()

        invoices = Invoice.query.filter_by(policy_id = self.policy.id)\
                                .filter(Invoice.bill_date <= date_cursor)\
                                .order_by(Invoice.bill_date).all()
        for invoice in invoices:
            invoice.deleted = True

        new_invoices = []

        self.policy.billing_schedule = billing_schedule
        if billing_schedule == 'Annual':
            pass
        elif billing_schedule == 'Two-Pay':
            pass
        elif billing_schedule == 'Quarterly':
            pass
        elif billing_schedule == 'Monthly':
            pass
        else:
            print "You have entered an invalid billing schedule"
        


################################
# The functions below are for the db and 
# shouldn't need to be edited.
################################
def build_or_refresh_db():
    db.drop_all()
    db.create_all()
    insert_data()
    print "DB Ready!"

def insert_data():
    #Contacts
    contacts = []
    john_doe_agent = Contact('John Doe', 'Agent')
    contacts.append(john_doe_agent)
    john_doe_insured = Contact('John Doe', 'Named Insured')
    contacts.append(john_doe_insured)
    bob_smith = Contact('Bob Smith', 'Agent')
    contacts.append(bob_smith)
    anna_white = Contact('Anna White', 'Named Insured')
    contacts.append(anna_white)
    joe_lee = Contact('Joe Lee', 'Agent')
    contacts.append(joe_lee)
    ryan_bucket = Contact('Ryan Bucket', 'Named Insured')
    contacts.append(ryan_bucket)

    for contact in contacts:
        db.session.add(contact)
    db.session.commit()

    policies = []
    p1 = Policy('Policy One', date(2015, 1, 1), 365)
    p1.billing_schedule = 'Annual'
    p1.agent = bob_smith.id
    policies.append(p1)

    p2 = Policy('Policy Two', date(2015, 2, 1), 1600)
    p2.billing_schedule = 'Quarterly'
    p2.named_insured = anna_white.id
    p2.agent = joe_lee.id
    policies.append(p2)

    p3 = Policy('Policy Three', date(2015, 1, 1), 1200)
    p3.billing_schedule = 'Monthly'
    p3.named_insured = ryan_bucket.id
    p3.agent = john_doe_agent.id
    policies.append(p3)

    for policy in policies:
        db.session.add(policy)
    db.session.commit()

    for policy in policies:
        PolicyAccounting(policy.id)

    payment_for_p2 = Payment(p2.id, anna_white.id, 400, date(2015, 2, 1))
    db.session.add(payment_for_p2)
    db.session.commit()

