"""
Gives access and parses output of lsusb into python objects.
"""
import re
import subprocess

class USBDevice(object):
    """
    Representation of an USB device connected to the system
    """
    def __init__(self, device, tag, usb_id):
        self.device = device
        self.tag = tag
        self.usb_id = usb_id
    
    def __str__(self):
        return "{} ({})".format(self.tag, self.usb_id)

    def __repr__(self):
        t = type(self)
        return "<{}.{}: {}>".format(t.__module__, t.__name__, str(self))


def get_device_list():
    """
    Generator for USBDevice types
    """
    device_re = re.compile(r"Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<usb_id>\w+:\w+)\s(?P<tag>.+)$", re.I)
    device_output = subprocess.check_output("lsusb", shell=True)
    for i in device_output.split('\n'):
        info = device_re.match(i)
        if info:
            dinfo = info.groupdict()
            dinfo['device'] = '/dev/bus/usb/{}/{}'.format(
                dinfo.pop('bus'), dinfo.pop('device'))
            yield USBDevice(**dinfo)

