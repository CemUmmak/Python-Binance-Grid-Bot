from defs import *


def open_first_positions(coin, size, rv_quantity):
    try:
        ticker = client.get_symbol_ticker(symbol=coin)
        last_price = float(ticker['price'])

        qty = round(size / last_price, rv_quantity)

        if qty > 0:
            order1 = client.futures_create_order(symbol=coin, side="SELL", type='MARKET', quantity=str(qty),
                                                 positionSide="SHORT",
                                                 # timestamp=int(time.time() * 1000 + time_offset),
                                                 recvWindow=60000)
            order2 = client.futures_create_order(symbol=coin, side="BUY", type='MARKET', quantity=str(qty),
                                                 positionSide="LONG",
                                                 # timestamp=int(time.time() * 1000 + time_offset),
                                                 recvWindow=60000)

            print_order_details(order1)
            print_order_details(order2)
            time.sleep(0.5)
    except Exception as Exp:
        tele_print("Error while opening first positions " + str(Exp))
