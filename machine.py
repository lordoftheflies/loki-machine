
import time
import subprocess
import ConfigParser
import ast
import sys
import thread
import threading
import websocket
import Queue
import json
import socket

import loki_common
import loki_driver
import loki_rabbitmq
import loki_websocket

RETRY_INTERVAL = 0.1


class JsonTransport:
    def parse(self, data):
        return json.dumps(data)


class DataRiver:
    def loadConfiguration(self, fileName, space):
        config = ConfigParser.SafeConfigParser({
            'node': 'unknown-node',
            'sensors': [],
            'period': 1,

            'protocol': 'ws',
            'host': 'localhost',
            'port': 8183,
        })
        config.read(fileName)

        try:
            space['node'] = config.get("machine-controller", "node")
            space['sensors'] = ast.literal_eval(config.get("machine-controller", "sensors"))
        except ConfigParser.NoSectionError:
            config.add_section("machine-controller")
            config.set("machine-controller", "node", space['node'])
            config.set("machine-controller", "sensors", space['sensors'])

        try:
            space['protocol'] = config.get("ingestion-gateway", "protocol")
            space['host'] = config.get("ingestion-gateway", "host")
            space['port'] = config.getint("ingestion-gateway", "port")
        except ConfigParser.NoSectionError:
            config.add_section("ingestion-gateway")
            config.set("ingestion-gateway", "protocol", space['protocol'])
            config.set("ingestion-gateway", "host", space['host'])
            config.set("ingestion-gateway", "port", str(space['port']))

        try:
            space['period'] = config.getfloat("sensor-sampling", "period")
        except ConfigParser.NoSectionError:
            config.add_section("sensor-sampling")
            config.set("sensor-sampling", "period", str(space['period']))

    def saveConfiguration(self, fileName, space):
        config = ConfigParser.SafeConfigParser()

        if (not config.has_section("machine-controller")):
            config.add_section("machine-controller")
        config.set("machine-controller", "node", space['node'])
        config.set("machine-controller", "sensors", str(space['sensors']))

        if (not config.has_section("ingestion-gateway")):
            config.add_section("ingestion-gateway")
        config.set("ingestion-gateway", "protocol", space['protocol'])
        config.set("ingestion-gateway", "host", space['host'])
        config.set("ingestion-gateway", "port", str(space['port']))

        if (not config.has_section("sensor-sampling")):
            config.add_section("sensor-sampling")
        config.set("sensor-sampling", "period", str(space['period']))

        # Writing our configuration file.
        with open(fileName, 'wb') as configfile:
            config.write(configfile)


class Machine:
    def __init__(self, std_err, std_out):
        self.std_err = std_err
        self.std_out = std_out

    def restart(self):
        print("Network connection broken, restarting...")
        command = "/usr/bin/sudo /sbin/reboot"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print(output)


class Channel:
    def __init__(self, destination):
        self.destination = destination


class DataCollectorThread(threading.Thread):
    """
    Thread for collection data from a sensor.
    """

    def __init__(self, sensor, queue, collection_interval = 1):
        """
        :param sensor: Sensor descriptor object.
        :param queue: Data buffer queue
        :param collection_interval: Cycle interval for data-collection.
        """
        threading.Thread.__init__(self)
        self.sensor = sensor
        self.collection_interval = collection_interval
        self.queue = queue

    def run(self):
        """
        Continous USB module reading.
        """
        print("Starting data-collection of %s sensor ..." % self.sensor.name)
        # Create USB handler for the sensor.
        handler = loki_driver.UsbHandler(self.sensor)
        # Read until sensor enabled.
        while (self.sensor.enabled):
            try:
                # Read sensor data from the USB module
                dataArray = handler.read()
                for data in dataArray:
                    # Add node name
                    data['node'] = socket.gethostname()
                    # Push data to the queue
                    self.queue.put(JsonTransport().parse(data))
                # Wait a cycle
                time.sleep(self.collection_interval)
            except loki_common.SensorIoError as ex:
                print (ex.message)
                print("Restart data-collection of %s sensor ..." % self.sensor.name)
                handler = loki_driver.UsbHandler(self.sensor)
        print("Stop data-collection of %s sensor ..." % self.sensor.name)


sensor_thread_pool = {}
channel_thread_pool = {}
sensors = [
    loki_driver.Sensor(name="avago", vendor=0x16c0, product=0x03ee, bm_request_type=0xC0, b_request=3, w_value=0, w_index=0,
                       w_length=6, parser_expression=lambda data: [
            {'code': 'light', 'value': (256 * data[0]) + data[1]},
            {'code': 'mtn_cnt', 'value': (256 * data[2]) + data[3]},
            {'code': 'mtn_perc', 'value': data[5]}
        ]),
    loki_driver.Sensor(name="sht25", vendor=0x16c0, product=0x03ef, bm_request_type=0xC0, b_request=3, w_value=0, w_index=0,
                       w_length=4, parser_expression=lambda data: [
            {'code': 'hum', 'value': (256 * data[0]) + data[1]},
            {'code': 'temp', 'value': (256 * data[2]) + data[3]}
        ]),
    loki_driver.Sensor(name="telaire", vendor=0x16c0, product=0x03f0, bm_request_type=0xC0, b_request=3, w_value=0,
                       w_index=0,
                       w_length=2, parser_expression=lambda data: [
            {'code': 'co2', 'value': (256 * data[0]) + data[1]}
        ]),
    loki_driver.Sensor(name="adau", vendor=0x16c0, product=0x03f1, bm_request_type=0xC0, b_request=3, w_value=0, w_index=0,
                       w_length=2, parser_expression=lambda data: [
            {'code': 'noise', 'value': (256 * data[0]) + data[1]}
        ]),
    loki_driver.Sensor(name="default", vendor=0x16c0, product=0x05df, bm_request_type=0xC0, b_request=3, w_value=0,
                       w_index=0,
                       w_length=6, parser_expression=lambda data: [
            {'code': 'default', 'value': data}
        ])
]
channels = [
    Channel(destination="")
]


def initialize(queue, collection_interval=1):
    for sensor in sensors:
        sensor_thread_pool[sensor.name] = DataCollectorThread(
            sensor=sensor,
            queue=queue,
            collection_interval=collection_interval)
    # for channel in channels:
    #     channel_thread_pool[channel.name] = loki_websocket.WebsocketDataExtractorThread(
    #         sensor=sensor,
    #         queue=queue,
    #         stream_url=channel.destination)

    channel_thread_pool['rabbitmq'] = loki_rabbitmq.RabbitMqDataExtractorThread(queue=queue)


def run_data_collection():
    for sensor in sensors:
        sensor_thread_pool[sensor.name].start()


def run_data_extraction():
    # for channel in channels:
    #     channel_thread_pool[channel.name].start()
    channel_thread_pool['rabbitmq'].start()


if __name__ == '__main__':
    # Create data queue
    data_queue = Queue.Queue()
    # Initialize data channels
    initialize(data_queue)
    # Start services

    run_data_collection()
    run_data_extraction()
