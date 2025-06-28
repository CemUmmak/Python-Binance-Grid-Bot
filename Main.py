from defs import *
from orders_price import calculate_orders_price
from open_orders import send_new_orders
from first_positions import open_first_positions
import os

check = get_data_from_google_sheets("kamber")


# Sunucu zamanını al ve zaman farkını hesapla
"""def get_time_offset():
    server_time = client.futures_time()['serverTime']
    local_time = int(time.time() * 1000)
    return server_time - local_time"""


"""# Zaman farkını başlangıçta bir kez hesapla
time_offset = get_time_offset()"""


# Zaman farkını periyodik olarak güncellemek için bir fonksiyon
"""def update_time_offset():
    global time_offset
    time_offset = get_time_offset()
"""

settings = pd.read_excel("Data/settings.xlsx")

timeOffsetCheck = 0

while check:

    """timeOffsetCheck += 1

    if timeOffsetCheck > 5:
        update_time_offset()
        timeOffsetCheck = 0"""

    settings = pd.read_excel("Data/settings.xlsx")

    for index in range(len(settings)):

        # Set Block List
        blocklist = pd.read_csv('blocklist.csv')

        # Settings
        coin = settings.iloc[index]['coin'].upper()
        size = int(settings.iloc[index]['ilkPozisyon'])
        order_gap = float(settings.iloc[index]['ordermesafesi'])
        order_size1 = float(settings.iloc[index]['orderboyutu1'])
        order_chance = float(settings.iloc[index]['orderdegistir'])
        order_size2 = float(settings.iloc[index]['orderboyutu2'])
        order_count = int(settings.iloc[index]['orderadeti'])
        target_percent = float(settings.iloc[index]['hedefyuzdesi'])
        trade = settings.iloc[index]['trade'].lower()
        go_step_two = float(settings.iloc[index]['ikiposizyonarasimesafe'])
        step_two = True if settings.iloc[index]['stepiki'].lower() == "yes" else False
        long_high_distance = float(settings.iloc[index]['pozisyonfiyatarasimesafe'])
        exit_point = float(settings.iloc[index]['stopuzakligi'])
        fifth_reset = True if settings.iloc[index]['5.adımResetleme'].lower() == "yes" else False
        profitStop = True if settings.iloc[index]['KarAlıncaDur'].lower() == "yes" else False
        reverseOrderGap = float(settings.iloc[index]['TersIslemOrderAraligi'])
        reverseOrderDolar1 = float(settings.iloc[index]['TersIslemDolar1'])
        reverseOrderDolar2 = float(settings.iloc[index]['TersIslemDolar2'])
        # reOrder = float(settings.iloc[index]['OrderDizYeniden'])

        if os.path.exists(f"Data/Coin/{coin}.csv"):
            Step2Data = pd.read_csv(f"Data/Coin/{coin}.csv", index_col=False)
        else:
            Step2Data = [{"Highest": 0.0, "Lowest": 999999.0, "Step5Long": False,
                          "Step5Short": False, "OrderChance": False}]
            Step2Data = pd.DataFrame(Step2Data)

        if trade != "yes" or coin in blocklist['coin'].values:
            continue

        multup = (1 + (order_gap / 100))
        multdn = (1 - (order_gap / 100))

        # Set Symbol Round Level
        rv_price, rv_quantity = set_round_level(coin)

        long_size, short_size, cur_profit, total_margin, target_profit = 1.0, 1.0, 0.0, 0.0, 0.0
        distance_between_2_positions, mark_price, long_price, short_price = 0.0, 0.0, 0.0, 0.0

        try:
            # Check Positions / Get Positions Info
            positions = client.futures_position_information()
            positions = pd.DataFrame(positions)
            positions = positions.loc[positions.symbol == coin].reset_index()

            long_size = float(positions["positionAmt"][0])
            short_size = abs(float(positions["positionAmt"][1]))
            total_margin = abs(float(positions["notional"][0])) + abs(float(positions["notional"][1]))
            total_margin = total_margin if total_margin > 0 else 1
            cur_profit = round(float(positions["unRealizedProfit"][0]) + float(positions["unRealizedProfit"][1]), 2)
            target_profit = round(total_margin / 100 * target_percent, 2)
            mark_price = float(positions["markPrice"][0])
            long_price = float(positions["entryPrice"][0])
            short_price = float(positions["entryPrice"][1])

            if long_size > 0 and short_size > 0:
                distance_between_2_positions = abs(round((long_price - short_price) / long_price * 100, 2))

        except Exception as Exp:
            tele_print("Check Positions Error " + str(Exp))

        # Open First Positions
        if not long_size and not short_size:
            open_first_positions(coin, size, rv_quantity)
            continue

        try:
            # There is Only One Position
            if (not long_size and short_size) or (long_size and not short_size):
                tele_print("The open position is closing. Orders will be reset.")

                close_all(coin, short_size, long_size)
                time.sleep(3)
                close_all(coin, short_size, long_size)

                continue

        except Exception as Exp:
            tele_print("Error while closing for only one order" + str(Exp))

        # There are Two Positions
        if long_size and short_size:

            try:
                # Check Profit
                if cur_profit > target_profit > 0:
                    close_all(coin, short_size, long_size)

                    tele_print("Profit" + coin)

                    Step2Data.loc[0, "Step5Long"] = False
                    Step2Data.loc[0, "Step5Short"] = False
                    Step2Data.loc[0, "OrderChance"] = False

                    if profitStop:
                        new_coin = pd.DataFrame([[coin]], columns=['coin'])
                        new_coin.to_csv('blocklist.csv', mode='a', header=False, index=False)

                    time.sleep(3)
                    close_all(coin, short_size, long_size)
                    continue

            except Exception as Exp:
                tele_print("Error while check profit" + str(Exp))

            #  Calculate orders price
            buy_count, sell_count, buy_price, sell_price, min_buy_order_price, max_sell_order_price, openOrders = (
                calculate_orders_price(coin, order_count))

            # Set Order Size
            longDif = is_difference_percent_threshold(long_price, mark_price, order_chance)
            shortDif = is_difference_percent_threshold(short_price, mark_price, order_chance)

            if longDif or shortDif:
                order_size = order_size2
                reverseOrderDolar = reverseOrderDolar2

                if Step2Data.loc[0, "OrderChance"]:
                    close_all(coin, 0, 0, True)
                    Step2Data.loc[0, "OrderChance"] = True
            else:
                order_size = order_size1
                reverseOrderDolar = reverseOrderDolar1

            # Set New Orders After Distance
            """if reOrder > 0 and len(openOrders) > 0:
                openOrders['price'] = pd.to_numeric(openOrders['price'], errors='coerce')
                openOrders['stopPrice'] = pd.to_numeric(openOrders['stopPrice'], errors='coerce')

                openOrders['order_price'] = openOrders['price'].where(openOrders['price'] > 0, openOrders['stopPrice'])

                uporders = openOrders[openOrders['order_price'] > long_price]
                dnorders = openOrders[openOrders['order_price'] < short_price]

                up = uporders['order_price'].min() if not uporders.empty else 0
                dn = dnorders['order_price'].max() if not dnorders.empty else 0

                longDif = is_difference_percent_threshold(up, short_price, reOrder) if up > 0 else False
                shortDif = is_difference_percent_threshold(dn, long_price, reOrder) if dn > 0 else False

                price_difference = abs(dn - long_price)
                percentage_difference = (price_difference / short_price) * 100

                print("Dif :", percentage_difference)


                if longDif:
                    tele_print("Yeni orderlar dizildi 1")
                    gap = order_gap * short_price / 100
                    gap = int(abs(short_price - up) / gap)

                    orderPrice = short_price

                    for i in range(int(gap / 2)):
                        orderPrice *= multup

                        qty = round(order_size / orderPrice, rv_quantity)

                        order2 = client.futures_create_order(symbol=coin, side="SELL", type="STOP_MARKET",
                                                             quantity=str(qty),
                                                             positionSide="SHORT",
                                                             stopPrice=round(sell_price * multup, rv_price),
                                                             timestamp=int(time.time() * 1000 + time_offset),
                                                             recvWindow=60000)


                        if reverseOrderGap > 0 and reverseOrderDolar > 0:
                            buyPrice = orderPrice * (1 - reverseOrderGap / 100)
                            qty = round(reverseOrderDolar / buyPrice, rv_quantity)

                            # Sell limit emrini oluşturuyoruz
                            order = client.futures_create_order(
                                symbol=coin,
                                side="BUY",
                                type="LIMIT",
                                quantity=str(qty),
                                price=round(buyPrice, rv_price),
                                positionSide="LONG",
                                timeInForce="GTC",  # "GTC" (Good-Til-Canceled), zaman sınırı ekleyin
                                timestamp=int(time.time() * 1000 + time_offset),
                                recvWindow=60000
                            )
                            print_order_details(order)


                if shortDif:
                    tele_print("Yeni orderlar dizildi 2", False)
                    gap = order_gap * long_price / 100
                    gap = int(abs(long_price - dn) / gap)

                    orderPrice = long_price

                    for i in range(int(gap / 2)):
                        orderPrice *= multdn
                        print(orderPrice)
                        qty = round(order_size / orderPrice, rv_quantity)

                        order = client.futures_create_order(symbol=coin, side="BUY", type="STOP_MARKET", quantity=str(qty),
                                                            positionSide="LONG",
                                                            stopPrice=round(orderPrice, rv_price),
                                                            timestamp=int(time.time() * 1000 + time_offset),
                                                            recvWindow=60000)

                        if reverseOrderGap > 0 and reverseOrderDolar > 0:
                            sellprice = orderPrice * (1 + reverseOrderGap / 100)
                            qty = round(reverseOrderDolar / sellprice, rv_quantity)

                            # Sell limit emrini oluşturuyoruz
                            order = client.futures_create_order(
                                symbol=coin,
                                side="SELL",
                                type="LIMIT",
                                quantity=str(qty),
                                price=round(sellprice * multdn, rv_price),
                                positionSide="SHORT",
                                timeInForce="GTC",  # "GTC" (Good-Til-Canceled), zaman sınırı ekleyin
                                timestamp=int(time.time() * 1000 + time_offset),
                                recvWindow=60000
                            )"""


            # Open Orders
            if buy_price > 0 and sell_price > 0:
                send_new_orders(buy_count, sell_count, buy_price, sell_price, multup,
                                rv_price, rv_quantity, multdn, coin, order_size,
                                reverseOrderGap, reverseOrderDolar)
            try:
                # secont step
                if step_two and distance_between_2_positions > go_step_two:

                    # Calculate Highest and Lowest Point
                    if mark_price > Step2Data.loc[0, "Highest"] and mark_price > long_price:
                        Step2Data.loc[0, "Highest"] = mark_price
                    elif mark_price < long_price:
                        Step2Data.loc[0, "Highest"] = 0

                    if mark_price < Step2Data.loc[0, "Lowest"] and mark_price < short_price:
                        Step2Data.loc[0, "Lowest"] = mark_price
                    elif mark_price > short_price:
                        Step2Data.loc[0, "Lowest"] = 999999.0

                    if Step2Data.loc[0, "Lowest"] != 999999.0:
                        LowTrigger = (abs(Step2Data.loc[0, "Lowest"] - short_price) / Step2Data.loc[0, "Lowest"] * 100
                                      > long_high_distance)

                        if (LowTrigger and mark_price > short_price * (1 - (exit_point / 100))
                                and short_size > long_size * 1.10):

                            qty = round(short_size - long_size, rv_quantity)

                            if qty > 0:
                                order1 = client.futures_create_order(symbol=coin, side="BUY", type='MARKET',
                                                                     quantity=str(qty),
                                                                     positionSide="LONG",
                                                                     #timestamp=int(time.time() * 1000 + time_offset),
                                                                     recvWindow=60000)
                                print(order1)
                                tele_print("Sync Amount")
                                Step2Data[0, "Step5short"] = True
                                time.sleep(0.5)
                                close_all(coin, 0, 0, True)

                    if Step2Data.loc[0, "Highest"] != 0:
                        HighTrigger = (abs(Step2Data.loc[0, "Highest"] - long_price) / Step2Data.loc[0, "Highest"] * 100
                                       > long_high_distance)

                        if (HighTrigger and mark_price < long_price * (1 + (exit_point / 100))
                                and long_size > short_size * 1.10):

                            qty = round(long_size - short_size, rv_quantity)

                            if qty > 0:
                                order1 = client.futures_create_order(symbol=coin, side="SELL", type='MARKET',
                                                                     quantity=str(qty),
                                                                     positionSide="SHORT",
                                                                     #timestamp=int(time.time() * 1000 + time_offset),
                                                                     recvWindow=60000)
                                print(order1)
                                tele_print("Sync Amount")
                                time.sleep(0.5)
                                Step2Data.loc[0, "Step5Long"] = True
                                close_all(coin, 0, 0, True)

                if fifth_reset:
                    if Step2Data.loc[0, "Step5Long"] and mark_price < long_price:
                        close_all(coin, 0, 0, True)
                        Step2Data.loc[0, "Step5Long"] = False
                        tele_print("Step 5 Reset")

                    if Step2Data.loc[0, "Step5Short"] and mark_price > short_price:
                        close_all(coin, 0, 0, True)
                        Step2Data.loc[0, "Step5Short"] = False
                        tele_print("Step 5 Reset")

            #    -    -    -    -    -    -    -    -    -    -    -    -    -    -

            except Exception as Exp:
                tele_print("Secont Step Error " + str(Exp))

        Step2Data.to_csv(f"Data/Coin/{coin}.csv", index=False)
        time.sleep(0.5)
        print(get_time_now(), coin, "Target :", str(target_profit) + "$ ", "Profit :", cur_profit)
    time.sleep(5)
