import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core import (
    calculate_monthly_interest,
    calculate_sac_table,
    apply_appreciation,
    Liquidity,
    run_npv,
    run_inflation,
    run_interest
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
    plot_total_inflation
)

### parameters ###

# constants
fgts_interest = 3./100
monthly_fgts_interest = calculate_monthly_interest(fgts_interest)

# title
st.title('Vale a pena comprar ou alugar?')
st.write('Vamos tentar responder a essa pergunta passo a passo tentando fazer um cálculo de fluxo de caixa.')

### basic info section ###

st.title('Informações básicas')
st.write('Vamos começar com informações básicas sobre o imóvel.')

total_amount = st.number_input(
    'Qual é o valor do imóvel que você vai comprar? (R$)',
    0.0,
    100e6,
    1000e3,
    step=10e3,
    format='%0f'    
)

downpay_amount = st.number_input(
    'Qual é o valor da entrada (se for pagar à vista use o valor total do imóvel)? (R$)',
    0.0,
    total_amount,
    200e3,
    step=10e3,
    format='%0f'    
)

home_appreciation = st.slider(
    'Quanto você espera que o imóvel valorize por ano? (%)',
    -10.0,
    10.0,
    2.0, 
    0.1,
)/100

inflation = st.slider(
    'Qual você espera que seja a inflação anual média no longo prazo? (%)',
    -10.0,
    10.0,
    2.0, 
    0.1,
)/100

monthly_inflation = calculate_monthly_interest(inflation)

time_horizon = st.slider(
    'Você quer projetar a simulação financeira para quantos anos no futuro?',
    0,
    40,
    30, 
    1,
) * 12

### how to use the tool section ###

st.title("Como usar essa ferramenta")
st.write("Vamos apresentar diversos gráficos tentando detalhar a dinâmica financeira entre comprar e alugar, " 
         "adotando a perspectiva de **comprar** um apartamento. ")
st.write("Dessa forma, nos gráficos seguintes, **valores positivos** representam "
         " que **comprar** é **vantajoso** em relação à **alugar**. "
         "Por outro lado, valores **negativos** representam que **alugar** é **mais vantajoso** em relação à **comprar**.")

plot_example()

### mortgage section ###

st.title("1. Financiamento")
st.markdown(
    """
    Vamos começar pelo financiamento. Aqui temos duas dinâmicas diferentes que você não teria no caso do aluguel:\n
    1. Todo mês você paga parcelas do financiamento (custo)\n
    2. Você constrói patrimônio na forma do imóvel, que valoriza no tempo (receita)\n
    O ponto (1) gera uma desvantagem financeira em relação ao aluguel e o ponto (2) gera uma vantagem. 
    O saldo será positivo se o apartamento tiver uma valorização acima dos juros do financiamento. 
    Assumimos que o financiamento seguirá a tabela SAC, onde a amortização é constante.
    """
)

mortgage_value = total_amount - downpay_amount
st.markdown(f"Você vai financiar um total de **{mortgage_value/1e3:.0f} mil reais.**")

n_months = st.slider(
    'Qual é o prazo do financiamento em meses?',
    60, 
    360, 
    360,
    3
)

mort_interest = st.slider(
    'Qual é o Custo Efetivo Total (CET) do financiamento?',
    5.0,
    12.0,
    7.3, 
    0.1,
) / 100

if st.checkbox('Vai usar o FGTS na entrada?'):

    downpay_fgts_amount = st.number_input(
        'Qual será o valor a ser amortizado via FGTS na entrada? (R$)',
        0.,
        downpay_amount,
        0.,
        1e3,
        format='%0f'
    )

else:
    downpay_fgts_amount = 0.  

if st.checkbox('Vai usar o FGTS para amortizar o saldo devedor?'):

    fgts_frequency = st.slider(
        'Em qual frequência você espera usar o FGTS para amortizar o seu saldo devedor? (a cada X anos)',
        0,
        10,
        2,
        2,format='%0f'
    )

    fgts_amount = st.number_input(
        'Quanto você espera conseguir amortizar do saldo devedor em cada ocasião que isso acontecer? (R$)',
        0.,
        mortgage_value,
        0.,
        1e3,
        format='%0f'
    )

else:
    fgts_amount = 0
    fgts_frequency = 2

# calculating sac table
sac_df = calculate_sac_table(
    total_amount - downpay_amount,
    n_months,
    mort_interest,
    fgts_frequency,
    fgts_amount
)

# time horizon is at least the time of the mortgage
time_horizon = max(
    time_horizon,
    sac_df.shape[0]
)

# calculating home appreciation
home_value = apply_appreciation(
    total_amount, 
    home_appreciation,
    time_horizon,
    'home_value'
)

# joining into cash flow df
cash_flow = (
    pd.concat([sac_df, home_value], axis=1)
    .assign(downpayment=[downpay_amount] + [0]*(home_value.shape[0]-1))
    .assign(mort_installment = lambda x: x.mort_installment.fillna(0))
    .assign(mort_amount_interest = lambda x: x.mort_amount_interest.fillna(0))
    .assign(mort_add_pay = lambda x: x.mort_add_pay.fillna(0))
    .fillna(method='ffill')
    .assign(buy_estate = lambda x: x.home_value - x.mort_balance)
    #.apply(lambda x: run_inflation(x, monthly_inflation))
)

