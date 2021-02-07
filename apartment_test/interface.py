import numpy as np
import pandas as pd
import streamlit as st
from core import apply_interest_series

def display_header():

    st.title('Vale a pena comprar ou alugar?')
    st.write('Vamos tentar responder a essa pergunta passo a passo tentando fazer um cálculo de fluxo de caixa.')

def display_basic_info_section():

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

    time_horizon = st.slider(
        'Você quer projetar a simulação financeira para quantos anos no futuro?',
        0,
        40,
        30, 
        1,
    ) * 12

    return total_amount, downpay_amount, home_appreciation, inflation, time_horizon

def display_tutorial_section():

    st.title("Como usar essa ferramenta")
    st.write("Vamos apresentar diversos gráficos tentando detalhar a dinâmica financeira entre comprar e alugar, " 
            "adotando a perspectiva de **comprar** um apartamento. ")
    st.write("Dessa forma, nos gráficos seguintes, **valores positivos** representam "
            " que **comprar** é **vantajoso** em relação à **alugar**. "
            "Por outro lado, valores **negativos** representam que **alugar** é **mais vantajoso** em relação à **comprar**.")

def display_mortage_section_basic_info(total_amount, downpay_amount):

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

    return mortgage_value, n_months, mort_interest


def display_mortage_section_fgts_info(downpay_amount, mortgage_value):

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

    return downpay_fgts_amount, fgts_amount, fgts_frequency

def display_investments_section():

    st.title("2. Entrada, FGTS e investimentos")
    st.markdown(
        """
        Outro fator importante que torna o investimento em imóveis **desvantajoso**
        em relação ao aluguel é **imobilizar recursos próprios e FGTS**, que poderiam estar
        gerando **renda passiva** caso não tivessem sido usados na compra do imóvel. 
        O FGTS rende a uma taxa de 3% ao ano. 
        """
    )

    invest_options = {
        'Não investiria esses recursos (custo oportunidade de 0%)': 0.0,
        'Poupança (custo oportunidade de 1%)': 0.01,
        'Renda fixa / Tesouro Direto (custo oportunidade de 3%)': 0.03,
        'Bolsa / Índice Ibovespa (custo oportunidade de 7%)': 0.07,
        'Investiria em diversos ativos diferentes (selecione seu custo de oportunidade)': None,
    }

    invest_type = st.selectbox(
        'Onde você investiria os recursos próprios da entrada (sem FGTS) se não usasse para comprar o imóvel?',
        list(invest_options.keys()),
        index = 2
    )

    invest_interest = invest_options[invest_type]
    
    if invest_interest == None:

        invest_interest = st.slider(
            'Quanto você espera que seja a valorização média anual dos seus investimentos?',
            0.0,
            30.0,
            10.0, 
            0.1,
        ) / 100 

    return invest_interest

def display_rent_section():

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

    return rent_amount, rent_appreciation

def display_rent_reinvestment_option(cash_flow, rent_over_time, invest_interest):

    is_rent_reinvestment = st.checkbox('Deseja simular o reinvestimento da diferença entre parcelas e aluguel? (usando mesma taxa de rendimento da seção (2))', True)

    if is_rent_reinvestment:

        diff = rent_over_time - cash_flow['mort_installment']

        positive_diff = diff.clip(0, None)
        negative_diff = diff.clip(None, 0)

        positive_diff_interest = apply_interest_series(positive_diff, invest_interest) - positive_diff.cumsum()
        negative_diff_interest = apply_interest_series(negative_diff, invest_interest) - negative_diff.cumsum()
        
        diff_interest = (positive_diff_interest + negative_diff_interest).round(0)
        rent_over_time = rent_over_time.cumsum() + diff_interest

    else:
        rent_over_time = rent_over_time.cumsum()
        diff_interest = None

    return rent_over_time, diff_interest, is_rent_reinvestment

def display_final_results_section():

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
    
    use_inflation = st.checkbox("corrigir pela inflação?")

    return use_inflation

def display_conclusion(total):

    words_mapping = {1: 'um **ganho**', -1: 'uma **perda**'}
    sign_total = np.sign(total.iloc[-1])

    st.markdown(
        f"""
        Depois de **{(len(total) - 1)/12:.1f}** anos, 
        a decisão de comprar um imóvel (ao invés de alugar) acarretará 
        {words_mapping[sign_total]}
        de **{total.iloc[-1]/1e3:.0f} mil reais**.
        """
    )

