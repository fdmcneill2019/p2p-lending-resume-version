import re
from datetime import datetime, date
import utils

from src.insurance_terms import Insurance
from src.repayment_balance import RepaymentBalance


class LoanTerms:
    def __init__(self, title, borrower):
        normalized_title = title
        req_amount, repay_amounts, repay_dates, location, payment_methods \
            = LoanTerms.parse_text(normalized_title)
        self.loan_id: str
        self.submission_id: str
        self.lender = None
        self.borrower = borrower
        self.late_fee: float = 0.0
        self.loan_amount: float = req_amount[0]
        self.total_balance: float = 0.0
        self.repayment_balances = []  # A list of repayment balance objects
        self.unpaid_repayment_balances = []
        self.currency_code: str = 'USD'  # Default value
        self.repayment_amounts = repay_amounts  # Total amount of loan amount + interest
        self.insurance = None
        self.is_defaulted: bool = False
        self.is_repaid: bool = False
        self.fund_date: datetime.date = None
        self.due_dates: list = repay_dates
        self.payments: list = []  # List of repayment transactions
        self.was_charged_late_fee: bool = False
        self.sticky_state_cmt = None  # Reference to the sticky comment of the submission

        self.set_repayment_balances(repay_amounts, repay_dates)  # Need to create a dictionary with dates as
        # keys and their balance

    def get_id(self):
        return self.loan_id

    def set_id(self, loan_id: str):
        self.loan_id = loan_id

    def get_lender(self):
        return self.lender

    def set_lender(self, lender):
        self.lender = lender

    def get_borrower(self):
        return self.borrower

    def set_borrower(self, borrower):
        self.borrower = borrower

    def get_late_fee(self) -> float:
        return self.late_fee

    def set_late_fee(self, late_fee: float):
        self.late_fee = late_fee

    def impose_late_fee_penalty(self):
        if not self.was_charged_late_fee:  # This should only be done once in the lifetime of the loan
            self.total_balance = self.total_balance + self.late_fee
            for repay_bal in self.unpaid_repayment_balances:
                repay_bal.charge_late_fee(self.late_fee)

    def get_loan_amount(self) -> float:
        return self.loan_amount

    def set_loan_amount(self, loan_amount: float):
        self.loan_amount = loan_amount

    def get_total_balance(self) -> float:
        return self.total_balance

    def set_total_balance(self):
        total_balance = 0.0
        for balance in self.repayment_balances:
            total_balance = total_balance + balance.get_remaining_balance()  # balance is a tuple of str?
        self.total_balance = total_balance

    # Takes a list of tuples for repay amounts and
    # a list of date objects for repay dates
    def set_repayment_balances(self, repay_amounts, repay_dates):
        # Create a repayment balance object for each pair of amounts and dates
        for i in range(len(repay_dates)):
            new_repayment_balance = RepaymentBalance(repay_amounts[i][0], repay_dates[i])
            self.repayment_balances.append(new_repayment_balance)

        # To ensure that the repayment balances are in the correct chronological order,
        # we sort them by their dates and create a sorted list
        sorted_balances = sorted(self.repayment_balances,
                                 key=lambda repayment_balance: repayment_balance.get_due_date())
        self.unpaid_repayment_balances = sorted_balances
        # self.repayment_balances.update({f'{repay_dates[i]}': float(repay_amounts[i][0])})  # date needs to be
        # converted

    def get_repayment_balance(self, index):
        return self.repayment_balances[index].get_remaining_balance()

    def get_repayment_balances(self) -> list:
        return self.repayment_balances

    def get_currency_code(self):
        return self.currency_code

    def set_currency_code(self, currency_code):
        self.currency_code = currency_code

    # Get the amount to pay back in interest
    def get_repayment_amount(self, index):
        return self.repayment_amounts[index][0]

    # Sets the amount to payback in interest
    def set_repayment_amounts(self, repayment_amounts):
        self.repayment_amounts = repayment_amounts

    # Subtracts from the total balance and
    # earliest remaining repayment balance
    def make_payment(self, repayment):
        pay_record = repayment
        self.total_balance = self.total_balance - repayment

        leftover_amount = True
        i = 0
        while leftover_amount:
            earliest_unpaid_bal = self.unpaid_repayment_balances[i]
            if earliest_unpaid_bal:
                repayment = earliest_unpaid_bal.subtract_from_remaining_balance(repayment)  # Any repayment > 0
                # is left over amount
                if repayment == 0.0:
                    leftover_amount = False
                else:
                    i += 1

        
        # Get the current date and time
        current_datetime = datetime.now()
       
        # Record transaction date and amount
        trans_date = current_datetime.strftime("%A, %B %d, %Y")
        self.payments.append({'Date': trans_date, 'Amount': pay_record})

    def get_insurance(self) -> Insurance:
        return self.insurance

    def set_insurance(self, insurance):
        self.insurance = insurance

    def is_insured(self) -> bool:
        if self.insurance is None:
            return False
        else:
            return True

    def is_defaulted(self) -> bool:
        return self.is_defaulted

    def mark_as_defaulted(self):
        self.is_defaulted = True

    def is_repaid(self) -> bool:
        return self.is_repaid

    def mark_as_repaid(self):
        self.is_repaid = True

    def get_fund_date(self) -> date:
        return self.fund_date

    def set_fund_date(self, fund_date):
        self.fund_date = fund_date

    def get_due_date(self, index):
        return self.due_dates[index]

    def get_due_dates(self) -> list:
        return self.due_dates

    def set_due_dates(self, due_dates):
        self.due_dates = due_dates

    def confirm_terms(self):
        self.set_total_balance()
        self.set_fund_date(datetime.now().date())

    # Change code so no longer static and it initializes this object within the method itself
    @staticmethod
    def parse_text(text):
        # Regular expressions for currency amounts, dates, location, and payment methods
        currency_pattern = r'\s*\(?(\d+(?:\.\d+)?)\s*([A-Za-z]{3})'
        date_pattern = (r'(Jan(?:uary)|Feb(?:ruary)|Mar(?:ch)|Apr(?:il)|May|Jun(?:e)|Jul(?:y)|Aug(?:ust)|Sep(?:tember)'
                        r'|Oct(?:ober)|Nov(?:ember)|Dec(?:ember)?)\s*(\d{1,2},)\s*(\d{4})')
        location_pattern = r'#([A-Za-z0-9\s,]+)'
        payment_method_pattern = r'([A-Za-z0-9\s,]+)\)$'

        currency_matches = re.findall(currency_pattern, text, re.IGNORECASE)
        date_matches = re.findall(date_pattern, text, re.IGNORECASE)
        location_matches = re.findall(location_pattern, text, re.IGNORECASE)
        payment_method_match = re.search(payment_method_pattern, text, re.IGNORECASE)

        # Extracting REQ and Repay amounts
        req_amount, repay_amounts = None, []
        for match in currency_matches:
            if match[0].lower() == '[req]':
                req_amount = (match[1], match[2])
            elif match[0].lower() == 'repay':  # need to check for month
                repay_amounts.append((match[1], match[2]))

        # Extracting repayment dates
        repay_dates = []
        for match in date_matches:
            if (match[0].lower() ==
                    'jan' or 'january'
                    or 'feb' or 'february'
                    or 'mar' or 'march'
                    or 'apr' or 'april'
                    or 'may'
                    or 'jun' or 'june'
                    or 'jul' or 'july'
                    or 'aug' or 'august'
                    or 'sep' or 'september'
                    or 'oct' or 'october'
                    or 'nov' or 'november'
                    or 'dec' or 'december'):
                repay_date_str = ' '.join(match[0:])
                try:
                    repay_dates.append(datetime.strptime(repay_date_str, '%B %d, %Y').date())
                except ValueError:
                    repay_dates.append(datetime.strptime(repay_date_str, '%b %d, %Y').date())

        # Extracting location
        location = location_matches[0] if location_matches else None

        # Extracting payment methods
        payment_methods = [method.strip() for method in
                           payment_method_match.group(1).split(',')] if payment_method_match else None

        return req_amount, repay_amounts, repay_dates, location, payment_methods

    def convert_to_json(self) -> dict:
        return {
            "id": self.loan_id,
            "submissionId": self.submission_id,
            "lender": self.lender,
            "borrower": self.borrower,
            "lateFee": self.late_fee,
            "loanAmount": self.loan_amount,
            "balance": self.balance,
            "currencyCode": self.currency_code,
            "repaymentAmount": self.repayment_amount,
            "insurance": self.insurance,
            "isDefaulted": self.is_defaulted,
            "isRepaid": self.is_repaid,
            "fundDate": self.fund_date,
            "dueDate": self.due_date,
            "repaymentDate": self.repayment_date,
            "payments": self.payments
        }

    # Initialize loan terms from a json representation.
    def init_from_json(self, json):
        self.loan_id = json["id"]
        self.submission_id = json["submissionId"]
        self.lender = json["lender"]
        self.borrower = json["borrower"]
        self.late_fee = json["lateFee"]
        self.loan_amount = json["loanAmount"]
        self.balance = json["balance"]
        self.currency_code = json["currencyCode"]
        self.repayment_amount = json["repaymentAmount"]
        self.insurance = json["insurance"]
        self.is_defaulted = json["isDefaulted"]
        self.is_repaid = json["isRepaid"]
        self.fund_date = json["fundDate"]
        self.due_date = json["dueDate"]
        self.repayment_date = json["repaymentDate"]
        self.payments = []

    def to_string(self, reddit) -> str:
        return (f"The terms of this loan are as follows:"
                f"Lender: {utils.get_redditor(reddit, self.lender.get_id())}"  # Find the Redditor with the id
                f"Borrower: {utils.get_redditor(reddit, self.borrower.get_id())}"
                f"Late fee: {self.late_fee}"
                f"Loan amount: {self.loan_amount}"
                f"Balance: {self.balance}"
                f"Currency: {self.currency_code}"
                f"Repayment amount: {self.repayment_amount}"
                f"Insured: {self.is_insured()}"
                f"Repaid: {self.is_repaid}"
                f"Fund date: {self.fund_date}"
                f"Due date: {self.due_date}"
                f"Repayment date: {self.repayment_date}")
