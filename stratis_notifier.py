import os, platform, requests, time
import threading
from decimal import *

push_default_timeout = 8000
fomo_threshold = 2
# default is 5 minute cycle
minute_cycle = 30

# define how many decimals we work with
crypto_dec = Decimal(10) ** -8

COLORS = dict(
        list(zip([
            'grey',
            'red',
            'green',
            'yellow',
            'blue',
            'magenta',
            'cyan',
            'white',
            ],
            list(range(30, 38))
            ))
        )

RESET = '\033[0m'

def colorprint(text, color=None):

    now = time.strftime("%d %b %H:%M:%S")

    if color is not None:

        text = '%s: \033[%dm%s' % (now, COLORS[color], text)

    text += RESET

    print(text)

def pushNotification(message, timeout):

    # Determine OS filepaths
    if platform.system() == "Linux":

        if message:
            wrapped = "\"%s\"" % message
            command = "notify-send -a terminal -t %i %s" % (timeout, wrapped)
            os.system(command)

        else:

            print("Empty command was send to pushNotification function")

    # Filepath for windows
    elif platform.system() == "Windows":

        print("windows")

    # Filepath for Mac untested
    elif platform.system() == "Darwin":

        os.system("""osascript -e 'display notification "{}" with title "{}"' """.format(message, "Stratis Notifier"))

    else:

        print("Unable to determine OS")

def getStrat():

    price_history = []
    percent = 0

    while 1:

        try:

            price_list = []

            # Bittrex
            trex_req = requests.get('https://bittrex.com/api/v1.1/public/getmarketsummary?market=btc-strat')
            trex_market_price = Decimal(float(trex_req.json()['result'][0]['Bid'])).quantize(crypto_dec)
            trex_market_price = Decimal(float(trex_req.json()['result'][0]['Bid'])).quantize(crypto_dec)

            # Polo
            polo_req = requests.get('https://poloniex.com/public?command=returnTicker')
            polo_market_price = Decimal(float(polo_req.json()['BTC_STRAT']['highestBid'])).quantize(crypto_dec)
            polo_market_volume = Decimal(float(polo_req.json()['BTC_STRAT']['baseVolume'])).quantize(crypto_dec)

            price_list.append(trex_market_price)
            price_list.append(polo_market_price)

            price_median = Decimal(sum(price_list) / len(price_list)).quantize(crypto_dec)
            volume_total = Decimal(trex_market_price + polo_market_volume).quantize(crypto_dec)

            # Insert at position 0
            price_history.insert(0, price_median)

            # Set default text
            text = "STRAT @ %s" % price_median
            volume = " with a total volume of %s BTC" % volume_total
            term_color = "blue"

            if len(price_history) == 3:

                del price_history[-1]

            elif len(price_history) > 3:

                break

            if len(price_history) == 2:

                percent = ((price_history[0] / price_history[1]) - 1) * 100

            if percent != 0:

                if percent > fomo_threshold:

                    text = "STRAT just jumped %.2f%% to %.8f in the last %i minutes" % (percent, price_median, minute_cycle)
                    term_color = "green"

                elif percent < -fomo_threshold:

                    text = "STRAT just jumped %.2f%% to %.8f in the last %i minutes" % (percent, price_median, minute_cycle)
                    term_color = "red"

            else:

                None

            colorprint(text + volume, term_color)
            pushNotification(text, push_default_timeout)

        except (requests.exceptions.ConnectionError) as e:

            print(e)

        # Query markets every x minutes
        time.sleep(60 * minute_cycle)

def main():

    hw_thread = threading.Thread(target = getStrat)
    hw_thread.daemon = True
    hw_thread.start()

    try:

        while 1:

            time.sleep(3600)

    except KeyboardInterrupt:
        print ("\nGoodbye!")

if __name__ == "__main__":

    main()
