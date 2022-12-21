import asyncio
import json
import os
import traceback
from websockets import connect
import time
from datetime import datetime

class tx_item:
    def __init__(self):
        self.arrival_time = time.time()
        self.hangup_time = 0.0
        self.is_removed = False
        self.tx_detail = None

def get_tx_dict_json():
    output = {}
    for key in tx_dict:
        output[key] = tx_dict[key].__dict__
    return output

# Listen to new pending transaction event
async def listen_to_event():
    async with connect("ws://jeju.andrew.cmu.edu:8647") as ws:
        await ws.send(json.dumps({"jsonrpc": "2.0", "id": "listen", "method": "eth_subscribe", "params": ["newPendingTransactions"]}).encode('utf-8'))
        subscription_response = await ws.recv()
        print(subscription_response)
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=60)
                new_tx = json.loads(message)
                tx_dict[new_tx['params']['result']] = tx_item()
                pass
            except Exception as e:
                print(traceback.format_exc())
                pass

# Poll transaction pool every second
async def poll_txpool():
    while True:
        async with connect("ws://jeju.andrew.cmu.edu:8647", max_size=1_000_000_000) as ws:
            try:
                await ws.send(json.dumps({"jsonrpc":"2.0","id":"1","method":"txpool_content","params":[]}).encode('utf-8'))
                message = await ws.recv()
                txpool = json.loads(message)
            except Exception as e:
                print(traceback.format_exc())
            hash_to_tx = {}
            for sender in txpool['result']['pending']:
                for nonce in txpool['result']['pending'][sender]:
                    tx = txpool['result']['pending'][sender][nonce]
                    hash_to_tx[tx['hash']] = tx

            # Try to find tx we subscribed in txpool
            for hash in tx_dict:
                if tx_dict[hash].is_removed:
                    continue

                tx_dict[hash].hangup_time = time.time() - tx_dict[hash].arrival_time
                if hash in hash_to_tx:
                    if tx_dict[hash].tx_detail is None:
                        tx_dict[hash].tx_detail = hash_to_tx[hash]

                        if hash_to_tx[hash]['from'] not in addr_nonce:
                            addr_nonce[hash_to_tx[hash]['from']] = {
                                hash_to_tx[hash]['nonce']: {'cnt': 1, 'txs': [hash_to_tx[hash]]}
                            }
                        elif hash_to_tx[hash]['nonce'] not in addr_nonce[hash_to_tx[hash]['from']]:
                            addr_nonce[hash_to_tx[hash]['from']][hash_to_tx[hash]['nonce']] = {'cnt': 1, 'txs': [hash_to_tx[hash]]}
                        else:
                            addr_nonce[hash_to_tx[hash]['from']][hash_to_tx[hash]['nonce']]['cnt'] += 1
                            addr_nonce[hash_to_tx[hash]['from']][hash_to_tx[hash]['nonce']]['txs'].append(hash_to_tx[hash])

                else:
                    tx_dict[hash].is_removed = True

            tmp_file = "{}/mempool.json".format(directory, )
            with open(tmp_file, "w") as fd:
                json.dump(txpool, fd, indent=4)

        await asyncio.sleep(0.3)

# Write to disk every minute
async def persistent():
    while True:
        try:
            file = "{}".format(datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d_%H:%M:%S'))
            with open("{}/{}".format(directory, file), "w") as fd:
                json.dump(get_tx_dict_json(), fd, indent=4)

            file = "nonce_{}".format(datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d_%H:%M:%S'))
            with open("{}/{}".format(directory, file), "w") as fd:
                json.dump(addr_nonce, fd, indent=4)
        except Exception as e:
            print(traceback.format_exc())
        await asyncio.sleep(60)

async def timer():
    start_time = time.time()
    while True:
        now = time.time()
        # Collect data for 1 hour
        if now - start_time > 60 * 60:
            exit(0)
        await asyncio.sleep(1)

async def get_all_functions():
    while True:
        e1 = loop.create_task(listen_to_event())
        e2 = loop.create_task(poll_txpool())
        e3 = loop.create_task(persistent())
        e4 = loop.create_task(timer())
        await asyncio.wait([e1, e2, e3, e4])


if __name__ == "__main__":
    # tx map. tx hash => tx_item
    tx_dict = {}

    # from address => nonce => list of tx
    addr_nonce = {}

    # directory to store data
    directory = "data_{}".format(datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    os.mkdir(directory)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all_functions())
