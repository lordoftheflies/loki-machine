
from __future__ import print_function
import thread
import sys
import threading
import loki_websocket

class WebsocketDataExtractorThread(threading.Thread):
    """
    Thread for sending data to the cloud.
    """

    def __init__(self, queue, stream_url):
        self.queue = queue
        self.stream_url = stream_url

    def on_open(self, ws):
        print("")
        while not self.queue.empty():
            ws.send(self.queue.get())

    def on_message(self, ws, message):
        print(message, file=sys.stdout)

    def on_error(self, ws, error):
        print(error, file=sys.stderr)

    def on_close(self):
        print("Close data-stream.")
        thread.exit()

    def run(self):
        ws = loki_websocket.WebSocketApp(
            url=self.stream_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)
        ws.run_forever()

