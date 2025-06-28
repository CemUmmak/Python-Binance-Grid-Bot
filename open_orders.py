from defs import *


def send_new_orders(buy_count, sell_count, buy_price, sell_price, multup, rv_price,
                    rv_quantity, multdn, coin, order_size, reverse_order_gap, reverse_order_dolar):

    try:
        # Open Stop Orders
        for i in range(buy_count):

            qty = round(order_size / buy_price, rv_quantity)

            order = client.futures_create_order(symbol=coin, side="BUY", type="STOP_MARKET", quantity=str(qty),
                                                 positionSide="LONG",
                                                 stopPrice=round(buy_price * multup, rv_price),
                                                #timestamp=int(time.time() * 1000 + time_offset),
                                                recvWindow=60000)

            print_order_details(order)

            if reverse_order_gap > 0 and reverse_order_dolar > 0:
                sellprice = buy_price * (1 + reverse_order_gap / 100)
                qty = round(reverse_order_dolar / sellprice, rv_quantity)

                print(round(sellprice, rv_price))
                # Sell limit emrini oluşturuyoruz
                order = client.futures_create_order(
                    symbol=coin,
                    side="SELL",
                    type="LIMIT",
                    quantity=str(qty),
                    price=round(sellprice, rv_price),
                    positionSide="SHORT",
                    timeInForce="GTC",  # "GTC" (Good-Til-Canceled), zaman sınırı ekleyin
                    #timestamp=int(time.time() * 1000 + time_offset),
                    recvWindow=60000
                )
                print_order_details(order)
            buy_price *= multup

        for i in range(sell_count):

            qty = round(order_size / sell_price, rv_quantity)

            order2 = client.futures_create_order(symbol=coin, side="SELL", type="STOP_MARKET",
                                                 quantity=str(qty),
                                                 positionSide="SHORT",
                                                 stopPrice=round(sell_price * multdn, rv_price),
                                                 #timestamp=int(time.time() * 1000 + time_offset),
                                                 recvWindow=60000)

            print_order_details(order2)

            if reverse_order_gap > 0 and reverse_order_dolar > 0:
                buyPrice = sell_price * (1 - reverse_order_gap / 100)
                qty = round(reverse_order_dolar / buyPrice, rv_quantity)

                # Sell limit emrini oluşturuyoruz
                order = client.futures_create_order(
                    symbol=coin,
                    side="BUY",
                    type="LIMIT",
                    quantity=str(qty),
                    price=round(buyPrice, rv_price),
                    positionSide="LONG",
                    timeInForce="GTC",  # "GTC" (Good-Til-Canceled), zaman sınırı ekleyin
                    #timestamp=int(time.time() * 1000 + time_offset),
                    recvWindow=60000
                )
                print_order_details(order)
            sell_price *= multdn

    except Exception as Exp:
        tele_print("Error while sending stop orders" + str(Exp))
