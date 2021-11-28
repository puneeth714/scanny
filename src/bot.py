from __future__ import print_function, unicode_literals
from sys import stderr
from time import sleep, time
from colorama import Fore, Back, Style
from timeit import default_timer as timer
from pyfiglet import Figlet
import threading
import concurrent.futures
import asyncio
import os
import json
import yaml
import math
import time
import subprocess

# Binance API Helper - https://github.com/sammchardy/python-binance.git
from binance.client import Client,BinanceAPIException

# SQLite3 to save local records of trades
import sqlite3

# Connect to records.db database
conn = sqlite3.connect('records.db')
c = conn.cursor()

# Import user config and instantiate variables
conf_import = "conf.yaml"
secrets = "secrets-binance.yaml"
coin = None
config = None

# Switched to .yaml as it offers commenting and other features
#It shouldn't be an issue for speed as dict is loaded into memory
with open(conf_import, "r") as conf_file:
    config = yaml.safe_load(conf_file)

# Open secret.json, retrieve keys and place in config dictionary
with open(secrets, "r") as secrets_file:
    api_keys = yaml.safe_load(secrets_file)

config['api_key'] = api_keys['api_key']
config['api_secret'] = api_keys['api_secret']

#print(config)

# Command Line interface prompts for PyInquirer
question1 = [
    {
        'type': 'list',
        'name': 'trade_conf',
        'message': 'Please select trade configuration?',
        'choices': list(config["trade_configs"].keys()),
    }
]
question2 = [
    {
        'type': 'input',
        'name': 'coin',
        'message': 'Please enter coin for Pump?',
    }
]
question3 = [
    {
        'type': 'confirm',
        'name': 'continue',
        'message': 'Do you wish to proceed?',
        'default': True,
    }
]

# Show crypto-bot banner
def show_header():
     
    fig = Figlet(font='slant')
    print(fig.renderText('scanny'))

# Binance API Helper Debug mode
def debug_mode(client):
    # client.ping()
    time_res = client.get_server_time()
    print("Server Time: {}".format(time_res["serverTime"]))
    
    status = client.get_system_status()
    print("System Status: {}".format(status["msg"]))

# Get account balance for "pairing" in config before trade
def acct_balance(send_output=False):
    acct_balance = client.get_asset_balance(asset=config['trade_configs']
                                                [selected_config]['pairing'])
        
    print('\nYour {} balance is {}\n'.format(config['trade_configs'][selected_config]['pairing'], acct_balance['free']))
    print(Fore.YELLOW + 'Please ensure Config is correct before proceeding\n' + Fore.RESET)

    if config['trade_configs'][selected_config]['pairing'] == 'BTC':
        if float(acct_balance['free']) < 0.001:
            print(Fore.RED + 'Binance requires min balance of 0.001 BTC for trade\n' + Fore.RESET)
    else:
        print(Fore.RED + 'A min balance is often required for trade on Binance\n' + Fore.RESET)

    return acct_balance

# Get account balance for "pairing" in config after trade
def acct_balance2(send_output=False):
    acct_balance = client.get_asset_balance(asset=config['trade_configs']
                                                [selected_config]['pairing'])
        
    print('\nYour {} balance after trading is {}\n'.format(config['trade_configs'][selected_config]['pairing'], acct_balance['free']))

    difference = acct_balance['free'] - balance['free']
    percentage = (difference/balance) * 100

    if float(acct_balance['free']) < balance:
        
        print(Fore.YELLOW + 'A {:.2f}% loss\n'.format(percentage) + Fore.RESET)

    if float(acct_balance['free']) > balance:
        
        print(Fore.GREEN + 'A {:.2f}% gain\n'.format(percentage) + Fore.RESET)

    return acct_balance

def pump_duration(start_time, end_time):
    time_delta = end_time - start_time
    time_delta = round(time_delta, 2)
    print(f"Time elapsed for pump is {time_delta}s\n")

# Get available trading amount with user config
def trading_amount():
    return (
        float(balance['free'])
        * config['trade_configs'][selected_config]['buy_qty_from_wallet']
    )

# Execute market order - buy and/or sell
def market_order(client, selected_coin_pair, order_type, coin_pair_info, balance):
    try:
        if order_type == 'buy':
            avail_trading_amount = trading_amount()
            current_price = client.get_symbol_ticker(symbol=selected_coin_pair)
            buy_qty = math.floor(avail_trading_amount / float(current_price['price']))
            order = client.order_market_buy(symbol=selected_coin_pair, quantity=buy_qty)
            return order

        elif order_type == 'sell':
            #This here is a potential bottle neck and may introduce delays
            coin_balance = client.get_asset_balance(asset=selected_coin.upper())
            # print(coin_balance)
            # current_price = client.get_symbol_ticker(symbol=selected_coin_pair)
            # print(current_price)
            # sell_qty = math.floor(coin_balance * float(current_price['price']))
            sell_qty = math.floor(float(coin_balance['free']) * config['trade_configs'][selected_config]['sell_qty_from_wallet'])
            order = client.order_market_sell(symbol=selected_coin_pair, quantity=sell_qty)
            return order
    except BinanceAPIException as e:
        print(Fore.RED + '\nBinance API error\n' + Fore.RESET)
        print(e)
        print(Fore.RED + '\nExiting\n' + Fore.RESET)
        exit(1)

