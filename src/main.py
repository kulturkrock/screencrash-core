import asyncio
import base64
import json
import os.path
import websockets

with open(os.path.join("resources", "script.pdf"), mode="rb") as f:
    pdf_content = f.read()
script = base64.b64encode(pdf_content).decode("utf-8")
nodes = {
    "11": {
        "next": "160",
        "prompt":
        "Jag har hört att han är dömd att segla de sju haven för alltid i en fruktlös jakt på sin älskade!",
        "pdfPage": 2,
        "pdfLocationOnPage": 0.6,
    },
    "160": {
        "next": "1126",
        "prompt": "Ja, då var vi av med honom!",
        "pdfPage": 8,
        "pdfLocationOnPage": 0.4,
    },
    "1126": {
        "next": "11",
        "prompt": "Vad är tårtan till?",
        "pdfPage": 48,
        "pdfLocationOnPage": 0.48,
    },
}
history = ["1126"]


async def socket_listener(websocket, path):
    # Handshake
    await websocket.send(json.dumps({"messageType": "nodes", "data": nodes}))
    await websocket.send(json.dumps({"messageType": "history", "data": history}))
    await websocket.send(json.dumps({"messageType": "script",
                                     "data": f"data:application/pdf;base64,{script}"}))
    # Listen for messages
    async for message in websocket:
        message_dict = json.loads(message)
        message_type = message_dict["messageType"]
        if message_type == "next-node":
            current_node = nodes[history[-1]]
            history.append(current_node["next"])
            await websocket.send(json.dumps({"messageType": "history", "data": history}))
        else:
            print(f"WARNING: Unknown message type {message_type}")


async def serve():
    async with websockets.serve(socket_listener, "localhost", 8001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print('Exiting')
