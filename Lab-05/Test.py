import json
import os
import multichain

######################################Server Connection############################
rpcuser = "multichainrpc"
rpcpassword = "4Eaxwaw8HVn1cpNUDoCuHh695gwZcWWhiNtB4KN1miY4"
rpchost = "127.0.0.1"
rpcport = "9244"
chainname = "test"
mc=multichain.MultiChainClient(rpchost, rpcport, rpcuser, rpcpassword)
result = mc.getaddresses()
print(result)
txid = mc.create('stream', 'Shahbazcoin1', True)
result = mc.liststreams()
result2=mc.subscribe(['stream', 'Shahbazcoin1']) 
result = mc.getstreaminfo('Shahbazcoin1')
print(result2)
txid = mc.publish('Shahbazcoin1', 'key1', {'json' : {'Coinname' : 'Shahbaz', 'amount' : 30}}) # JSON data

print(txid)
result2 = mc.liststreamkeyitems('Shahbazcoin1','key1')
print(result2)

