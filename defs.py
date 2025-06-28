from binance import Client
import pandas as pd
import telebot
import datetime
import time
import requests


# pandas show all rows / colomns
pd.set_option('display.max_rows', 1000)
pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 1000)
pd.set_option('display.precision', 4)
pd.set_option('display.float_format', '{:.6f}'.format)

api = pd.read_csv("Data/api.csv", header=None)

binanceApi = api[1][0]
binanceSecret = api[1][1]
telegramBot = api[1][2]
telegramChat = api[1][3]

client = Client(binanceApi, binanceSecret)


def get_data_from_google_sheets(name):
    try:
        google_sheets_url = "https://docs.google.com/spreadsheets/d/1-YpvtUu_0HixzbNE3YgT4BeXk4hFTW2ZQ7XnHL7htmo/export?format=csv&range=A:B"

        # Google Sheets'ten veriyi çek
        df = pd.read_csv(google_sheets_url)

        for i in df.values:
            nameSheed = str(i[0]).lower().strip()
            permise = str(i[1]).lower().strip()

            if nameSheed == name.lower() and permise == "yes":
                print(f"{name} robotu lisanslı")
                return True
        print(f"{name} robotu lisanslı değil. Yazılımcı ile iletişime geçin")
        return False
    except Exception as e:
        print("Veri alınırken hata oluştu:", e)
        return False


def get_last_telegram_message():

    result = requests.get(f"https://api.telegram.org/bot{telegramBot}/getUpdates?offset=-1&limit=1&chat_id={telegramChat}").json()
    if result["ok"]:
        messages = result["result"]
        if messages:
            last_message = messages[0]["message"]
            if "text" in last_message:
                return last_message["text"]
            else:
                return "No text found."
        else:
            return "No messages found."
    else:
        return "Request failed."


def round_value_quantity(symbol_info):
    try:
        minPrice = ""
        minQty = ""
        for i in symbol_info:
            if "minPrice" in i:
                minPrice = i["minPrice"]
            if "minQty" in i:
                minQty = i["minQty"]
            if len(minPrice) > 0 and len(minQty) > 0:
                break


        print("Min Price ", minPrice)
        return find_round_value(minPrice), find_round_value(minQty)
    except Exception as Exp:
        print(Exp)


def find_round_value(string_number):
    count = -1

    for i in string_number:
        if i == ".":
            count = 0
        elif count >= 0:
            count += 1

    return count if count >= 0 else 0


def print_order_details(order):

    # İşlem bilgilerini temizleme ve yazdırma
    print(" ")
    print("Alınan varlık:", order['symbol'])
    print("Alınan miktar:", order['origQty'])
    print("Toplam maliyet (USDT):", order['cumQuote'])
    print("İşlem türü:", order['type'])


def accont_hedge_mode(hedge_mode=True):
    try:
        client.futures_change_position_mode(dualSidePosition="true" if hedge_mode else "false")
        print("Account position mode has been chanced to Hedge Mode")
        time.sleep(0.1)
    except Exception as Exp:
        print("Account already in Hedge Mode", "  ", Exp)


def set_leverage(coin, cross=True, leverage=20):

    new_margin_type = "CROSSED" if cross else "ISOLATED"

    try:
        client.futures_change_margin_type(symbol=coin, marginType=new_margin_type)
        time.sleep(0.1)
    except Exception as Exp:
        print("Account already in ", new_margin_type, "  ", Exp)

    try:
        client.futures_change_leverage(symbol=coin, leverage=leverage)
        time.sleep(0.1)
    except Exception as Exp:
        print("Account already in ", new_margin_type, "  ", Exp)


def tele_print(message, telegram=True):
    print(message)
    if telegram:
        try:
            telebot.TeleBot(telegramBot).send_message(telegramChat, message)
        except Exception as Exp:
            print(Exp)
    time.sleep(5)


def get_time_now():
    """
    Only return hour,minute,secont

    :return 12:20:36 -> string
    """
    time2 = str(datetime.datetime.now())
    time2 = time2.split(" ")
    time2 = time2[1].split(".")
    return time2[0]


def close_all(coin, short_size, long_size, close_orders=True):
    try:
        if short_size > 0:
            client.futures_create_order(symbol=coin, side="BUY", type='MARKET',
                                        positionSide="SHORT", quantity=short_size)
        if long_size > 0:
            client.futures_create_order(symbol=coin, side="SELL", type='MARKET',
                                        positionSide="LONG", quantity=long_size)
        if close_orders:
            open_orders = client.futures_get_open_orders()
            open_orders = pd.DataFrame(open_orders)

            if len(open_orders) > 0:
                client.futures_cancel_all_open_orders(symbol=coin)

    except Exception as Exp:
        tele_print("Error from close all" + str(Exp))


def set_round_level(coin):
    symInfo = pd.read_csv("Data/symInfo.csv")

    if coin in symInfo['symbol'].values:
        row = symInfo[symInfo['symbol'] == coin].iloc[0]
        rv_price = row['rvp']
        rv_quantity = row['rvq']
    else:
        symInfo = client.futures_exchange_info()
        symData = []

        for i in symInfo["symbols"]:
            if i["symbol"] == coin:
                symData = i["filters"]

        rv_price, rv_quantity = round_value_quantity(symData)

        new_symInfo = pd.DataFrame([{'symbol': coin, 'rvp': rv_price, 'rvq': rv_quantity}])

        new_symInfo.to_csv("Data/symInfo.csv", mode="a", index=False, header=False)

    return rv_price, rv_quantity

def is_difference_percent_threshold(price1, price2, threshold_percent):
    price_difference = abs(price1 - price2)
    percentage_difference = (price_difference / price2) * 100
    return percentage_difference > threshold_percent
