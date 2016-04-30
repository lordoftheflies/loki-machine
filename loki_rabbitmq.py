from __future__ import print_function

import pika
import threading
import thread
import sys
import socket
import logging
import time

LOGGER = logging.getLogger(__name__)
logging.basicConfig(format='(%(threadName)-10s) %(message)s')


class RabbitMqDataExtractorThread(threading.Thread):
    """
    Thread for sending data to the cloud.
    """

    def __init__(self, queue, host='hegedus.pikotera.hu', port=5672, vhost='/druid', username='druid',
                 password='diurd', round_interval = 1):
        super(RabbitMqDataExtractorThread, self).__init__()

        self.queue = queue
        self.host = host
        self.port = port
        self.vhost = vhost
        self.username = username
        self.password = password
        self._terminated = False
        self.round_interval = round_interval

        self.channel = None

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika. If you want the reconnection to work, make
        sure you set stop_ioloop_on_close to False, which is not the default
        behavior of this adapter.

        :rtype: pika.SelectConnection

        """

        return pika.SelectConnection(pika.URLParameters(self._url),
                                     on_open_callback=self.on_connection_open,
                                     on_close_callback=self.on_connection_closed,
                                     stop_ioloop_on_close=False)

    def on_open_connection(self):
        print("Open connection ...")

    def on_declare_queue(self):
        print("Queue declared ")

    def on_open_queue(self):
        print("Open queue ...")
        # while not self.queue.empty():
        #     ws.send(self.queue.get())

        while not self._terminated:
            while not self.queue.empty():
                message = self.queue.get()
                print ("Send message to cloud %s" % str(message))
                self.channel.basic_publish(
                    exchange='data-exchange',
                    routing_key=socket.gethostname(),
                    body=message)
            time.sleep(self.round_interval)

    def on_message(self, ws, message):
        print(message, file=sys.stdout)

    def on_error(self, ws, error):
        print(error, file=sys.stderr)

    def on_close(self):
        print("Close data-stream.")
        thread.exit()

    def run(self):
        print("Start AMQP data-extraction ...")
        try:
            LOGGER.info('Connecting to AMQP://%s:%s%s ...', (self.host, self.port, self.vhost))
            # connection = pika.SelectConnection(
            #     pika.ConnectionParameters(
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    virtual_host=self.vhost,
                    port=5672,
                    credentials=pika.PlainCredentials(username=self.username, password=self.password)
                ))

            self.channel = connection.channel()
            self.channel.queue_declare(queue=socket.gethostname())

            self.on_open_queue()

        # except ChannelClosed as ex:

        except Exception as ex:
            print("Error in the extraction service: %s " % ex.message, file=sys.stderr)
