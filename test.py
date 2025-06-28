from defs import *

coin = "ADAUSDT"

symInfo = client.futures_exchange_info()
symData = []

for i in symInfo["symbols"]:
    if i["symbol"] == coin:
        symData = i["filters"]

rv_price, rv_quantity = round_value_quantity(symData)

new_symInfo = pd.DataFrame([{'symbol': coin, 'rvp': rv_price, 'rvq': rv_quantity}])

print(new_symInfo)