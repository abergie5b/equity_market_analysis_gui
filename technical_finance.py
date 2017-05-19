#!/usr/bin/env python3
'''
download the anaconda distribution of python3
'''
import os
import tkinter as tk
from tkinter import ttk
from matplotlib import use as mpl_use
from pandas import DataFrame, Series
from pandas import set_option as pandas_options
from quandl_products import FUTURES
from pandas_datareader import data as pdr
import datetime as dt
import quandl
import numpy as np
from functools import reduce
mpl_use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from matplotlib.ticker import ScalarFormatter
from matplotlib.finance import candlestick_ohlc
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from scrapers import yahoo_fundamental_scraper
from bs4 import BeautifulSoup
import requests
from PIL import Image, ImageTk

pandas_options('display.max_rows', 100)
pandas_options('display.height', 1000000)
plt.style.use(['ggplot'])

quandl.ApiConfig.api_key = "Gwk_6cq1wNLgvTYF5bjs"


class EquityMarketAnalysisGUI(ttk.Notebook):
    '''
    Equity Market Analysis GUI
    
        - stock market, options and fundamental data
                - finance.yahoo.com
                - quandl.com
        - technical indicators RSI, SMA, BBands
        - exporting and importing data to CSV
    
    Created by Andrew Berger
    '''
            

    # Charts
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax1 = ax.twinx()
    ax2 = ax.twinx()
    ax3 = ax.twinx()

    # Options
    qfig = plt.figure()
    qax = qfig.add_subplot(221)
    qax1 = qax.twinx()
    qax2 = qfig.add_subplot(222)
    qax3 = qfig.add_subplot(223)
    qax4 = qfig.add_subplot(224)
    
    # Statistics
    sfig = plt.figure()
    sax = sfig.add_subplot(221)
    sax1 = sfig.add_subplot(222)
    sax2 = sfig.add_subplot(223)
    sax3 = sfig.add_subplot(224)

    # Fundamentals 
    ffig = plt.figure()
    fax = ffig.add_subplot(111)
    
    # MPL POSITIONING & FORMATTING
    ax.set_position(Bbox([[0.1, 0.2], [0.9, 0.8]]))
    ax1.set_position(Bbox([[0.1, 0.2], [0.9, 0.8]]))
    ax2.set_position(Bbox([[0.1, 0.1], [0.9, 0.2]]))
    ax3.set_position(Bbox([[0.1, 0.8], [0.9, 0.9]]))
    
    formatter = ScalarFormatter(useOffset=False)
    formatter.set_scientific(False)
    
    axes = (
            ax, ax1, ax2, ax3,           # Charts 
            qax, qax1, qax2, qax3, qax4, # Quotes
            sax, sax1, sax2, sax3,       # Statistics
            fax                          # Fundamentals
            )
            
    stock = 'GOOG'
    start = '2017-01-01'
    end = '2018-01-01'
    rsi = 14
    std = 14
    
    fundamentals = {}

    def __init__(self, root, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        root.title('Equity Market Analysis GUI')  
        
        page1 = ttk.Frame(self)
        page11 = ttk.Frame(page1, relief='ridge')
        page12 = ttk.Frame(page1, relief='ridge')
        page2 = ttk.Frame(self)
        page3 = ttk.Frame(self)
        page5 = ttk.Frame(self)
        
        self.add(page1, text='Charts')
        self.add(page2, text='Quotes')
        self.add(page3, text='Statistics')
        self.add(page5, text='Fundamentals')
        
        page11.pack(side=tk.LEFT)
        page12.pack(side=tk.LEFT, expand=True, fill='both')
        self.pack(expand=True, fill='both')
        
        root.bind('<Return>', self.fetch_market)
        
        image = Image.open("yahoo_icon.PNG")
        photo = ImageTk.PhotoImage(image, master=page11)
        
        label = tk.Label(page11, image=photo)
        label.image = photo
        label.pack()

        # Menubar
        menubar = tk.Menu(root, tearoff=False)
        menu = tk.Menu(menubar, tearoff=False)
        menu.add_command(label='Settings', command=self.settings)
        menu.add_command(label='Export', command=self.export)
        menu.add_command(label='Links', command=self.links)
        menu.add_command(label='Exit', command=root.quit)
        menu1 = tk.Menu(menubar, tearoff=False)
        menu1.add_command(label='About', command=self.about)
        menubar.add_cascade(label='File', menu=menu)
        menubar.add_cascade(label='Help', menu=menu1)
        root.config(menu=menubar)
        
        # Charts
        self.ticker = tk.Entry(page11)
        tk.Label(page11, text="Stock").pack(side=tk.TOP)
        self.ticker.pack(side=tk.TOP)
        self.ticker.insert(0, self.stock)
        
        self.start_date_entry = tk.Entry(page11)
        tk.Label(page11, text="Start").pack(side=tk.TOP)
        self.start_date_entry.pack(side=tk.TOP, padx=10)
        self.start_date_entry.insert(0, self.start)
        
        self.end_date_entry = tk.Entry(page11)
        tk.Label(page11, text="End").pack(side=tk.TOP)
        self.end_date_entry.pack(side=tk.TOP, padx=10)
        self.end_date_entry.insert(0, self.end)
        
        self.enable_bbands = tk.IntVar()
        bbands_check = tk.Checkbutton(page11, text='bollinger bands', 
                                      variable=self.enable_bbands)
        bbands_check.pack()
         
        tk_button = tk.Button(page11, text="Get Market Data", command=self.fetch_market)
        tk_button.pack(side=tk.TOP, padx=25, pady=50)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=page12)
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, page12)
        self.toolbar.pack(side=tk.TOP)     
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Quotes
        self.quotes = tk.Text(page2, width=50)
        self.quotes.pack(side=tk.LEFT)
        self.qcanvas = FigureCanvasTkAgg(self.qfig, master=page2)
        self.qcanvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Statistics
        self.stats = tk.Text(page3, width=35)
        self.stats.pack(side=tk.LEFT)
        self.scanvas = FigureCanvasTkAgg(self.sfig, master=page3)
        self.scanvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Fundamentals
        self.fcanvas = FigureCanvasTkAgg(self.fig, master=page5)
        self.fstats = tk.Text(page5, width=75)
        self.fstats.pack(side=tk.LEFT)
        self.fcanvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH)

    def about(self):
        top = tk.Toplevel(width=750)
        top.title('About')
        frame = tk.Frame(top, relief='ridge')
        frame.pack()
        msg = self.__doc__
        tk.Label(frame, text=msg).pack(padx=25, pady=25)
        tk.Button(frame, text='Close', command=top.destroy).pack(pady=25)
        
    def settings(self):
        top = tk.Toplevel(width=750)
        top.title('Settings')

        self.ticker_setting = tk.Entry(top)
        tk.Label(top, text="Stock").pack(padx=25)
        self.ticker_setting.pack(padx=25)
        self.ticker_setting.insert(0, self.ticker.get())

        self.rsi_setting = tk.Entry(top)
        tk.Label(top, text='RSI').pack(padx=25)
        self.rsi_setting.pack(padx=25)
        self.rsi_setting.insert(0, self.rsi)

        self.std_setting = tk.Entry(top)
        tk.Label(top, text='STD').pack(padx=25)
        self.std_setting.pack(padx=25)
        self.std_setting.insert(0, self.std)

        self.start_date_entry_setting = tk.Entry(top)
        tk.Label(top, text="start").pack(padx=25)
        self.start_date_entry_setting.pack(padx=25)
        self.start_date_entry_setting.insert(0, self.start_date_entry.get())    

        self.end_date_entry_setting = tk.Entry(top)
        tk.Label(top, text="end").pack(padx=25)
        self.end_date_entry_setting.pack(padx=25)
        self.end_date_entry_setting.insert(0, self.end_date_entry.get())

        update_settings = tk.Button(top, text='Update', command=self.fetch_new_market)
        update_settings.pack(padx=25, pady=10)
        exit_settings = tk.Button(top, text='Exit', command=top.destroy)
        exit_settings.pack(padx=25)
    
    def export(self):
        top = tk.Toplevel(width=5000)
        top.title('Export Market Data')
        path = os.getcwd()
        frame = tk.Frame(top)
        frame1 = tk.Frame(top)
        frame.pack(side=tk.TOP)
        frame1.pack(side=tk.TOP)
        
        self.export_price_data = tk.IntVar()
        self.export_options_data = tk.IntVar()
        self.export_fundamentals_data = tk.IntVar()
        _export_price_data = tk.Checkbutton(frame, text='Include share prices', 
                                            variable=self.export_price_data)
        _export_price_data.pack(padx=25, pady=5)                                    
        _export_options_price_data = tk.Checkbutton(frame, text='Include options prices', 
                                            variable=self.export_options_data)   
        _export_options_price_data.pack(padx=25, pady=5)
        _export_fundamentals_price_data = tk.Checkbutton(frame, text='Include fundamentals data', 
                                            variable=self.export_fundamentals_data)   
        _export_fundamentals_price_data.pack(padx=25, pady=5)
        
        submit = tk.Button(frame1, text='Save', command=lambda : self._savefile_to_disk(top))
        tk.Label(frame1, text=path).pack(pady=10)
        submit.pack(side=tk.LEFT, padx=25, pady=10)
        exit = tk.Button(frame1, text='Close', command=top.destroy)
        exit.pack(side=tk.RIGHT, padx=25, pady=10)
        
    def _savefile_to_disk(self, inst):
        if self.export_price_data:
            self.xs.to_csv('%s_%s_to_%s.csv' % (
                            self._xs, self.start_date_entry.get(), self.end_date_entry.get()))
        if self.export_options_data:
            self.options_xs.to_csv('%s_%s_to_%s_options.csv' % (
                                    self._xs, self.start_date_entry.get(), self.end_date_entry.get()))
        if self.export_fundamentals_data:
            self.fundamentals.to_csv('%s_%s_to_%s_fundamentals.csv' % (
                                     self._xs, self.start_date_entry.get(), self.end_date_entry.get()))
        inst.destroy()
           
    def links(self):
        pass

    def fetch_new_market(self):
        self.update_ticker(self.ticker_setting.get())
        self.rsi = self.rsi_setting.get()
        self.std = self.std_setting.get()
        self.update_dates([self.start_date_entry_setting.get(), self.end_date_entry_setting.get()])
        self.fetch_market()
        
    def fetch_market(self, event=None):
        self.plot_candles()
        self.plot_options_data()
        self.update_statistics()
        self.canvas.draw()
        self.scanvas.draw()
        self.qcanvas.draw()
        self.toolbar.update()
        
    def update_statistics(self):
        data = self.xs['Adj Close']
        vol = self.xs['Volume']
        msg = 'avg volume: %s\nmin volume: %s\nmax volume: %s\n' % (
               vol.mean(), vol.min(), vol.max())
        self.stats.delete(1.0, tk.END)
        self.stats.insert(tk.END, '%s: %s\n' % (self._xs, data[-1]))
        self.stats.insert(tk.END, msg)
        
    def update_dates(self, values):
        start, end = values
        self.start_date_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(tk.END, start)
        self.end_date_entry.insert(tk.END, end)
        
    def update_ticker(self, value):
        self.ticker.delete(0, tk.END)
        self.ticker.insert(tk.END, value)
        
    def plot_options_data(self):
        _options = pdr.Options(self._xs, data_source='yahoo')
        self.options_xs = _options.get_near_stock_price(call=True, put=True, above_below=35)
        print(self.options_xs.ix[0])
        price, underlying = self.options_xs['Underlying_Price'][0], self.options_xs['Underlying'][0]
        
        _index = self.options_xs.index.get_level_values('Symbol')
        data_reset = self.options_xs.reset_index()
        data_reset.index = _index
        
        vols = list(map(lambda x: x['impliedVolatility']*100, data_reset['JSON']))
        open_int = list(map(lambda x: x['openInterest']*100, data_reset['JSON']))
        pct_change = list(map(lambda x: x['percentChange']*100, data_reset['JSON']))
        
        calls = self.options_xs[self.options_xs.index.get_level_values('Type').isin(['call'])]
        calls_index = self.options_xs.index.get_level_values('Symbol')
        calls_data_reset = self.options_xs.reset_index()
        data_reset.index = calls_index
        
        puts = self.options_xs[self.options_xs.index.get_level_values('Type').isin(['put'])]
        puts_index = self.options_xs.index.get_level_values('Symbol')
        puts_data_reset = self.options_xs.reset_index()
        data_reset.index = puts_index
        
        self.quotes.delete(1.0, tk.END)
        self.quotes.insert(tk.END, data_reset[['Strike', 'Bid', 'Ask']])
        
        self.qax.set_title('%s: $%s' % (self._xs, price))
        self.qax.bar(data_reset['Strike'], data_reset['Bid'], color='g')
        self.qax.bar(data_reset['Strike'], data_reset['Ask'], color='r')
        #self.qax.set_xticklabels(data_reset['Symbol'], rotation=45)
        
        self.qax1.fill_between(data_reset['Strike'], vols,
                               label='impliedVol', alpha=0.25)
        self.qax2.fill_between(data_reset['Strike'], open_int,
                               label='openInt', alpha=0.25)
        self.qax3.fill_between(calls_data_reset['Strike'], list(map(lambda x: x['openInterest']*100, calls_data_reset['JSON'])))
        self.qax4.fill_between(puts_data_reset['Strike'], list(map(lambda x: x['openInterest']*100, puts_data_reset['JSON'])))
        
        self.qax1.set_ylim([0, max(vols)*4])
        self.qax2.set_ylim([0, max(open_int)*4])
        self.qax.set_xlabel('strike')
        self.qax.set_ylabel('price')
        self.qax.legend(loc='best', fancybox=True)
        self.qax1.legend(loc='bottom', fancybox=True)
        self.qax2.legend(loc='best', fancybox=True)
        print(data_reset.head())
        
    def clear_axes(self):
        for _ax in self.axes:
            _ax.clear()

    def _get_df(self, product):
        if product in FUTURES:
            str_start = '%s-%s-%s' % list(map(int, self.start_date_entry.get().split('-')))
            df = quandl.get(FUTURES[product], start_date=str_start)
        else:
            dt_start = dt.datetime(*list(map(int, self.start_date_entry.get().split('-'))))
            dt_end = dt.datetime(*list(map(int, self.end_date_entry.get().split('-'))))
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

    def get_fundamental_data(self):
        data = yahoo_fundamental_scraper(self.ticker.get())
        data = Series(data)
        self.fstats.delete(1.0, tk.END)
        self.fstats.insert(tk.END, '%s fundamentals: \n' % self._xs)
        self.fstats.insert(tk.END, data)
        return data

    def _init_candles(self):
        self._xs = self.ticker.get()
        self.xs = self._get_df(self._xs)
        self.x_col= self._get_column_names()
        self.clear_axes()
        
    def geometric_returns(self, rets):
        geo_rets = reduce(lambda x, y: x * y, map(lambda x: x + 1, rets)) ** (1 / len(rets))
        return (geo_rets - 1) * 100
        
    def plot_candles(self, mavgs=[7, 14, 28, 55, 125]):
        self._init_candles()
        self.fundamentals = fundamentals = self.get_fundamental_data()
        self.fig.suptitle('%s: $%s' % (self._xs, self.xs['Adj Close'][-1]))

        ts = list(map(lambda x: x.timestamp(), self.xs.index))
        dts = list(map(lambda x: dt.datetime.fromtimestamp(x), ts))
        
        candles = list(zip(ts, self.xs.Open, self.xs.High, self.xs.Low, self.xs.Close))
        
        # Calculations
        rets = self.xs['Adj Close'].pct_change()
        std_rets = rets.std()
        mwindow = self.xs.Close.rolling(window=int(self.std))
        mavg = mwindow.mean()
        stds = 2 * self.xs.Close.rolling(window=int(self.std)).std()
        vol = self.xs['Adj Close'].pct_change().rolling(window=3).std()
        rsi = self.relative_strength_index()
        log_xs = self.xs['Adj Close'].apply(np.log)
        log_xs_rets = log_xs.pct_change().dropna()
        geo_rets = self.geometric_returns(rets.dropna())
        
        self.ax.set_ylabel('price') 
        self.ax.set_xticklabels(dts, rotation=25)
        self.ax.xaxis.set_visible(False)
        
        self.ax1.set_ylim([0, self.xs['Volume'].max()*4])
        self.ax1.set_ylabel('volume')
        
        self.ax3.set_title('%s - %s' % (dts[0], dts[-1]))
        
        # Candlesticks
        candlestick_ohlc(self.ax, candles, width=100000, colorup='g', colordown='r')
            
        if self.enable_bbands.get():
            self.ax.plot(ts, mavg - stds, ':', color='grey', alpha=0.5)                         
            self.ax.plot(ts, mavg + stds, ':', color='grey', alpha=0.5,
                         label='adj close: %s\navg returns: %s\nstd returns: %s' % (
                                self.xs.ix[-1]['Adj Close'], round(geo_rets, 2), round(std_rets, 2)))
        
        self.ax1.fill_between(ts, self.xs['Volume'], alpha=0.1, color='b',
                              label='Beta: %s\nRev: %s\nP/E: %s\nMkt Cap: %s\nFwd P/E: %s\nAvg 10-Day Vol: %s' % (
                              fundamentals['Beta '], fundamentals['Revenue (ttm)'], 
                              fundamentals['Trailing P/E '], fundamentals['Market Cap (intraday) 5'],
                              fundamentals['Forward P/E 1'], fundamentals['Avg Vol (10 day) 3']))
        
        self.ax2.fill_between(ts, vol, alpha=0.5, color='grey', label='mstd returns')
        
        self.ax3.plot(ts, rsi, label='rsi', alpha=0.5)
        self.ax3.axhline(30, linewidth=0.5,  alpha=0.25)
        self.ax3.axhline(70, linewidth=0.5, alpha=0.25)
        self.sax.hist(rets.dropna(), label='avg rets: %s' % round(geo_rets, 2), bins=100)
        
        self.sax1.fill_between(ts, mwindow.std(), label='mstd prices', alpha=0.75)
        
        self.sax2.plot(ts, log_xs, label='log prices')
        
        self.sax3.fill_between(log_xs_rets.index, log_xs_rets, label='log returns', alpha=0.75)
        
        for _ax in self.axes:
            _ax.grid(False)
            _ax.legend(loc='best', fancybox=True)
            _ax.xaxis.set_major_formatter(self.formatter)
            _ax.yaxis.set_major_formatter(self.formatter)
  

if __name__ == '__main__':
    root = tk.Tk()
    app = EquityMarketAnalysisGUI(root)
    app.mainloop()
