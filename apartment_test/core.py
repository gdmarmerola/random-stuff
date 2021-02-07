import numpy as np
import pandas as pd
from copy import deepcopy


def convert_yearly_to_monthly_interest(yearly_interest):
    
    """
    Convert yearly interest to monthly interest.
    """
    
    monthly_interest = np.power((1 + yearly_interest), 1/12) - 1
    return monthly_interest

def build_fgts_cash_flow(fgts_amount, fgts_frequency, n_months):
    """
    Build a dict representing times and amounts ({month: amount}) where fgts will be used.
    """
    fgts_payments = {}

    for i in range(1, n_months + 1):

        if i % (fgts_frequency * 12) == 0:
            fgts_payments[i] = fgts_amount
        else:
            fgts_payments[i] = 0

    return fgts_payments

def calculate_mortgage_over_time(principal, n_months, yearly_interest, fgts_frequency=0, fgts_amount=0):

    """
    Computes mortage over time. Allows using FGTS amount at fixed periods.

    Args:
        principal (float): total amount of mortgage 
        n_months (float): number of months of mortgage
        yearly_interest (float): yearly interest of mortgage
        fgts_frequency (int): frequency in years that FGTS will be used
        fgts_amount (float): amount at each time FGTS is used

    Returns:

        mortgage_df (pd.DataFrame): DataFrame containg mortgage expected cash flow
    """
    
    monthly_amortization = principal/n_months
    monthly_interest = yearly_interest/12
    
    balance = [deepcopy(principal)]
    amount_paid = [0]
    amount_interest = [balance[0] * monthly_interest]
    installment = [amount_interest[0] + monthly_amortization]
    fgts_paid = [0]

    fgts_payments = build_fgts_cash_flow(fgts_amount, fgts_frequency, n_months)

    for i in range(1, n_months + 1):
        
        current_balance = balance[-1] - monthly_amortization - fgts_payments[i]
        current_paid = amount_paid[-1] + monthly_amortization + fgts_payments[i]
        current_interest = balance[-1] * monthly_interest
        current_installment = current_interest + monthly_amortization

        balance.append(current_balance)
        amount_paid.append(current_paid)
        amount_interest.append(current_interest)
        installment.append(current_installment)
        fgts_paid.append(fgts_payments[i])

        if current_balance < 0:
            break

    mortgage_df = pd.DataFrame(
        {'mort_balance': balance, 
         'mort_amount_paid': amount_paid, 
         'mort_amount_interest': amount_interest,
         'mort_installment': installment,
         'mort_fgts_paid': fgts_paid}
    )
    
    return mortgage_df

def apply_interest_series(x, yearly_interest):

    """
    Apply interest dynamically to a series.
    """

    monthly_interest = convert_yearly_to_monthly_interest(yearly_interest)
    series = pd.Series(np.zeros(len(x)))

    for i, value in x.iteritems():

        powers = np.clip(x.index - i + 1, 0, None)
        multipliers = np.clip(powers, 0, 1)
        temp_series = value * multipliers * (1 + monthly_interest) ** powers
        series = series + temp_series
    
    return series

def apply_interest_scalar(amount, yearly_interest, n_months, name):

    """
    Apply interest to a fixed amount of money at t=0.
    """

    amount_over_time = pd.Series([amount] + [0] * (n_months - 1))

    amount_over_time = apply_interest_series(amount_over_time, yearly_interest)
    amount_over_time.name = name

    return amount_over_time

def apply_inflation(series, inflation):

    """
    Apply inflation to series.
    """
        
    inflation_series = apply_interest_scalar(1, inflation, series.shape[0], 'inflation_series')
    return series / inflation_series

def calculate_rent_reinvestment(rent_over_time, installments_over_time, interest):
    
    """
    Calculate passive income (opportunity cost) by reinvesting rent or installment surplus. 
    """

    diff = rent_over_time - installments_over_time

    rent_surplus = diff.clip(0, None)
    installment_surplus = diff.clip(None, 0)

    rent_passive_income = apply_interest_series(rent_surplus, interest) - rent_surplus.cumsum()
    installment_passive_income = apply_interest_series(installment_surplus, interest) - installment_surplus.cumsum()
    
    final_passive_income = (rent_passive_income + installment_passive_income).round(0)

    return final_passive_income
        