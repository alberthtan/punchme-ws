import asyncio
import websockets
import os
import jwt
import datetime
import json
from urllib.parse import parse_qs, urlparse

RESTAURANTS = dict() # {restaurant_id: websocket, ...}
CUSTOMERS = dict() # {customer_id: websocket, ...}

async def handler(websocket, path):
    role = None
    try:
        # Extract the access token from the query parameters of the websocket request
        query_params = parse_qs(urlparse(path).query)
        token = query_params.get("access_token", [None])[0]
        if not token:
            raise ValueError("Missing access token")

        # Verify and decode the JWT
        payload = jwt.decode(token, os.environ.get("SECRET_KEY_WS"), algorithms=['HS256'])
        expiration_time = datetime.datetime.fromtimestamp(payload['exp'])

        if expiration_time < datetime.datetime.now():
            # Token has expired
            raise ValueError("Token expired")

        # Extract the user information from the payload
        id = payload.get("id")
        role = payload.get("role")
        if id is None or role is None:
            raise ValueError("Missing user information")

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
    print("connecting customer with id: " + str(id))
    
    CUSTOMERS[id] = websocket

    async for websocket_message in websocket:
        message = json.loads(websocket_message)

        if "restaurant_id" in message:
            restaurant_websocket = RESTAURANTS.get(message["restaurant_id"])
            if restaurant_websocket:
                json_message = json.dumps({"scanned": True})
                try:
                    await restaurant_websocket.send(json_message)
                except websockets.ConnectionClosed:
                    pass


async def handle_restaurant(websocket, id):
    # Handle the websocket connection for a restaurant
    print("connecting restaurant with id: " + str(id))

    RESTAURANTS[id] = websocket

    async for websocket_message in websocket:
        message = json.loads(websocket_message)

        if "customer_id" in message:
            customer_websocket = CUSTOMERS.get(message["customer_id"])
            if customer_websocket:
                json_message = json.dumps({"scanned": True})
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