#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from matplotlib import use as mpl_use
mpl_use('TkAgg')
from pandas import DataFrame
from pandas import set_option as pandas_options
pandas_options('display.max_rows', 100)
pandas_options('display.height', 1000000)
from quandl_products import FUTURES
from pandas_datareader import data as pdr
import datetime as dt
import quandl
quandl.ApiConfig.api_key = "Gwk_6cq1wNLgvTYF5bjs"
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from matplotlib.ticker import ScalarFormatter
from matplotlib.finance import candlestick_ohlc
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
plt.style.use(['seaborn-dark', 'dark_background'])


class Correlations(ttk.Notebook):
    QPRODUCTS = FUTURES
    fig = plt.figure()
    qfig = plt.figure()
    ax = fig.add_subplot(111)
    ax1 = ax.twinx()
    ax2 = ax.twinx()
    ax3 = ax.twinx()
    axes = (ax, ax1, ax2, ax3)
    qax = qfig.add_subplot(211)
    qax1 = qfig.add_subplot(212)

    def __init__(self, root, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        page1 = ttk.Frame(self)
        page2 = ttk.Frame(self)
        page3 = ttk.Frame(self)
        page4 = ttk.Frame(self)
        
        self.add(page1, text='Charts')
        self.add(page2, text='Quotes')
        self.add(page3, text='Statistics')
        self.add(page4, text='Options')
        self.pack(expand=1, fill='both')
        
        # PAGE 1
        self.canvas = FigureCanvasTkAgg(self.fig, master=page1)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, page1)
        self.toolbar.pack(side=tk.TOP)
        
        self.ticker = tk.Entry(page1)
        tk.Label(page1, text="Stock").pack(side=tk.LEFT)
        self.ticker.pack(side=tk.LEFT)
        self.ticker.insert(0, 'AAPL')
        
        self.start_date = tk.Entry(page1)
        tk.Label(page1, text="start").pack(side=tk.LEFT)
        self.start_date.pack(side=tk.LEFT)
        self.start_date.insert(0, '2017-01-01')
        
        self.end_date = tk.Entry(page1)
        tk.Label(page1, text="end").pack(side=tk.LEFT)
        self.end_date.pack(side=tk.LEFT)
        self.end_date.insert(0, '2018-01-01')

        tk_button = tk.Button(page1, text="Get Market Data", command=self.fetch_market)
        tk_button.pack(side=tk.LEFT)

        self.formatter = ScalarFormatter(useOffset=False)
        self.formatter.set_scientific(False)
        
        # PAGE 2
        self.quotes = tk.Text(page2)
        self.quotes.pack(side=tk.TOP)

        # PAGE 3
        self.stats = tk.Text(page3)
        self.stats.pack(side=tk.LEFT)
        
        # PAGE 4
        self.qcanvas = FigureCanvasTkAgg(self.qfig, master=page4)
        self.qcanvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.toolbar = NavigationToolbar2TkAgg(self.qcanvas, page4)
        self.toolbar.pack(side=tk.TOP)

    def fetch_market(self):
        self.plot_candles()
        self.plot_options_data()
        self.quotes.insert(tk.END, self.xs)
        self.stats.insert(tk.END, self.xs.describe()['Adj Close'])
        self.canvas.draw()
        self.toolbar.update()
        
    def plot_options_data(self):
        _options = pdr.Options(self._xs, data_source='yahoo')
        _dat = _options.get_all_data()
        self.quotes.insert(tk.END, _dat['JSON'])
        _dat.plot(ax=self.qax, subplots=True)
        
    def clear_axes(self):
        for _ax in self.axes:
            _ax.clear()

    def _get_df(self, product):
        if product in self.QPRODUCTS:
            str_start = '%s-%s-%s' % list(map(int, self.start_date.get().split('-')))
            df = quandl.get(self.QPRODUCTS[product], start_start_date=str_start)
        else:
            dt_start = dt.datetime(*list(map(int, self.start_date.get().split('-'))))
            dt_end = dt.datetime(*list(map(int, self.end_date.get().split('-'))))
            try:
                df = pdr.DataReader(product, 'yahoo', start=dt_start, end=dt_end)       
            except:
                raise ValueError('%s not available in FUTURES or finance.yahoo.com' % product)
        return df

    def _get_column_names(self):
        _columns = ('Adj Close', 'Settle', 'Value', 'Last')
        x_col = None
        for col in _columns:
            if col in self.xs.columns:
                return x_col
        raise ValueError('could not find column names')

    def relative_strength_index(self):
        X = self.xs['Adj Close'].diff()
        ups, downs = X.copy(), X.copy()
        ups[ups < 0] = 0
        downs[downs > 0] = 0
        roll_up = ups.rolling(window=14).mean()
        roll_down = downs.apply(abs).rolling(window=14).mean()
        RSI = roll_up / roll_down
        RSI = 100 - (100 / (1 + RSI))
        return RSI

    def plot_candles(self, mavgs=[7, 14, 28, 55, 125]):
        self._xs = self.ticker.get()
        self.xs = self._get_df(self._xs)
        self.x_col= self._get_column_names()
        
        self.clear_axes()
        self.fig.suptitle(self._xs)

        ts = list(map(lambda x: x.timestamp(), self.xs.index))
        dts = list(map(lambda x: dt.datetime.fromtimestamp(x), ts))
        
        candles = list(zip(ts, self.xs.Open, self.xs.High, self.xs.Low, self.xs.Close))
        means = self.xs.Close.rolling(window=14).mean()
        stds = 2 * self.xs.Close.rolling(window=14).std()
        vol = self.xs.Close.pct_change().rolling(window=3).std()
        rsi = self.relative_strength_index()

        self.ax.set_position(Bbox([[0.1, 0.2], [0.9, 0.8]]))
        self.ax.set_ylabel('price') 
        self.ax.set_xticklabels(dts, rotation=25)
        self.ax.xaxis.set_visible(False)
        
        self.ax1.set_position(Bbox([[0.1, 0.2], [0.9, 0.8]]))
        self.ax1.set_ylim([0, self.xs['Volume'].max()*4])
        self.ax1.set_ylabel('volume')
        
        self.ax2.set_position(Bbox([[0.1, 0.1], [0.9, 0.2]]))
        
        self.ax3.set_position(Bbox([[0.1, 0.8], [0.9, 0.9]]))
        self.ax3.set_title('%s - %s' % (dts[0], dts[-1]))
        
        candlestick_ohlc(self.ax, candles, width=100000, colorup='g', colordown='r')
        
        for avg in mavgs:
            _means = self.xs.Close.rolling(window=avg).mean()
            self.ax.plot(ts, _means, ':', alpha=0.25, label='%s mavg' % avg)
                         
        self.ax.plot(ts, means - stds, ':', color='w', alpha=0.5, label='14 std lower')
        self.ax.plot(ts, means + stds, ':', color='w', alpha=0.5, label='14 std upper')
        self.ax1.fill_between(ts, self.xs['Volume'], label='volume', alpha=0.25)
        self.ax2.fill_between(ts, vol, label='mstd returns', alpha=0.5, color='w')
        self.ax3.plot(ts, rsi, label='rsi', alpha=0.5)
        self.ax3.axhline(30, linewidth=0.5,  alpha=0.25)
        self.ax3.axhline(70, linewidth=0.5, alpha=0.25)
        
        for _ax in self.axes:
            _ax.grid(False)
            _ax.legend(loc='best', fancybox=True)
            _ax.xaxis.set_major_formatter(self.formatter)
            _ax.yaxis.set_major_formatter(self.formatter)

if __name__ == '__main__':
    root = tk.Tk()
    app = Correlations(root)
    app.mainloop()
