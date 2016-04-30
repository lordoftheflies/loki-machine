import sys
import binascii

class IncomingValueError(IOError):
    """
    Incoming sensor data error.
    """

    def __init__(self, keys):
        """
        Incoming sensor value error constructor.
        :param keys: Not working sensor keys.
        """
        self.message = "Incoming value error - %s." % (",".join(keys))


class SocketError(IOError):
    def __init__(self):
        self.message = "Socket error."


class NetworkConnectionError(IOError):
    def __init__(self):
        self.message = "Network connection broken, rebooting..."


class BrokenPingError(IOError):
    def __init__(self, broken_pings):
        self.message = "Broken ping count: %s" % str(broken_pings)


class NoRouteToHost(IOError):
    def __init__(self):
        self.message = "No route to host (network lost)."


class UnknownException:
    def __init__(self, exception):
        self.message = "Other unhandled exception occured"


class IndexError:
    def __init__(self, query_bk, data_bk, response_bk):
        self.message = "Index error at calculating query from response(%s), query=%s, data=%s, response=%s" % (
            ('Error in line {} '.format(sys.exc_info()[-1].tb_lineno)),
            binascii.hexlify(query_bk),
            binascii.hexlify(data_bk),
            binascii.hexlify(response_bk))


class SerialPortError:
    def __init__(self):
        self.message = "Serial port error. Trying to reset port without reboot..."


class ConfigurationParsingError:
    def __init__(self):
        self.message = "Error parsing the config file!"


class SensorIoError(IOError):
    '''raise this when there's a lookup error for my app'''


class PointlessReadError(IOError):
    '''raise this when there's a lookup error for my app'''


class SensorStateException(IOError):
    '''raise this when there's a lookup error for my app'''
