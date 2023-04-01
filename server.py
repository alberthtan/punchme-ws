import asyncio
import websockets
import os
import jwt
import datetime
import json

RESTAURANTS = dict() # {restaurant_id: websocket, ...}
CUSTOMERS = dict() # {customer_id: websocket, ...}

async def handler(websocket, path):
    try:
        # Extract the access token from the headers of the websocket request
        token = websocket.request_headers.get("access_token")
        if not token:
            raise ValueError("Missing access token")

        # Verify and decode the JWT
        payload = jwt.decode(token, os.environ.get("SECRET_KEY_WS"), algorithms=['HS256'])

        # Extract the user information from the payload
        id = payload.get("id")
        role = payload.get("role")
        timestamp_unformatted = payload.get("timestamp")
        if id is None or role is None or timestamp_unformatted is None:
            raise ValueError("Missing information")
        
        timestamp = datetime.datetime.fromtimestamp(timestamp_unformatted)

        # Check if the timestamp is within the past one minute of the current time
        now = datetime.datetime.now()
        if timestamp < now - datetime.timedelta(minutes=1):
            raise ValueError("Token expired")

        if role == "CUSTOMER":
            await handle_customer(websocket, id)
        elif role == "RESTAURANT":
            await handle_restaurant(websocket, id)
        else:
            raise ValueError("Missing role")

    except Exception as e:
        # Handle authentication errors and other exceptions
        print(f"Error: {e}")
        await websocket.close()

     # WEBSOCKET CLOSES
    finally:
        # Remove the WebSocket from the appropriate dictionary
        if role == "CUSTOMER":
            CUSTOMERS.pop(id, None)
            print("customers clean up")
            print(CUSTOMERS)
        elif role == "RESTAURANT":
            RESTAURANTS.pop(id, None)
            print("restaurants clean up")
            print(RESTAURANTS)

async def handle_customer(websocket, id):
    # Handle the websocket connection for a customer
    
    CUSTOMERS[id] = websocket

    async for websocket_message in websocket:
        message = json.loads(websocket_message)

        if "restaurant_id" in message:
            restaurant_websocket = RESTAURANTS.get("restaurant_id")
            if restaurant_websocket:
                json_message = json.dumps({"message": "scanned"})
                try:
                    await restaurant_websocket.send(json_message)
                except websockets.ConnectionClosed:
                    pass


async def handle_restaurant(websocket, id):
    # Handle the websocket connection for a restaurant
    
    RESTAURANTS[id] = websocket

    async for websocket_message in websocket:
        message = json.loads(websocket_message)

        if "customer_id" in message:
            customer_websocket = CUSTOMERS.get("customer_id")
            if customer_websocket:
                json_message = json.dumps({"message": "scanned"})
                try:
                    await customer_websocket.send(json_message)
                except websockets.ConnectionClosed:
                    pass

async def main():
    try: 
        async with websockets.serve(handler, host="", port=os.environ.get('PORT', 8000)):
            await asyncio.Future()  # run forever
    except:
        print("closed out")

if __name__ == "__main__":
    asyncio.run(main())