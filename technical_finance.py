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
plt.style.use(['ggplot'])


class Correlations(ttk.Notebook):
    QPRODUCTS = FUTURES
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax1 = ax.twinx()
    ax2 = ax.twinx()
    ax3 = ax.twinx()
    qfig = plt.figure()
    qax = qfig.add_subplot(211)
    qax1 = qfig.add_subplot(212)
    sfig = plt.figure()
    sax = sfig.add_subplot(211)
    sax1 = sfig.add_subplot(212)
    ffig = plt.figure()
    fax = ffig.add_subplot(111)
    axes = (ax, ax1, ax2, ax3, qax, qax1, sax, sax1, fax)
    ax.set_position(Bbox([[0.1, 0.2], [0.9, 0.8]]))
    ax1.set_position(Bbox([[0.1, 0.2], [0.9, 0.8]]))
    ax2.set_position(Bbox([[0.1, 0.1], [0.9, 0.2]]))
    ax3.set_position(Bbox([[0.1, 0.8], [0.9, 0.9]]))
    
    def __init__(self, root, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        page1 = ttk.Frame(self)
        page2 = ttk.Frame(self)
        page3 = ttk.Frame(self)
        page4 = ttk.Frame(self)
        page5 = ttk.Frame(self)
        
        self.add(page1, text='Charts')
        self.add(page2, text='Quotes')
        self.add(page3, text='Statistics')
        self.add(page4, text='Options')
        self.add(page5, text='Fundamentals')
        self.pack(expand=1, fill='both')
        
        menubar = tk.Menu(root, tearoff=False)
        menu = tk.Menu(menubar, tearoff=False)
        menu.add_command(label='Exit', command=root.quit)
        menu.add_command(label='Settings', command=self.settings)
        menubar.add_cascade(label='File', menu=menu)
        root.config(menu=menubar)
        
        # PAGE 1
        self.canvas = FigureCanvasTkAgg(self.fig, master=page1)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, page1)
        self.toolbar.pack(side=tk.TOP)
        
        self.ticker = tk.Entry(page1)
        tk.Label(page1, text="Stock").pack(side=tk.LEFT)
        self.ticker.pack(side=tk.LEFT)
        self.ticker.insert(0, 'GOOG')
        
        self.start_date = tk.Entry(page1)
        tk.Label(page1, text="start").pack(side=tk.LEFT)
        self.start_date.pack(side=tk.LEFT)
        self.start_date.insert(0, '2017-01-01')
        
        self.end_date = tk.Entry(page1)
        tk.Label(page1, text="end").pack(side=tk.LEFT)
        self.end_date.pack(side=tk.LEFT)
        self.end_date.insert(0, '2018-01-01')
        
        self.rsi = 14
        self.std = 14
        self.fundamentals = {}

        tk_button = tk.Button(page1, text="Get Market Data", command=self.fetch_market)
        tk_button.pack(side=tk.LEFT)

        self.formatter = ScalarFormatter(useOffset=False)
        self.formatter.set_scientific(False)
        
        # PAGE 2
        self.quotes = tk.Text(page2)
        self.quotes.pack(side=tk.TOP, expand=1, fill='both')

        # PAGE 3
        self.stats = tk.Text(page3, width=25)
        self.stats.pack(side=tk.LEFT)
        self.scanvas = FigureCanvasTkAgg(self.sfig, master=page3)
        self.scanvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        
        # PAGE 4
        self.qcanvas = FigureCanvasTkAgg(self.qfig, master=page4)
        self.qcanvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.qtoolbar = NavigationToolbar2TkAgg(self.qcanvas, page4)
        self.qtoolbar.pack()
        
        # PAGE 5
        self.fcanvas = FigureCanvasTkAgg(self.ffig, master=page5)
        self.fcanvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def settings(self):
        top = tk.Toplevel()
        top.title('Settings')
        self.ticker_setting = tk.Entry(top)
        tk.Label(top, text="Stock").pack()
        self.ticker_setting.pack()
        self.ticker_setting.insert(0, self.ticker.get())
        self.rsi_setting = tk.Entry(top)
        tk.Label(top, text='RSI').pack()
        self.rsi_setting.pack()
        self.rsi_setting.insert(0, self.rsi)
        self.std_setting = tk.Entry(top)
        tk.Label(top, text='STD').pack()
        self.std_setting.pack()
        self.std_setting.insert(0, self.std)
        self.start_date_setting = tk.Entry(top)
        tk.Label(top, text="start").pack()
        self.start_date_setting.pack()
        self.start_date_setting.insert(0, self.start_date.get())    
        self.end_date_setting = tk.Entry(top)
        tk.Label(top, text="end").pack()
        self.end_date_setting.pack()
        self.end_date_setting.insert(0, self.end_date.get())
        update_settings = tk.Button(top, text='Update', command=self.fetch_new_market)
        update_settings.pack()
        exit_settings = tk.Button(top, text='Exit', command=top.destroy)
        exit_settings.pack()
        
    def fetch_new_market(self):
        self.update_ticker(self.ticker_setting.get())
        self.rsi = self.rsi_setting.get()
        self.std = self.std_setting.get()
        self.update_dates([self.start_date_setting.get(), self.end_date_setting.get()])
        self.fetch_market()
        
    def fetch_market(self):
        self.plot_candles()
        self.plot_options_data()
        self.stats.delete(1.0, tk.END)
        self.stats.insert(tk.END, self.xs['Adj Close'].pct_change().describe())
        self.canvas.draw()
        self.scanvas.draw()
        self.toolbar.update()
        
    def update_dates(self, values):
        start, end = values
        self.start_date.delete(0, tk.END)
        self.end_date.delete(0, tk.END)
        self.start_date.insert(tk.END, start)
        self.end_date.insert(tk.END, end)
        
    def update_ticker(self, value):
        self.ticker.delete(0, tk.END)
        self.ticker.insert(tk.END, value)
        
    def plot_options_data(self):
        _options = pdr.Options(self._xs, data_source='yahoo')
        _dat = _options.get_all_data()
        self.quotes.delete(1.0, tk.END)
        self.quotes.insert(tk.END, _dat[['Bid', 'Ask']])
        _dat[['Bid', 'Ask']].plot(ax=self.qax, subplots=True)
        
    def clear_axes(self):
        for _ax in self.axes:
            _ax.clear()

    def _get_df(self, product):
        if product in self.QPRODUCTS:
            str_start = '%s-%s-%s' % list(map(int, self.start_date.get().split('-')))
            df = quandl.get(self.QPRODUCTS[product], start_date=str_start)
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
        for col in _columns:
            if col in self.xs.columns:
                return col
        raise ValueError('could not find column names')

    def relative_strength_index(self):
        X = self.xs['Adj Close'].diff()
        ups, downs = X.copy(), X.copy()
        ups[ups < 0] = 0
        downs[downs > 0] = 0
        roll_up = ups.rolling(window=int(self.rsi)).mean()
        roll_down = downs.apply(abs).rolling(window=int(self.rsi)).mean()
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
        means = self.xs.Close.rolling(window=int(self.std)).mean()
        stds = 2 * self.xs.Close.rolling(window=int(self.std)).std()
        vol = self.xs.Close.pct_change().rolling(window=3).std()
        rsi = self.relative_strength_index()

        self.ax.set_ylabel('price') 
        self.ax.set_xticklabels(dts, rotation=25)
        self.ax.xaxis.set_visible(False)
        
        self.ax1.set_ylim([0, self.xs['Volume'].max()*4])
        self.ax1.set_ylabel('volume')
        
        self.ax3.set_title('%s - %s' % (dts[0], dts[-1]))
        
        candlestick_ohlc(self.ax, candles, width=100000, colorup='g', colordown='r')
            
        self.ax.plot(ts, means - stds, ':', color='grey', alpha=0.5)
        self.ax.plot(ts, means + stds, ':', color='grey', alpha=0.5)
        
        self.ax1.fill_between(ts, self.xs['Volume'], label='avg volume: %s' % round(self.xs['Volume'].mean(), 2), alpha=0.25)
        
        self.ax2.fill_between(ts, vol, label='avg std returns: %s' % round(vol.mean(), 4), alpha=0.5, color='grey')
        
        self.ax3.plot(ts, rsi, label='rsi', alpha=0.5)
        self.ax3.axhline(30, linewidth=0.5,  alpha=0.25)
        self.ax3.axhline(70, linewidth=0.5, alpha=0.25)
        
        log_xs = self.xs['Adj Close'].apply(np.log)
        
        self.sax.fill_between(dts, log_xs.pct_change(), label='log returns')
        
        self.sax1.plot(dts, log_xs, label='log prices')  
        
        for _ax in self.axes:
            _ax.grid(False)
            _ax.legend(loc='best', fancybox=True)
            _ax.xaxis.set_major_formatter(self.formatter)
            _ax.yaxis.set_major_formatter(self.formatter)
  
  
if __name__ == '__main__':
    root = tk.Tk()
    app = Correlations(root)
    app.mainloop()