if st.checkbox('Mostrar valor das parcelas?'):
    plot_installment(cash_flow)
plot_total_amount_mortgage(cash_flow)
plot_home_value(cash_flow)

### passive income section ###

st.title("2. Entrada, FGTS e investimentos")
st.markdown(
    """
    Outro fator importante que torna o investimento em imóveis **desvantajoso**
    em relação ao aluguel é **imobilizar recursos próprios e FGTS**, que poderiam estar
    gerando **renda passiva** caso não tivessem sido usados na compra do imóvel. 
    O FGTS rende a uma taxa de 3% ao ano. 
    """
)

invest_interest = st.slider(
    'Quanto você acha que os recursos próprios (sem FGTS) usados na entrada renderiam em média por ano se você não os investisse em um imóvel? (%)',
    0.0,
    30.0,
    10.0, 
    0.1,
) / 100 

monthly_invest_interest = calculate_monthly_interest(invest_interest)

downpay_interest = (
    (downpay_amount - downpay_fgts_amount) * 
    (1 + monthly_invest_interest) ** np.arange(cash_flow.shape[0])
    +
    (downpay_fgts_amount) * 
    (1 + monthly_fgts_interest) ** np.arange(cash_flow.shape[0])
    - downpay_amount
)

fgts_amort_interest = run_interest(cash_flow['mort_add_pay'], monthly_fgts_interest) - cash_flow['mort_add_pay'].cumsum()
downpay_and_amort_interest = downpay_interest + fgts_amort_interest

plot_interest_downpay_fgts(downpay_and_amort_interest)

### rent section ###

st.title("3. Aluguel")
st.markdown(
    """
    Por fim, um fator importante que torna o investimento em imóveis **vantajoso**
    em relação ao aluguel é **deixar de pagar aluguel**. A diferença entre o valor das parcelas
    e o aluguel também pode ser reinvestida. Dependendo das premissas, a economia do aluguel pode ser o 
    fator mais relevante da simulação.
    """
)

rent_amount = st.number_input(
    'Se você não comprasse um apartamento, quanto pagaria de aluguel hoje (em imóvel equivalente)? (R$ por mês)',
    0.,
    20e3,
    5000.,
    100.,
    format='%0f'
)

rent_appreciation = st.slider(
    'Quanto você espera que o preço do aluguel aumente em média por ano? (%)',
    0.0,
    15.0,
    2.0, 
    0.1,
) / 100

# calculating rent appreciation
rent_over_time = apply_appreciation(
    rent_amount, 
    rent_appreciation,
    time_horizon,
    'rent'
)
 
plot_rent_economy(rent_over_time)

diff = rent_over_time - cash_flow['mort_installment']
plot_rent_installment_diff(diff.cumsum())

if st.checkbox('Deseja simular o reinvestimento da diferença entre parcelas e aluguel? (usando mesma taxa de rendimento esperada para entrada e FGTS caso não tivessem sido usados)', True):
    
    positive_diff = diff.clip(0, None)
    negative_diff = diff.clip(None, 0)

    positive_diff_interest = run_interest(positive_diff, monthly_invest_interest)
    negative_diff_interest = run_interest(negative_diff, monthly_invest_interest)
    
    diff_interest = (positive_diff_interest + negative_diff_interest + diff.cumsum()).round(0)
    plot_rent_installment_diff_reinvest(diff_interest)
    rent_over_time = rent_over_time.cumsum() + diff_interest
else:
    rent_over_time = rent_over_time.cumsum()

### final results section ###

st.title("4. Resultado final")
st.markdown(
    """
    Mostramos o resultado final da simulação abaixo, seguindo a seguinte fórmula:\n
    *Resultado = * \n
    **(+)** * Patrimônio líquido * \n
    **(+)** * Total economizado em aluguel * \n 
    **(+)** * Renda passiva acumulada do reinvestimento da diferença entre parcelas e aluguel * \n 
    **(-)** * Total pago no imóvel (entrada + financiamento) * \n
    **(-)** * Renda passiva acumulada do investimento da entrada e FGTS se não tivessem sido usados na compra do imóvel* \n
    Lembrando que resultados positivos indicam que comprar é mais vantajoso que alugar.  
    """
)

downpay_and_amortization = (cash_flow['mort_add_pay'] + cash_flow['downpayment']).cumsum()
estate = cash_flow['buy_estate']

total = rent_over_time + estate - downpay_and_amort_interest - downpay_and_amortization - cash_flow['mort_installment'].cumsum()

if st.checkbox("corrigir pela inflação?"):
    plot_total_inflation(total, monthly_inflation)
else:
    plot_total(total)

words_mapping = {1: 'um **ganho**', -1: 'uma **perda**'}
sign_total = np.sign(total.iloc[-1])

st.markdown(
    f"""
    Depois de **{(len(total) - 1)/12:.1f}** anos, a decisão de comprar um imóvel (ao invés de alugar) acarretará {words_mapping[sign_total]}
    de **{total.iloc[-1]/1e3:.2f} mil reais**.
    """
)