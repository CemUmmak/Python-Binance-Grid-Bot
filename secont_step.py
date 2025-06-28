import os

from defs import *


def secont_stepp(coin, distance_between_2_positions, mark_price, long_price, short_price,
                 long_high_distance, exit_point, short_amt, long_amt, rvq, close_percent,
                 reset_order_after_stop, equalize_after_stop):

    # read or create csv
    if os.path.exists(f"Data/Coin/{coin}.csv"):
        data = pd.read_csv(f"Data/Coin/{coin}.csv", index_col=False)
    else:
        data = [{
            "Coin": coin,
            "Dif": distance_between_2_positions,
            "LastPrice": mark_price,
            "LongPrice": long_price,
            "ShortPrice": short_price,
            "MaxHigh": 0.0,
            "MinLow": 999999.0,
            "ExitPoint": 0.0,
            "lastClose": "-"
        }]
        data = pd.DataFrame(data)

    # set new data
    data.loc[0, "Dif"] = distance_between_2_positions
    data.loc[0, "LastPrice"] = mark_price
    data.loc[0, "LongPrice"] = long_price
    data.loc[0, "ShortPrice"] = short_price

    # find max high
    if data.loc[0, "LastPrice"] > data.loc[0, "LongPrice"]:
        if data.loc[0, "LastPrice"] > data.loc[0, "MaxHigh"]:
            data.loc[0, "MaxHigh"] = data.loc[0, "LastPrice"]
    else:
        data.loc[0, "MaxHigh"] = 0

    # find min low
    if data.loc[0, "LastPrice"] < data.loc[0, "ShortPrice"]:
        if data.loc[0, "LastPrice"] < data.loc[0, "MinLow"]:
            data.loc[0, "MinLow"] = data.loc[0, "LastPrice"]
    else:
        data.loc[0, "MinLow"] = 999999

    # find long exit point
    if data.loc[0, "MaxHigh"] > 0:
        distance_between_long_maxhigh = abs(round((data.loc[0, "LongPrice"] - data.loc[0, "MaxHigh"]) /
                                                  data.loc[0, "LongPrice"] * 100, 2))

        # price went up calculate exit point
        if distance_between_long_maxhigh > long_high_distance:
            data.loc[0, "ExitPoint"] = long_price + (long_price * exit_point / 100)

        # close position
        if data.loc[0, "LastPrice"] < data.loc[0, "ExitPoint"] > 0:
            if long_amt > short_amt:
                tele_print("Close Buy Order")

                close_amaunt = abs(round(long_amt - (short_amt / 100 * close_percent), rvq))

                close_all(coin, 0, close_amaunt, reset_order_after_stop)

                data.loc[0, "ExitPoint"] = 0
                data.loc[0, "MaxHigh"] = 0
                data.loc[0, "lastClose"] = "buy"

    # find short exit point
    elif data.loc[0, "MinLow"] != 999999:
        distance_between_short_minlow = abs(round((data.loc[0, "ShortPrice"] - data.loc[0, "MinLow"]) /
                                                  data.loc[0, "ShortPrice"] * 100, 2))

        # price went dn calculate exit point
        if distance_between_short_minlow > long_high_distance:
            data.loc[0, "ExitPoint"] = short_price - (short_price * exit_point / 100)

        # close position
        if data.loc[0, "LastPrice"] > data.loc[0, "ExitPoint"] > 0:
            if short_amt > long_amt:
                tele_print("Close Sell Order")

                close_amaunt = abs(round(short_amt - (long_amt / 100 * close_percent), rvq))

                close_all(coin, close_amaunt, 0, reset_order_after_stop)

                data.loc[0, "ExitPoint"] = 0
                data.loc[0, "MinLow"] = 999999
                data.loc[0, "lastClose"] = "sell"

    # sync amount short order
    if equalize_after_stop:
        if (long_amt > short_amt * 1.10 and data.loc[0, "LastPrice"] > data.loc[0, "LongPrice"]
                and data.loc[0, "lastClose"] == "sell"):

            qty = round(long_amt - short_amt, rvq)

            if qty > 0:
                order1 = client.futures_create_order(symbol=coin, side="SELL", type='MARKET', quantity=str(qty),
                                                     positionSide="SHORT")
                print(order1)
                tele_print("Sync Amount")
                data.loc[0, "lastClose"] = "sync sell"
                time.sleep(0.5)
                close_all(coin, 0, 0, True)

        # sync amount long order
        if (short_amt > long_amt * 1.10 and data.loc[0, "LastPrice"] < data.loc[0, "ShortPrice"]
                and data.loc[0, "lastClose"] == "buy"):

            qty = round(short_amt - long_amt, rvq)

            if qty > 0:
                order1 = client.futures_create_order(symbol=coin, side="BUY", type='MARKET', quantity=str(qty),
                                                     positionSide="LONG")
                print(order1)
                tele_print("Sync Amount")
                data.loc[0, "lastClose"] = "sync buy"
                time.sleep(0.5)
                close_all(coin, 0, 0, True)

    print(data)
    data.to_csv(f"Data/Coin/{coin}.csv", index=False)
    time.sleep(0.5)
