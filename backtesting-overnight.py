import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np

def fetch_data(tickers, start_date, end_date):
    """Fetches stock data from yfinance."""
    data = yf.download(tickers, start=start_date, end=end_date)
    return data

def calculate_returns(data, strategy):
    """Calculates cumulative returns for a given strategy."""
    returns = pd.DataFrame()
    for ticker in data.columns.get_level_values(1).unique():
        try:
            if strategy == 'open_to_close':
                daily_returns = data['Close', ticker] / data['Open', ticker] - 1
            elif strategy == 'close_to_open':
                daily_returns = data['Open', ticker].shift(-1) / data['Close', ticker] - 1
                daily_returns = daily_returns.dropna()
            elif strategy == 'buy_and_hold':
                daily_returns = data['Adj Close', ticker].pct_change()
                daily_returns = daily_returns.dropna()
            else:
                raise ValueError("Invalid strategy")
            cumulative_returns = (1 + daily_returns).cumprod()
            returns[ticker] = cumulative_returns
        except KeyError as e:
            st.error(f"Error calculating returns for {ticker}: {e}. Ensure the ticker has the required data.")
            continue
    return returns

def plot_investment_value(returns_open_to_close, returns_close_to_open, returns_buy_and_hold, start_date, end_date, initial_investment, log_scale=False):
    """Plots cumulative investment value for all strategies."""
    fig = go.Figure()

    all_values = []

    for ticker in returns_open_to_close.columns:
        investment_value_open_to_close = returns_open_to_close[ticker] * initial_investment
        investment_value_close_to_open = returns_close_to_open[ticker] * initial_investment
        investment_value_buy_and_hold = returns_buy_and_hold[ticker] * initial_investment

        fig.add_trace(go.Scatter(x=returns_open_to_close.index, y=investment_value_open_to_close, mode='lines', name=f'{ticker} - Apertura a Cierre'))
        fig.add_trace(go.Scatter(x=returns_close_to_open.index, y=investment_value_close_to_open, mode='lines', name=f'{ticker} - Cierre a Apertura'))
        fig.add_trace(go.Scatter(x=returns_buy_and_hold.index, y=investment_value_buy_and_hold, mode='lines', name=f'{ticker} - Comprar y Mantener'))

        all_values.extend(investment_value_open_to_close)
        all_values.extend(investment_value_close_to_open)
        all_values.extend(investment_value_buy_and_hold)

    # Add horizontal line at initial investment
    fig.add_trace(go.Scatter(x=[returns_open_to_close.index[0], returns_open_to_close.index[-1]], y=[initial_investment, initial_investment],
                             mode='lines', line=dict(color='black', dash='dash'), name='Inversión Inicial'))

    fig.update_layout(title=f'Valor de la Inversión desde {start_date} hasta {end_date}',
                      xaxis_title='Fecha',
                      yaxis_title='Valor de la Inversión ($)',
                      legend_title='Estrategia',
                      yaxis_type="log" if log_scale else None)

    if log_scale:
        all_values.append(initial_investment)
        all_values = np.array(all_values)

        min_val = np.min(all_values[all_values > 0]) if np.any(all_values > 0) else 0.1
        max_val = np.max(all_values)

        # Set the range to be a bit wider than the min and max values
        range_padding = 0.1 * (max_val - min_val)
        fig.update_yaxes(range=[np.log10(min_val - range_padding) if min_val - range_padding > 0 else np.log10(0.1), np.log10(max_val + range_padding)])

    st.plotly_chart(fig)

def main():
    st.title("Aplicación de Backtesting de Acciones")

    # Sidebar for user inputs
    st.sidebar.header("Parámetros de Entrada")
    start_date = st.sidebar.date_input("Fecha de Inicio", value=pd.to_datetime("2023-01-01"), min_value=pd.to_datetime("1970-01-01"))
    end_date = st.sidebar.date_input("Fecha de Fin", value=date.today() + timedelta(days=1))
    tickers = st.sidebar.text_input("Ingrese los símbolos de las acciones (separados por comas, máximo 5)", "AAPL,MSFT,GOOG").upper()
    tickers = [ticker.strip() for ticker in tickers.split(',')][:5]
    initial_investment = st.sidebar.number_input("Inversión Inicial ($)", value=100.00, min_value=0.01)
    log_scale = st.sidebar.checkbox("Escala Logarítmica en el eje Y", value=False)

    if st.sidebar.button("Ejecutar Backtest"):
        if not tickers:
            st.error("Por favor, ingrese al menos un símbolo de acción.")
            return
        try:
            data = fetch_data(tickers, start_date, end_date)
            if data.empty:
                st.error("No se encontraron datos para los símbolos y el rango de fechas seleccionados.")
                return
            returns_open_to_close = calculate_returns(data, 'open_to_close')
            returns_close_to_open = calculate_returns(data, 'close_to_open')
            returns_buy_and_hold = calculate_returns(data, 'buy_and_hold')
            plot_investment_value(returns_open_to_close, returns_close_to_open, returns_buy_and_hold, start_date, end_date, initial_investment, log_scale)
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    main()
