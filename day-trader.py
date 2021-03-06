import yfinance as yf
import pickle
import options_scraper

class Trader:
    """
    Simulates a trader. Initialized with name, money, and portfolio.
    Can buy, sell, short sell, and short cover stocks. using the function below.
    """
    def __init__(self, name, money):
         self.name = name
         self.portfolio = Portfolio(name)
         self.money = money
         all_traders.append(self)

    def buy(self, stock_name, quantity, price):
        assert self.money >= quantity*price, "Insufficient funds to place order"
        self.money -= quantity*price
        for pos in self.portfolio:
            if pos.name is stock_name and type(pos) != Short:
                pos.add(quantity)
                return
        newPosition = Position(stock_name, quantity)
        self.portfolio.append(newPosition)

    def sell(self, stock_name, quantity, price):
        self.money += quantity*price
        for pos in self.portfolio:
            if pos.name is stock_name:
                pos.subtract(quantity)

    def market_order_buy(self, stock_name, quantity):
        """
        Buy some quantity of a stock for the market ask price at or below the current
        ask size.
        """
        ask_offer = get_ask_offer(stock_name, True)
        assert quantity <= ask_offer[1], 'Quantity desired ({0}) is greater than ask size ({1})'.format(quantity, ask_offer[1])
        self.buy(stock_name, quantity, ask_offer[0])

    def market_order_sell(self, stock_name, quantity):
        """
        Sell some quantity of a stock for the market bid price at or below the current
        bid size.
        """
        bid_offer = get_bid_offer(stock_name, True)
        assert quantity <= bid_offer[1], 'Quantity desired ({0}) is greater than ask size ({1})'.format(quantity, bid_offer[1])
        self.sell(stock_name, quantity, bid_offer[0])

    def short_sell(self, stock_name, quantity):
        """
        Short sell some quantity of stock for the current bid price at or below the current
        bid size.
        """
        self.money += quantity*get_bid_offer(stock_name, True)[0]
        for pos in self.portfolio:
            if pos.name is stock_name and type(pos) == Short:
                pos.add(quantity)
                return
        newShort = Short(stock_name, quantity)
        self.portfolio.append(newShort)

    def short_cover(self, stock_name, quantity):
        """
        Cover some quantity of stock for the current ask price at or below the current
        ask size.
        """
        long_pos = None
        short_pos = None

        for pos in self.portfolio:
            if pos.name == stock_name and type(pos) == Position:
                long_pos = pos
            if pos.name == stock_name and type(pos) == Short:
                short_pos = pos

        assert (long_pos == None) or (long_pos.quantity >= quantity), 'Not enough stock to cover desired quantity'
        long_pos.subtract(quantity)
        short_pos.subtract(quantity)

class Portfolio:
    """
    Represents a trading portfolio. Current implementation has the portfolio behave
    almost exactly like a Python list, except for some behaviors such as its representation
    """
    def __init__(self, owner):
        self.portfolio_list = []
    def __getitem__(self, index):
        return self.portfolio_list[index]
    def __setitem__(self, index, value):
        self.portfolio_list[index] = value
    def __iter__(self):
        return iter(self.portfolio_list)
    def __next__(self):
        return self.portfolio_list.next()
    def __len__(self):
        return len(self.portfolio_list)
    def append(self, value):
        self.portfolio_list.append(value)
    def extend(self, other_list):
        self.portfolio.extend(other_list)
    def remove(self, value):
        for i in self.portfolio_list:
            if i is value:
                self.portfolio_list.remove(i)
    def __repr__(self):
        return_val = ''
        for pos in self.portfolio_list:
            return_val += str(pos) +'\n'
        return return_val

class Position:
    """
    Represents a basic long position of a security
    """
    updateNeeded = False
    def __init__(self, name, quantity):
        self.name = name
        self.ticker = yf.Ticker(name)
        self.quantity = quantity
    def add(self, amount):
        self.quantity += amount
    def subtract(self, amount):
        self.quantity-=amount
        if self.quantity == 0:
            self.portfolio.remove(self)
    def __repr__(self):
        return str(self.name)+' '+str(self.quantity)

class Short(Position):
    """
    Represents a short position of a security
    """
    def __init__(self, name, quantity):
        super().__init__(name, quantity)
        self.borrow_fee = get_borrowing_fee(name)

class Call(Position):
    """
    Represents a call option
    """
    def __init__(self, name, quantity, expire_date, strike_price):
        super().__init__(name,quantity)
        self.expire_date = expire_date
        self.strike_price = strike_price

class Put(Short):
    """
    Represents a put option
    """
    def __init__(self, name, quantity, expire_date, strike_price):
        super().__init__(name,quantity)
        self.expire_date = expire_date
        self.strike_price = strike_price


def get_borrowing_fee(name):
    return

def get_ask_offer(stock_name, return_values=False):
    info = yf.Ticker(stock_name).info
    if return_values:
        return info['ask'], info['askSize']
    return '${0} x {1}'.format(info['ask'], info['askSize'])

def get_bid_offer(stock_name, return_values=False):
    info = yf.Ticker(stock_name).info
    if return_values:
        return info['bid'], info['bidSize']
    return '${0} x {1}'.format(info['bid'], info['bidSize'])

def get_ask_offer_call(stock_name, expire_date, strike_price, return_values=False):
    data = get_call_data(stock_name, expire_date, strike_price)[1]
    if return_values:
        return data
    return "Current premium is " + data

def get_bid_offer_call(stock_name, expire_date, strike_price, return_values=False):
    data = get_call_data(stock_name, expire_date, strike_price)[0]
    if return_values:
        return data
    return "Current premium is " + data

def get_ask_offer_put(stock_name, expire_date, strike_price, return_values=False):
    data = get_put_data(stock_name, expire_date, strike_price)[1]
    if return_values:
        return data
    return "Current premium is " + data

def get_bid_offer_put(stock_name, expire_date, strike_price, return_values=False):
    data = get_put_data(stock_name, expire_date, strike_price)[0]
    if return_values:
        return data
    return "Current premium is " + data

###################
# Analysis Tools #
##################

"""
Fundamental and technical analysis tools coming in future versions
"""

#######################################
# Saving and loading Trading accounts #
#######################################

all_traders = []
all_file_names = []

def save(trader):
    """
    Saves a trader object into a bytestream using the Python pickle module
    """
    file_name=trader.name+'.p'
    file_path = './pickled_data/'

    if file_name in all_file_names:
        print("A file with the name {0}, would you like to overwrite that file?".format(file_name))
        ans = input("Yes/No: ")
        if ans == 'yes':
            pickle.dump(trader, open(file_path+file_name, 'wb'))
    else:
        pickle.dump(trader, open(file_path+file_name, 'wb'))
        all_file_names.append(file_name)
    pickle.dump(all_file_names, open(file_path+'all_file_names.p', 'wb'))

def load(file_name):
    """
    Returns the trader object contained within a file
    """
    file_path = './pickled_data/'
    return pickle.load(open(file_path+file_name, 'rb'))

####################################
#Loads data from previous sessions #
####################################
if __name__ == '__main__':
    all_file_names = pickle.load(open('./pickled_data/all_file_names.p', 'rb'))
