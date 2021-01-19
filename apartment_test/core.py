import numpy as np
import pandas as pd
from copy import deepcopy


def calculate_monthly_interest(interest):
    return np.power((1 + interest), 1/12) - 1


def calculate_sac_table(amount, n_months, yearly_interest, fgts_frequency=0, fgts_amount=0):
    
    amortization = amount/n_months
    monthly_interest = yearly_interest/12
    
    balance = [deepcopy(amount)]
    amount_paid = [0]
    amount_interest = [balance[0] * monthly_interest]
    installment = [amount_interest[0] + amortization]
    add_pay = [0]

    additional_amortization = {}
    if fgts_amount > 0:
        for i in range(12*fgts_frequency, n_months, 12*fgts_frequency):
            additional_amortization[i] = fgts_amount

    for i in range(1, n_months + 1):
        
        if i in additional_amortization:
            additional_pay = additional_amortization[i]
        else:
            additional_pay = 0 

        current_balance = balance[-1] - amortization - additional_pay
        current_paid = amount_paid[-1] + amortization + additional_pay
        current_interest = balance[-1] * monthly_interest
        current_installment = current_interest + amortization

        balance.append(current_balance)
        amount_paid.append(current_paid)
        amount_interest.append(current_interest)
        installment.append(current_installment)
        add_pay.append(additional_pay)

        if current_balance < 0:
            break

    sac_df = pd.DataFrame(
        {'mort_balance': balance, 
         'mort_amount_paid': amount_paid, 
         'mort_amount_interest': amount_interest,
         'mort_installment': installment,
         'mort_add_pay': add_pay}
    )
    
    return sac_df

def apply_appreciation(amount, interest, n_months, name):

    monthly_interest = calculate_monthly_interest(interest)
    amount_over_time = [amount]

    for i in range(1, n_months + 1):

        current_amount = amount_over_time[-1] * (1 + monthly_interest)
        amount_over_time.append(current_amount)

    return pd.Series(amount_over_time, name=name)

class Liquidity:

    def __init__(self, initial_value):
        self.total_value = initial_value

    def add_value(self, value):
        self.total_value += value

    def subtract_value(self, value):
        self.total_value -= value

    def apply_interest(self, interest, n_months=1):
        self.total_value = self.total_value * (1 + interest) ** n_months

def run_npv(series, interest):
    return (
        series * 
        np.power(1 + interest, series.index)[::-1]
    )

def run_inflation(series, inflation):
    return (
        series * 
        np.power(1 - inflation, series.index)
    )

def run_interest(x, interest):

    series = pd.Series(np.zeros(len(x)))

    for i, value in x.iteritems():

        powers = np.clip(x.index - i + 1, 0, None)
        multipliers = np.clip(powers, 0, 1)
        temp_series = value * multipliers * (1 + interest) ** powers
        series = series + temp_series
    
    return series