from __future__ import print_function

import time
import datetime
import sys
import usb.core
import usb.util


import loki_common


class Sensor:
    def __init__(self, name, vendor, product, parser_expression, b_request=3, w_length=6, bm_request_type=0xC0,
                 w_value=0, w_index=0, collection_interval=10):
        self.vendor = vendor
        self.product = product

        self.bm_request_type = bm_request_type,
        self.b_request = b_request
        self.w_value = w_value
        self.w_index = w_index
        self.w_length = w_length

        self.parser_expression = parser_expression
        self.collection_interval = collection_interval

        self.name = name
        self.enabled = False


class UsbHandler:
    def __init__(self, sensor):
        self.sensor = sensor

        self.handler = usb.core.find(
            idVendor=sensor.vendor,
            idProduct=sensor.product)
        if self.handler is None:
            print(('%s device not connected.' % self.sensor.name), file=sys.stderr)
            sensor.enabled = False
        else:
            print('Found %s device.' % self.sensor.name, file=sys.stdout)
            sensor.enabled = True

    def read(self):
        if (self.sensor.enabled is False):
            raise loki_common.SensorStateException('Disabled sensors are not readable.')
        try:
            # Todo syntax check to use the first parameter.
            # ret = self.handler.ctrl_transfer(self.sensor.bm_request_type,self.sensor.b_request,self.sensor.w_value, self.sensor.w_index,self.sensor.w_length)
            ret = self.handler.ctrl_transfer(0xC0, self.sensor.b_request, self.sensor.w_value, self.sensor.w_index, self.sensor.w_length)
            # Parse binary data
            dataArray = self.sensor.parser_expression(ret)
            # Put timestamp on the message
            for data in dataArray:
                # data['ts'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime())
                data['ts'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            print ("Read %s sensor data: %s"  % (self.sensor.name, str(dataArray)))
            # Return data object
            return dataArray

        except IOError as e:
            raise loki_common.SensorIoError('Could not read %s device ' % self.sensor.name)
