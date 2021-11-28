#!/usr/bin/env python3
#Detects price action(change) of a coin each time it is called for a specificied difference
import binance
import time
import os
from sys import argv
start_value = []
coins = binance.Client()
n = 0
start_time_0 = time.time()


def start():
    """start() is the starting point into the process 
    default no log into files"""
    a=analysis()
    
    if not a:

        yes_or_no = input(
            "Do you want to remove existing log files\n analysis.txt and timing_analysis.txt\n")
        remove_log(yes_or_no,a)
        print("starting : ")
    timing_analysis(time.time(),"at_first",a)
    # time_start=time.time()
    global coins, n
    while True:
        # print(coins.get_ticker())
        tickers_list_of_dict = coins.get_all_tickers()
        if n == 0:
            start_value = tickers_list_of_dict
            # coins_filter = get_coins("BTC", start_value)
        make = value_change(tickers_list_of_dict, start_value,a)
        if make is not None:
            return make
        write_file(formater(make,a),a)
        n = n+1
        # print(n)
    


# list coins with btc pair
def get_coins(quote, start_value):
    btc_list = []
    n = 0
    for symbols in start_value:
        if quote in symbols['symbol']:
            # a="BTC"
            # a.index("BTC")==1
            if symbols['symbol'].index(quote) == 0:
                continue
            btc_list.insert(n, symbols['symbol'])
            n += 1
    return(btc_list)


def value_change(tickers, start_value,boolean):
    values_to_send = []
    start_time_1 = time.time()
    for i in range(len(tickers)):
        start_time_2 = time.time()
        each_symbol_present = tickers[i]
        if "BTC" not in each_symbol_present['symbol'][-3:]:
            continue
        each_symbol_start = start_value[i]
        change_percent = (float(each_symbol_present['price'])-float(
            each_symbol_start['price']))*100/float(each_symbol_present['price'])
        if each_symbol_present['symbol'] != each_symbol_start['symbol']:
            print("check code something didn't go well :/")
            break
        if change_percent > float(argv[1]):
            timing_analysis(time.time()-start_time_0, " overall process",boolean)
            return each_symbol_present['symbol'][:-3]
        if boolean:
            continue
        change = time.time()-start_time_2
        values_to_send.append("change in value of " + each_symbol_start['symbol'] + " is = "+str(
            change_percent)+" % "+"executed in  {}".format(change))
        timing_analysis(change, " for each ticker check",boolean)
    if boolean:
        return
    timing_analysis(time.time()-start_time_1, " for all tickers check",boolean)

    return values_to_send


def just_one_coin():
    it_is = coins.get_ticker(symbol=input("enter the symbol = ").upper())
    print(it_is)


def write_file(input,boolean):
    if boolean:
        return
    with open("detect.txt", "a") as f:
        global n
        if n == 0:
            f.write("starting at "+str(time.time())+"\n")
        f.write(input)


def formater(listis,boolean) -> str:
    if boolean:
        return
    string_is = ""
    for each in listis:
        if string_is is None:
            continue
        string_is = string_is+"\n"+each
    return string_is


def timing_analysis(time_diff, stringin,boolean):
    if boolean:
        return
    f = open("timing_analysis.txt", "a")
    global n
    # bug here
    # if str(n) == "0" and stringin != " for all tickers check" and stringin != " for each ticker check":
    if stringin=="at_first":
        f.write("starting at "+str(time.time())+"\n")

    # f.write("starting at "+str(time.time())+"\n")
    elif stringin == " overall process":
        f.write(str(time_diff)+stringin+"\n")
        f.close()
    elif stringin == " for all tickers check":
        f.write("   "+str(time_diff)+stringin+"\n")
        f.close()
    elif stringin == " for each ticker check":
        f.write("           "+str(time_diff)+stringin+"\n")
        f.close()
    else:
        print("error in timing_analysis stringin didn't match :/")
        exit()


def remove_log(yes_or_no,boolean):
    if boolean:
        return
    if yes_or_no != "1":
        return

    if "timing_analysis.txt" not in os.listdir() or "detect.txt" not in os.listdir():
        print("one of the files is not present in the current working directory\n")
        print("let me create one\n")
        return
    else:
        os.remove("timing_analysis.txt")
        os.remove("detect.txt")


# need to work with logging level of program output

def debug_level(val,boolean)->str:
    return val
def analysis() -> bool:
    """default is no log into console i.e no analysis if wanted set first arg as 1"""
    # print(len(argv))
    if len(argv) == 2 or argv[2] == str(1):
        return True
    elif argv[2] == str(0):
        return False
    else:
        print("check args")
        exit("arg error")

def latency_detect(times):
    c=0
    start0= time.time()
    for _ in range(int(times)):
        start1=time.time()
        coins.get_all_tickers()
        c=(c+time.time()-start1)/2
    print("Time is "+str(c)+ " for geting all ticker values on average")
    print("Total time is "+str(time.time()-start0)+" for getting all ticker values {} times".format(times))
        
# start()


# just_one_coin()
# if KeyboardInterrupt:
#     timing_analysis.

# latency_detect(20)
