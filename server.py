import asyncio
import websockets
import os
import json

async def handler(websocket):
    # fsdf
    pass

async def broadcast(message, id):
    # sending a message to a customer or restaurant
    pass

async def main():
    try: 
        async with websockets.serve(handler, host="", port=os.environ.get('PORT', 8000)):
            await asyncio.Future()  # run forever
    except:
        print("closed out")


if __name__ == "__main__":
    asyncio.run(main())