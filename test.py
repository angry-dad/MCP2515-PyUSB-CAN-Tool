import usb.core
import time
import csv
import numpy as np
import datetime
import os

dev = usb.core.find(idVendor=0x04D8, idProduct=0x0070)

if dev is None:
    raise ValueError('MCP2515 Demo Board not found!')
print('MCP2515 Demo Board found!')

# set the active configuration. With no arguments, the first
# configuration will be the active one
dev.set_configuration()
# get an endpoint instance
cfg = dev.get_active_configuration()
intf = cfg[(0,0)]

ep_out = usb.util.find_descriptor(
    intf,
    # match the first OUT endpoint
    custom_match = \
    lambda e: \
        usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_OUT)
assert ep_out is not None      
print('MCP2515 Demo Board output endpoint found!')

ep_in = usb.util.find_descriptor(
    intf,
    # match the first IN endpoint
    custom_match = \
    lambda e: \
        usb.util.endpoint_direction(e.bEndpointAddress) == \
        usb.util.ENDPOINT_IN)
assert ep_in is not None
print('MCP2515 Demo Board input endpoint found!')

# Configure buad rate to 1 Mbps and normal mode
msg = bytearray(64)
msg[58] = 7
msg[60] = 2
msg[61] = 42

assert len(msg) == 64
num_bytes = dev.write(ep_out, msg, timeout = 500)
assert num_bytes is not None
print(f'Successfully set rate to 1 Mbps')

msg = bytearray(64)
msg[61] = 15
msg[62] = 7

assert len(msg) == 64
num_bytes = dev.write(ep_out, msg, timeout = 500)
assert num_bytes is not None
print(f'Successfully placed device in normal operation mode')

test_length = int(input("Enter number of random CAN frames to send:  "))
i=0

log_time_tag = datetime.datetime.now().strftime("%A_%B%d_%Y_%H%M%S")
with open(log_time_tag + '.csv', 'w', newline='') as writeFile:
    writer = csv.writer(writeFile)
    row = ['CAN ID SENT', 'CAN DATA SENT', 'CAN ID RECEIVED', 'CAN DATA RECEIVED', 'MATCH?']
    writer.writerow(row)
    while i < test_length:
        # Send a CAN frame with random ID and 8 bytes of random data
        msg = bytearray(64)
        msg[0] = np.random.randint(low=0, high=128, size=None, dtype='int')
        msg[1] = np.random.randint(low=1, high=241, size=None, dtype='int')
        msg[2] = 0
        msg[3] = 0
        msg[4] = 8
        msg[5] = np.random.randint(low=0, high=256, size=None, dtype='int')
        msg[6] = np.random.randint(low=0, high=256, size=None, dtype='int')
        msg[7] = np.random.randint(low=0, high=256, size=None, dtype='int')
        msg[8] = np.random.randint(low=0, high=256, size=None, dtype='int')
        msg[9] = np.random.randint(low=0, high=256, size=None, dtype='int')
        msg[10] = np.random.randint(low=0, high=256, size=None, dtype='int')
        msg[11] = np.random.randint(low=0, high=256, size=None, dtype='int')
        msg[12] = np.random.randint(low=0, high=256, size=None, dtype='int')
        msg[52] = 1
        msg[58] = 7
        assert len(msg) == 64
        num_bytes = dev.write(ep_out, msg, timeout = 500)
        assert num_bytes is not None

        can_id_tx = hex(msg[0]*16 + msg[1]//32)
        can_data_tx = '0x' + (hex(msg[5]) + hex(msg[6]) + hex(msg[7]) + hex(msg[8]) + \
        hex(msg[9]) + hex(msg[10]) + hex(msg[11]) + hex(msg[12])).replace('0x','')
        print(f'Random CAN frame sent:  ID: {can_id_tx} Data: 0x{can_data_tx}')

        while True:
            ret = dev.read(ep_in, len(msg), 500)
            if ret[0] == 136:
                break

        can_id_rx = hex(ret[1]*16 + ret[2]//32)
        can_data_rx = '0x' + (hex(ret[3]) + hex(ret[4]) + hex(ret[5]) + hex(ret[6]) + \
        hex(ret[7]) + hex(ret[8]) + hex(ret[9]) + hex(ret[10])).replace('0x','')
        print(f'Random CAN frame received:  ID: {can_id_rx} Data: 0x{can_data_rx}')

        if can_id_tx == can_id_rx and can_data_tx == can_data_rx:
            match = True
        else:
            match = False

        row = [can_id_tx, can_data_tx, can_id_rx, can_data_rx, match]
        writer.writerow(row)
        i = i+1

os.system("start " + log_time_tag + '.csv')
