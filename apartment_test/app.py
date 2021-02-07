import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core import (
    convert_yearly_to_monthly_interest,
    calculate_mortgage_over_time,
    apply_interest_scalar,
    apply_interest_series,
    apply_inflation,
    calculate_rent_reinvestment
)

from viz import (
    plot_example,
    plot_installment,
    plot_total_amount_mortgage,
    plot_home_value,
    plot_interest_downpay_fgts,
    plot_rent_economy,
    plot_rent_installment_diff,
    plot_rent_installment_diff_reinvest,
    plot_total,
)

from interface import (
    display_header,
    display_basic_info_section,
    display_tutorial_section,
    display_mortage_section_basic_info,
    display_mortage_section_fgts_info,
    display_investments_section,
    display_rent_section,
    display_rent_reinvestment_option,
    display_final_results_section,
    display_conclusion
)

# constants #
FGTS_INTEREST = 3./100

# header #
display_header()

# basic info section #
total_amount, downpay_amount, downpay_fgts_amount, home_appreciation, inflation, time_horizon = display_basic_info_section()

# how to use the tool section #
display_tutorial_section()
plot_example()

# mortgage section #
mortgage_value, n_months, mort_interest = display_mortage_section_basic_info(total_amount, downpay_amount)
fgts_amount, fgts_frequency = display_mortage_section_fgts_info(downpay_amount, mortgage_value)

# calculating mortgage cash flow
mortgage_df = calculate_mortgage_over_time(
    mortgage_value,
    n_months,
    mort_interest,
    fgts_frequency,
    fgts_amount
)

# time horizon is at least the time of the mortgage
time_horizon = max(
    time_horizon,
    mortgage_df.shape[0]
)

# calculating home appreciation
home_value = apply_interest_scalar(
    total_amount, 
    home_appreciation,
    time_horizon,
    'home_value'
)

# joining everything into cash flow df
cash_flow = (
    pd.concat([mortgage_df, home_value], axis=1)
    .assign(downpayment=[downpay_amount] + [0]*(home_value.shape[0] - 1))
    .assign(mort_installment = lambda x: x.mort_installment.fillna(0))
    .assign(mort_amount_interest = lambda x: x.mort_amount_interest.fillna(0))
    .assign(mort_fgts_paid = lambda x: x.mort_fgts_paid.fillna(0))
    .fillna(method='ffill')
    .assign(estate = lambda x: x.home_value - x.mort_balance)
)

# show installments?
if st.checkbox('Mostrar valor das parcelas?'):
    plot_installment(cash_flow)

plot_total_amount_mortgage(cash_flow)
plot_home_value(cash_flow)

# passive income section #
invest_interest = display_investments_section()

downpay_interest = apply_interest_scalar(
     downpay_amount - downpay_fgts_amount, 
     invest_interest,
     cash_flow.shape[0],
     'downpay_interest'
)

downpay_fgts_interest = apply_interest_scalar(
     downpay_fgts_amount, 
     FGTS_INTEREST,
     cash_flow.shape[0],
     'downpay_fgts_interest'
)

fgts_amort_interest = (
    apply_interest_series(cash_flow['mort_fgts_paid'], FGTS_INTEREST) - 
    cash_flow['mort_fgts_paid'].cumsum()
)

downpay_and_amort_passive_income = (
    downpay_interest +
    downpay_fgts_interest +
    fgts_amort_interest - 
    downpay_amount
)

plot_interest_downpay_fgts(downpay_and_amort_passive_income)

# rent section #
rent_amount, rent_appreciation = display_rent_section()

# calculating rent appreciation
rent_over_time = apply_interest_scalar(
    rent_amount, 
    rent_appreciation,
    time_horizon,
    'rent'
)
 
plot_rent_economy(rent_over_time)

is_reinvestment = display_rent_reinvestment_option()

if is_reinvestment:
    rent_reinvestment_passive_income = calculate_rent_reinvestment(
        rent_over_time,
        cash_flow['mort_installment'],
        invest_interest
    )
    
    plot_rent_installment_diff_reinvest(rent_reinvestment_passive_income)

else:
    rent_reinvestment_passive_income = 0

# final results section #

# making final calculations
total = (
    rent_over_time.cumsum() +
    rent_reinvestment_passive_income +
    cash_flow['estate'] -
    downpay_and_amort_passive_income -
    cash_flow['mort_fgts_paid'].cumsum() -
    cash_flow['downpayment'].cumsum() -
    cash_flow['mort_installment'].cumsum()
)

use_inflation = display_final_results_section()

if use_inflation:
    total = apply_inflation(total, inflation)

plot_total(total)

display_conclusion(total)