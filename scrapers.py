from bs4 import BeautifulSoup
import requests

def yahoo_fundamental_scraper(stock):
    url = 'https://finance.yahoo.com/quote/%s/key-statistics' % stock
    params = {'p': stock}
    req = requests.get(url, params=params)
    text = req.text.encode('ascii', 'ignore').decode() # remove strange unicode chars
    soup = BeautifulSoup(text, 'lxml')
    html_table = soup.find_all('tbody')
    html_ratios = html_table[-1] # its the last table in the html (could change)
#    with open('output.txt', 'w') as _file:
#        _file.write(text)
    
    data = {}
    counter = 0 #
    for tag in html_table:
        for line in tag:
            tds = line.find_all('td')
            for td in tds:     
                if counter % 2 == 0:
                    cur_name = td.text
                    data[cur_name] = ''
                else:
                    data[cur_name] = td.text
                counter += 1
    return data


if __name__ == '__main__':
    yahoo_fundamental_scraper('AAPL')
