import websockets
import datetime
import matplotlib.pyplot as plt
import requests
import pandas as pd
import seaborn as sns
import json
import asyncio


symbol="btcusdt"
data=pd.DataFrame()
last=0
last_msg_time=0
ws_rec=False

fig, ax = plt.subplots()
ax.set_xlabel("Price")
ax.set_ylabel("Quantity")

plt.show(block=False)
LVLS_SAVE=50
FILENAME=f"binance_ob_{symbol}.csv"
def on_message_ob(message):
  
    message=json.loads(message)
    global last,ws_rec
    u=message["u"]
    U=message["U"]
    
    if (not ws_rec and U<=last+1 and u>=last+1) or (ws_rec and U==last+1):
        ws_rec=True
        last=u
        last_msg_time=str(datetime.datetime.now())
        frames = {side: pd.DataFrame(data=message[side], columns=["price", "quantity"],
                             dtype=float)
          for side in ["b", "a"]}
        frames_list = [frames[side].assign(side=side) for side in frames]
        data_up= pd.concat(frames_list, axis="index", 
                    ignore_index=True, sort=True)
        
        global data
        #data.update(data_up)
        data= (pd.concat([data, data_up])
        .drop_duplicates(["price"] , keep='last')
        .reset_index(drop=True))
       # print("upd")
       # sort_ob_print(data_up)
        data = data.drop(data[data['quantity'] < 0.0001].index)
       # print_price_summary()


def on_message(ws, message):
    print()
    print(str(datetime.datetime.now()) + ": ")
    print(message)


def on_error(ws, error):
    print(error)

def on_close(close_msg):
    print("### closed ###" + close_msg)

async def get_orderbook_snap():
    #print("get ob")
    url="https://api.binance.com/api/v3/depth"
    
    limit = 1000

    params = {"symbol": str.upper(symbol), "limit": limit}

    response = requests.get(url, params=params)
 
    if response.status_code == 200:
        ob = response.json()
        # Now 'data' contains the response from the Binance API
        obside_dict={
        "b": "bids",
         "a":"asks"
        }
        frames = {side: pd.DataFrame(data=ob[obside_dict[side]], columns=["price", "quantity"],
                                dtype=float)
            for side in ["b", "a"]}
        frames_list = [frames[side].assign(side=side) for side in frames]
        global data,last
        last=ob["lastUpdateId"]
        data= pd.concat(frames_list, axis="index", 
                    ignore_index=True, sort=True)
        sort_ob_print(data)
        # print(data)
        
        return(data)
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return(response.text)

def print_price_summary():
    price_summary = data.groupby("side").price.describe()
    print(price_summary)

def save_ob(lvls):
    df_bids = data.loc[data['side'] == "b"].sort_values(by='price', ascending=False)
    df_asks = data.loc[data['side'] == "a"].sort_values(by='price')
    pd.concat([df_asks.head(lvls).iloc[::-1],df_bids.head(lvls)]).to_csv(FILENAME, index=False, mode='a',header=False)
    

def sort_ob_print(data=data):
    df_bids = data.loc[data['side'] == "b"].sort_values(by='price', ascending=False)
    df_asks = data.loc[data['side'] == "a"].sort_values(by='price')
    print(df_bids.head(10))
    print(df_asks.head(10))
    print("============")


async def handle_ob():
    
    
    
    while(True):
        
        if(ws_rec):
            sort_ob_print(data)
            save_ob(LVLS_SAVE)

        await asyncio.sleep(1)
async def plot_ob():
    
    
    
    while(True):
        print("plot")
        if(ws_rec):
            
            t=str(datetime.datetime.now())
            
            ax.set_title(f"Last update: {t} (ID: {last})")

            sns.scatterplot(x="price", y="quantity", hue="side", data=data, ax=ax)
            # sns.histplot(x="price", hue="side",  data=data, ax=ax)
            # sns.rugplot(x="price", hue="side", data=data, ax=ax)
            

            # fig.canvas.draw()
            # fig.canvas.flush_events()
            plt.show(block=False)
            plt.pause(0.1)

            # plt.show(block=False)
            # plt.pause(0.05)
        await asyncio.sleep(1)
    
# async def stream_ob(currency):
#     print("stream ob")
#     websocket.enableTrace(False)
#     socket = f'wss://stream.binance.com:9443/ws/{currency}@depth'
#     #print(socket)
#     ws = websocket.WebSocketApp(socket,
#                                 on_message=on_message_ob,
#                                 on_error=on_error,
#                                 on_close=on_close)
 
    
#     await ws.run_forever()
   
async def stream_ob(currency):
    print("stream ob")
    uri = f'wss://stream.binance.com:9443/ws/{currency}@depth'
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            # Handle received message
            on_message_ob(message)
#     print("stream ob")
#     websocket.enableTrace(False)
#     socket = f'wss://stream.binance.com:9443/ws/{currency}@depth'
#     #print(socket)
#     ws = websocket.WebSocketApp(socket,
#                                 on_message=on_message_ob,
#                                 on_error=on_error,
#                                 on_close=on_close)
 
    
#     await ws.run_forever()

# def streamKline(currency, interval):
#     ob= get_orderbook_snap()
#     #websocket.enableTrace(False)
#     socket = f'wss://stream.binance.com:9443/ws/{currency}@kline_{interval}'
#     ws = websocket.WebSocketApp(socket,
#                                 on_message=on_message,
#                                 on_error=on_error,
#                                 on_close=on_close)

#     ws.run_forever()


async def main():
    # Schedule three calls *concurrently*:
     
     await asyncio.gather(
         stream_ob(symbol),
         get_orderbook_snap(),
         handle_ob(),
         
        
    )
    

asyncio.run(main())
#stream_ob("btcusdt")
#streamKline(symbol, '1m')
#print(get_orderbook_snap())
