from flask import Flask
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

SYMBOLS = ["SPY", "QQQ"]
INITIAL_CAPITAL = 100000
SHORT_WINDOW = 50
LONG_WINDOW = 200

def run_strategy(symbol):
    df = yf.download(symbol, start="2018-01-01", progress=False)
    df = df[['Close']].dropna()

    df['ma_short'] = df['Close'].rolling(SHORT_WINDOW).mean()
    df['ma_long'] = df['Close'].rolling(LONG_WINDOW).mean()

    df['signal'] = 0
    df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1
    df['signal'] = df['signal'].shift(1).fillna(0)

    cash = INITIAL_CAPITAL
    position = 0
    values = []

    for _, row in df.iterrows():
        price = row['Close']
        signal = row['signal']

        if signal == 1 and position == 0:
            size = cash // price
            if size > 0:
                cash -= size * price
                position = size

        elif signal == 0 and position > 0:
            cash += position * price
            position = 0

        values.append(cash + position * price)

    df["portfolio_value"] = values
    total_return = (values[-1] / INITIAL_CAPITAL - 1) * 100

    return df, round(total_return, 2)

@app.route("/")
def home():
    html = "<h1>Trading Bot Dashboard</h1>"

    for symbol in SYMBOLS:
        df, total_return = run_strategy(symbol)

        plt.figure()
        plt.plot(df["portfolio_value"])
        plt.title(f"{symbol} Portfolio Value")

        img = io.BytesIO()
        plt.savefig(img, format="png")
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        html += f"<h2>{symbol}</h2>"
        html += f"<p>Total Return: {total_return}%</p>"
        html += f'<img src="data:image/png;base64,{plot_url}"/>'

    return html
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
