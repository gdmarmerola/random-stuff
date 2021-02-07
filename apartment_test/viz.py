import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core import apply_interest_scalar

def range_min(x):
    return x * (1 - np.sign(x) * 0.3)

def range_max(x):
    return x * (1 + np.sign(x) * 0.2)

def plot_example():
    
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Comprar é mais vantajoso que alugar", "Alugar é mais vantajoso que comprar")    
    )

    fig.add_trace(
        go.Scatter(x=[0, 1], y=[1, 1], fill='tozeroy', line_color='green'),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(x=[0, 1], y=[-1, -1], fill='tozeroy', line_color='red'),
        row=1, col=2
    )

    fig.update_layout(
        height=300,
        width=750,
        showlegend=False,
        font={'family':"Roboto, monospace"},
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.update_yaxes(range=[-1.5, 1.5])
    st.write(fig)

def plot_installment(cash_flow):
    
    fig = go.Figure()

    installment = -cash_flow['mort_installment']

    fig.update_layout(
        legend=dict(orientation="h"),
        width=750,
        height=300,
        font=dict(size=14, family="Roboto, monospace"),
        title='Valor das parcelas',
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.add_trace(
        go.Scatter(
            x=cash_flow.index,
            y=installment,
            fill='tozeroy',
            line_color='red'
        )
    )

    fig.update_yaxes(range=[range_min(installment.min()), 0])
    fig.update_xaxes(title="Meses após compra")
    st.write(fig)

def plot_total_amount_mortgage(cash_flow):
    
    total_amount_mortgage = -(cash_flow['mort_installment'] + cash_flow['mort_fgts_paid'] + cash_flow['downpayment']).cumsum()

    fig = go.Figure()

    fig.update_layout(
        legend=dict(orientation="h"),
        width=750,
        height=300,
        font=dict(size=14, family="Roboto, monospace"),
        title='Total pago no imóvel: entrada + financiamento',
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.add_trace(
        go.Scatter(
            x=cash_flow.index,
            y=total_amount_mortgage,
            fill='tozeroy',
            line_color='red'
        )
    )

    fig.update_yaxes(range=[range_min(total_amount_mortgage.min()), 0])
    fig.update_xaxes(title="Meses após compra")
    st.write(fig)

def plot_home_value(cash_flow):
    
    fig = go.Figure()

    estate = cash_flow['estate']

    fig.update_layout(
        legend=dict(orientation="h"),
        width=750,
        height=300,
        font=dict(size=14, family="Roboto, monospace"),
        title='Patrimônio líquido (valor imóvel - saldo devedor)',
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.add_trace(
        go.Scatter(
            x=cash_flow.index,
            y=estate,
            fill='tozeroy',
            line_color='green'
        )
    )

    fig.update_yaxes(range=[0, range_max(estate.max())])
    fig.update_xaxes(title="Meses após compra")
    st.write(fig)

def plot_interest_downpay_fgts(downpay_and_amort):
    
    fig = go.Figure()

    fig.update_layout(
        legend=dict(orientation="h"),
        width=750,
        height=400,
        font=dict(size=14, family="Roboto, monospace"),
        title='Renda passiva potencial acumulada da entrada e FGTS se não tivessem<br>sido usados na compra do imóvel',
        margin=dict(l=20, r=20, t=80, b=20)
    )

    fig.add_trace(
        go.Scatter(
            x=downpay_and_amort.index,
            y=-downpay_and_amort,
            fill='tozeroy',
            line_color='red'
        )
    )

    fig.update_yaxes(range=[range_min((-downpay_and_amort).min()), 0])
    fig.update_xaxes(title="Meses após compra")
    st.write(fig)

def plot_rent_economy(rent_over_time):

    fig = go.Figure()

    fig.update_layout(
        legend=dict(orientation="h"),
        width=750,
        height=300,
        font=dict(size=14, family="Roboto, monospace"),
        title='Total economizado em aluguel (acumulado)',
        margin=dict(l=20, r=20, t=40, b=20)
    )

    fig.add_trace(
        go.Scatter(
            x=rent_over_time.index,
            y=rent_over_time.cumsum(),
            fill='tozeroy',
            line_color='green'
        )
    )

    fig.update_yaxes(range=[0, range_max(rent_over_time.cumsum().max())])
    fig.update_xaxes(title="Meses após compra")
    st.write(fig)

def plot_rent_installment_diff(diff):

    positive_diff = pd.Series(np.clip(diff, 0, None)).replace(0, np.nan)
    negative_diff = pd.Series(np.clip(diff, None, 0)).replace(0, np.nan)

    fig = go.Figure()

    fig.update_layout(
        width=750,
        height=400,
        font=dict(size=14, family="Roboto, monospace"),
        title='Saldo acumulado fazendo a diferença<br>entre aluguel e parcelas',
        margin=dict(l=20, r=20, t=80, b=20),
        showlegend=False
    )

    fig.add_trace(
        go.Scatter(
            x=diff.index,
            y=positive_diff,
            fill='tozeroy',
            line_color='green'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=diff.index,
            y=negative_diff,
            fill='tozeroy',
            line_color='red'
        )
    )

    fig.update_yaxes(range=[range_min(diff.min()), range_max(diff.max())])
    fig.update_xaxes(title="Meses após compra")
    st.write(fig)


def plot_rent_installment_diff_reinvest(diff):
    
    positive_diff = pd.Series(np.clip(diff, 0, None)).replace(0, np.nan)
    negative_diff = pd.Series(np.clip(diff, None, 0)).replace(0, np.nan)

    fig = go.Figure()

    fig.update_layout(
        width=750,
        height=400,
        font=dict(size=14, family="Roboto, monospace"),
        title='Renda passiva potencial acumulada do reinvestimento da diferença<br>entre aluguel e parcelas',
        margin=dict(l=20, r=20, t=80, b=20),
        showlegend=False
    )

    fig.add_trace(
        go.Scatter(
            x=diff.index,
            y=positive_diff,
            fill='tozeroy',
            line_color='green'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=diff.index,
            y=negative_diff,
            fill='tozeroy',
            line_color='red'
        )
    )

    fig.update_yaxes(range=[range_min(diff.min()), range_max(diff.max())])
    fig.update_xaxes(title="Meses após compra")
    st.write(fig)


def plot_total(total):

    positive_totals = pd.Series(np.clip(total, 0, None)).replace(0, np.nan)
    negative_totals = pd.Series(np.clip(total, None, 0)).replace(0, np.nan)

    fig = go.Figure()

    fig.update_layout(
        width=750,
        height=300,
        font=dict(size=14, family="Roboto, monospace"),
        title='Resultado final acumulado segundo a simulação',
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )

    fig.add_trace(
        go.Scatter(
            x=total.index,
            y=positive_totals,
            fill='tozeroy',
            line_color='green'
        )
    )

    fig.add_trace(
        go.Scatter(
            x=total.index,
            y=negative_totals,
            fill='tozeroy',
            line_color='red'
        )
    )

    fig.update_yaxes(range=[range_min(total.min()), range_max(total.max())])
    fig.update_xaxes(title="Meses após compra")
    st.write(fig)