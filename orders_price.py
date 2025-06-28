from defs import *


def calculate_orders_price(coin, order_count):
    """buy_count, sell_count, buy_price, sell_price"""

    buy_price, sell_price, max_sell_stop_price, min_buy_stop_price = 0.0, 0.0, 0.0, 0.0

    try:
        # Calculate Orders Price
        open_orders = client.futures_get_open_orders()
        open_orders = pd.DataFrame(open_orders)

        if len(open_orders) > 0:
            open_orders = open_orders.loc[open_orders.symbol == coin].reset_index()

        if len(open_orders) > 0:

            buy_stop_count = open_orders[(open_orders['side'] == 'BUY') &
                                         (open_orders['type'] == "STOP_MARKET")].shape[0]

            sell_stop_count = open_orders[(open_orders['side'] == 'SELL') &
                                          (open_orders['type'] == "STOP_MARKET")].shape[0]

            max_buy_stop_price = float(open_orders.loc[(open_orders['type'] == 'STOP_MARKET') &
                                                       (open_orders['side'] == 'BUY'), 'stopPrice'].max())

            min_buy_stop_price = float(open_orders.loc[(open_orders['type'] == 'STOP_MARKET') &
                                                       (open_orders['side'] == 'BUY'), 'stopPrice'].min())

            min_sell_stop_price = float(open_orders.loc[(open_orders['type'] == 'STOP_MARKET') &
                                                        (open_orders['side'] == 'SELL'), 'stopPrice'].min())

            max_sell_stop_price = float(open_orders.loc[(open_orders['type'] == 'STOP_MARKET') &
                                                        (open_orders['side'] == 'SELL'), 'stopPrice'].max())

            buy_count = order_count - buy_stop_count
            sell_count = order_count - sell_stop_count

            buy_price = max_buy_stop_price if buy_stop_count > 0 else 0
            sell_price = min_sell_stop_price if sell_stop_count > 0 else 0
        else:
            positions = client.futures_position_information()
            positions = pd.DataFrame(positions)
            positions = positions.loc[positions.symbol == coin].reset_index()

            long_price = float(positions["entryPrice"][0])
            short_price = float(positions["entryPrice"][1])
            mark_price = float(positions["markPrice"][1])

            buy_count = order_count
            sell_count = order_count

            buy_price = long_price if long_price > mark_price else mark_price
            sell_price = short_price if short_price < mark_price else mark_price

        if not buy_price or not sell_price:
            positions = client.futures_position_information()
            positions = pd.DataFrame(positions)
            positions = positions.loc[positions.symbol == coin].reset_index()

            long_price = float(positions["entryPrice"][0])
            short_price = float(positions["entryPrice"][1])
            mark_price = float(positions["markPrice"][1])

            if not buy_price:
                buy_price = long_price if long_price > mark_price else mark_price
            if not sell_price:
                sell_price = short_price if short_price < mark_price else mark_price

        return buy_count, sell_count, buy_price, sell_price, min_buy_stop_price, max_sell_stop_price, open_orders

    except Exception as Exp:
        tele_print("Error while calculating orders price " + str(Exp))
