
api_id = "8599861"
api_hash = "67ab00243e8d9d67466192c76e0b6b11"

# # Here you define the target channel that you want to listen to:
# user_input_channel = 'https://t.me/superalgoscommunity'



# #listen to messages
# @client.on(events.NewMessage(chats=user_input_channel))
# async def newMessageListener(event):
#     #get message text
#     newMessage=event.message.message

# with client:
#     client.run_until_disconnected()



import asynchat
from lib2to3.pgen2.token import NEWLINE
from operator import index
from pydoc import cli
from telethon import TelegramClient, events, sync

# Remember to use your own values from my.telegram.org!
coin=""
client = TelegramClient('initial', api_id, api_hash)

@client.on(events.NewMessage(incoming=True,outgoing=False))
async def my_event_handler(event):
    
    
    if "#" in event.raw_text:

        string1=event.raw_text
        a=string1.index("#")

        may_be_coin=event.raw_text[a+1:a+5]
        # print(may_be_coin[:may_be_coin.find("\n")])
        # print(may_be_coin)
        # return(may_be_coin)
        global coin
        coin=may_be_coin[:may_be_coin.find("\n")]
        await client.disconnect()
        # return may_be_coin[:may_be_coin.find("\n")]
# client.start()
# client.run_until_disconnected()