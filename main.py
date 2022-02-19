def readAlloc():
    file = open("allocation.csv", "r")
    arr = file.read().split("\n")
    arr.pop(0)
    for i in range(len(arr)):
        arr[i] = arr[i].split(",")
    return arr

alloc = readAlloc()

import ccxt

from info import APIKEY, SECRET

binance = ccxt.binance({
    'apiKey': APIKEY,
    'secret': SECRET,
    'enableRateLimit': True
})
binance.loadMarkets()

#prezzo = binance.fetchTicker("BTC/USDT")["last"] 

allcoins = binance.fetch_balance()['total']
owned = [coin for coin, balance in allcoins.items() if balance > 0]
balance = 0
for coin in alloc:
    pair = coin[0] + "/USDT"
    balance += binance.fetchTicker(pair)["last"]*allcoins[coin[0]]
balance += allcoins["USDT"]
print("Total balance: " + str(balance) + " USDT")

def update():
    allcoins = binance.fetch_balance()['total']
    owned = [coin for coin, balance in allcoins.items() if balance > 0]
    balance = 0
    for coin in owned:
        pair = coin + "/USDT"
        balance += binance.fetchTicker(pair)["last"]*allcoins[coin]

def getSMA(pair, days):
    candles = binance.fetch_ohlcv(pair, '1d')
    sum = 0
    for i in range(len(candles)-days, len(candles)):
        sum += candles[i][4]
    return sum/days

def getUSDTEquivalent(coin, amount):
    return binance.fetchTicker(coin + "/USDT")["last"]*amount

import logging as log
log.raiseExceptions = False

from datetime import datetime as dt
log.basicConfig(filename='example.log', encoding='utf-8', level=log.INFO)

end = False
pause = False

### bot
exec(open("bot_manager.py").read())
### bot

def logAll(message):
    d = dt.now()
    out = str(d) + ' ' + message
    print(out)
    log.info(out)
    bot.send_message(TRUSTED_ID, str(d) + '\n✅✅\n' + message)

logAll("Process started.")

import time

while(not end): 
    if balance < 1 or pause:
        update()
        time.sleep(2)
        if end:
            break
        continue

    for coin in alloc:
        update()

        #verifica prezzi
        pair = coin[1]
        ind = 0
        if(coin[0] == "BTC" or coin[0] == "ETH"): #for BTC and ETH consider sma50, 35, 20. For altcoin consider sma20, 10, 5
            sma20 = getSMA(pair, 20)
            sma35 = getSMA(pair, 35)
            sma50 = getSMA(pair, 50)
            if sma50 < sma20:
                ind += 1
            if sma50 < sma35:
                ind += 1
        else:
            sma5 = getSMA(pair, 5)
            sma10 = getSMA(pair, 10)
            sma20 = getSMA(pair, 20)
            if sma20 < sma5:
                ind += 1
            if sma20 < sma10:
                ind += 1
        
        price = float(binance.fetchTicker(coin[0] + "/USDT")["last"])
        market = binance.market(pair)
        
        percentage = getUSDTEquivalent(coin[0], allcoins[coin[0]])*100/balance
        if ind == 2:  #if highest sma is down both lower smas
            if percentage < int(coin[2]):
                missingPerc = int(coin[2])-percentage
                missing = missingPerc*balance/100
                if allcoins["USDT"] > missing:
                    if extra > market["limits"]["amount"]["min"]:
                        #buy missing
                        message = str(missing/price) + ' ' + coin[0] + " bought for " + missing + " USDT."
                        binance.createMarketBuyOrder(pair, missing/price)
                        logAll(message)
                else:
                    message = "Can't buy " + str(missing/price) + ' ' + coin[0] + ", insufficient USDT balance."
                    print(message)
                    #logAll(message)
        if ind == 1:  #if highest sma is between lower smas
            if percentage < int(coin[2])/2:  #buy missing percentage
                missingPerc = int(coin[2])/2-percentage
                missing = missingPerc*balance/100
                if allcoins["USDT"] > missing:
                    if extra > market["limits"]["amount"]["min"]:
                        #buy missing
                        message = str(missing/price) + ' ' + coin[0] + " bought for " + missing + " USDT."
                        binance.createMarketBuyOrder(pair, missing/price)
                        logAll(message)
                else:
                    message = "Can't buy " + str(missing/price) + ' ' + coin[0] + ", insufficient USDT balance."
                    print(message)
                    #logAll(message)
            else:  #sell extra
                extraPerc = percentage-int(coin[2])/2
                extra = extraPerc*balance/100
                if extra > market["limits"]["amount"]["min"]:
                    #sell extra
                    message = str(extra/price) + ' ' + coin[0] + " sold for " + str(extra) + " USDT."
                    binance.createMarketSellOrder(pair, extra/price)
                    logAll(message)
        if ind == 0:
            if allcoins[coin[0]] > market["limits"]["amount"]["min"]:
                #sell all
                usdeq = getUSDTEquivalent(coin[0], allcoins[coin[0]])
                message = str(allcoins[coin[0]]) + ' ' + coin[0] + " sold for " + str(usdeq) + " USDT."
                binance.createMarketSellOrder(pair, allcoins[coin[0]])
                logAll(message)
    end = True

logAll("Process killed.")
bot.stop_polling()