# Displays order details asynchronously - see 'main' block
def display_order_details(order):
    return json.dumps(order, sort_keys=True, indent=4)

# Check user configs margin in to sell order
async def check_margin():

    global pending_sell_order
    margin = config['trade_configs'][selected_config]['profit_margin']

    fallback_task = asyncio.create_task(fallback_action())

    while True:
        # avg_price = client.get_avg_price(symbol=selected_coin_pair)
        current_price = client.get_symbol_ticker(symbol=selected_coin_pair)
        # print(current_price)
        # print(current_price['price'])
        try:
            if float(current_price['price']) >= (buy_order['fills'][0]['price'] * (1.0 + margin)):
                if pending_sell_order is None:
                    pending_sell_order = market_order(client, selected_coin_pair, 'sell', coin_pair_info, balance)
                    break
            else:
                await asyncio.sleep((config['trade_configs'][selected_config]['refresh_interval']/1000))
        except:
            pass

        if pending_sell_order:
            break

    return pending_sell_order

async def fallback_action():

    global pending_sell_order

    await asyncio.sleep((config['trade_configs'][selected_config]['sell_fallback_timeout_ms']/1000))
    if pending_sell_order is None:
        pending_sell_order = market_order(client, selected_coin_pair, 'sell', coin_pair_info, balance)

# Save orders to local db asynchronously
def insert_into_db(order):
    
    c.execute("INSERT INTO Orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            ("Binance", order['clientOrderId'], order['orderId'], order['fills'][0]['tradeId'], 
                order['symbol'], order['type'], order['side'], order['timeInForce'],
                order['transactTime'], order['fills'][0]['commissionAsset'],
                order['fills'][0]['price'], order['fills'][0]['commission'],
                order['fills'][0]['qty'], order['cummulativeQuoteQty']))
    
    conn.commit()

async def main():

    coin_pair_info = client.get_symbol_info(selected_coin_pair)

    start_time = time.time()
    buy_order=None
    buy_order = market_order(client, selected_coin_pair, 'buy', coin_pair_info, balance)

    # Execution using threading
    with concurrent.futures.ThreadPoolExecutor() as executor:
        
        #Print buy order details
        buy_order_details = executor.submit(display_order_details, buy_order)
        print('\n' + buy_order_details.result() + '\n')

        sell_order = await check_margin()

    end_time = time.time()
    sell_order_details = display_order_details(sell_order)
    print('\n' + sell_order_details + '\n')

    insert_into_db(order=buy_order)
    insert_into_db(order=sell_order)

    conn.close()

    balance2 = acct_balance2()
    pump_duration(start_time, end_time)


if __name__ == 'src.bot':

    show_header()
    client = Client(config["api_key"], config["api_secret"])
    if config['debug_mode']:
        debug_mode(client=client)
        print('\n')

    print(Fore.YELLOW + '-- Binance Edition --\n' + Fore.RESET)

    #Question1
    # answer1 = Inquirer.prompt(question1)
    selected_config ='market-trade-one'#answer1['trade_conf']

    #Retrieve current coin balance here
    balance = acct_balance()

    type_of_execution=input("Do you want to use telegram(1) or detector(2)= ")
    if type_of_execution=="2":
        # execute="src/detect_binance_api.py"
        # # os.system(execute)
        # a=subprocess.Popen([execute],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # selected_coin=a.communicate()[0].decode().replace("\n","")
        import src.detect_binance_api as detect
        selected_coin= detect.start()
        print(selected_coin)
    #Question2
    # answer2 = Inquirer.prompt(question2)
    elif type_of_execution=="1":
        # execute1=config["python_path"]
        # execute2="src/detect_telegram.py"
        # # os.chdir("/home/puneeth/programmes/others/bot/tmp/binance-pump-bot-main/python")
        # # os.system(execute1+" "+execute2)
        # a=subprocess.Popen([execute1,execute2],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # selected_coin = a.communicate()[0].decode().replace("\n","")
        import src.detect_telegram as detect
        detect.client.start()
        detect.client.run_until_disconnected()
        selected_coin=detect.coin
        print(selected_coin)
        #print(selected_coin)

        # os.chdir("/home/puneeth/programmes/others/bot/tmp/simple-pump-and-dump-bot-master/src/")
    #Coin Pair
    else:
        print("you selected nothing selected one of (1,2)")
        exit()
    selected_coin_pair = selected_coin.upper() + \
                            config['trade_configs'][selected_config]['pairing']
    print(selected_coin_pair)
    buy_order = None
    coin_pair_info = None
    pending_sell_order = None

    asyncio.run(main())
if KeyboardInterrupt:
    print("ended")