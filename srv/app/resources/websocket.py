import falcon
import falcon.asgi
import falcon.media
from app.resources.middleware import UserByTokenMiddleware


# Мы подключаемся к сервису
class SubscribeResource:
    def __init__(self, storage):
        self.storage = storage

    def on_get(self, req, resp):
        pass

    def on_websocket(self, req, ws):
        ws.accept()
        ws.send_media({'message': f'Hello, {name}'})

        print(ws.subprotocols)

        ws.close()

        """
        # Reject it?
        if some_condition:
            # If close() is called before accept() the code kwarg is
            #   ignored, if present, and the server returns a 403
            #   HTTP response without upgrading the connection.
            await ws.close()
            return



        # If, after examining the connection info, you would like to accept
        #   it, simply call accept() as follows:
        try:
            await ws.accept(subprotocol='wamp')
        except WebSocketDisconnected:
            return

        # Simply start sending messages to the client if this is an event
        #   feed endpoint.
        while True:
            try:
                event = await my_next_event()

                # Send an instance of str as a WebSocket TEXT (0x01) payload
                await ws.send_text(event)

                # Send an instance of bytes, bytearray, or memoryview as a
                #   WebSocket BINARY (0x02) payload.
                await ws.send_data(event)

            except WebSocketDisconnected:
                # Do any necessary cleanup, then bail out
                return

        # ...or loop like this to implement a simple request-response protocol
        while True:
            try:
                # Use this if you expect a WebSocket TEXT (0x01) payload,
                #   decoded from UTF-8 to a Unicode string.
                payload_str = await ws.receive_text()

                # Or if you are expecting a WebSocket BINARY (0x02) payload,
                #   in which case you will end up with a byte string result:
                payload_bytes = await ws.receive_data()

                # Or if you want to get a serialized media object (defaults to
                #   JSON deserialization of text payloads, and MessagePack
                #   deserialization for BINARY payloads, but this can be
                #   customized via app.ws_options.media_handlers).
                media_object = await ws.receive_media()

            except WebSocketDisconnected:
                # Do any necessary cleanup, then bail out
                return
            except TypeError:
                # The received message payload was not of the expected
                #   type (e.g., got BINARY when TEXT was expected).
                pass
            except json.JSONDecodeError:
                # The default media deserializer uses the json standard
                #   library, so you might see this error raised as well.
                pass

            # At any time, you may decide to close the websocket. If the
            #   socket is already closed, this call does nothing (it will
            #   not raise an error.)
            if we_are_so_done_with_this_conversation():
                # https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent
                await ws.close(code=1000)
                return


        # ...or run a couple of different loops in parallel to support
        #  independent bidirectional message streams.

        messages = collections.deque()

        async def sink():
            while True:
                try:
                    message = await ws.receive_text()
                except falcon.WebSocketDisconnected:
                    break

                messages.append(message)

        sink_task = falcon.create_task(sink())

        while not sink_task.done():
            while ws.ready and not messages and not sink_task.done():
                await asyncio.sleep(0)

            try:
                await ws.send_text(messages.popleft())
            except falcon.WebSocketDisconnected:
                break

        sink_task.cancel()
        try:
            await sink_task
        except asyncio.CancelledError:
            pass
        """

class HelloResource:
    async def on_get(self, req, resp):
        resp.media = {'message': f'Hello!'}

    async def on_websocket(self, req, ws, name):
        try:
            await ws.accept()
            await ws.send_media({'message': f'Hello, {name}'})

            while True:
                payload = await ws.receive_text()
                print(f'Received: [{payload}])')
        except falcon.WebSocketDisconnected:
            pass