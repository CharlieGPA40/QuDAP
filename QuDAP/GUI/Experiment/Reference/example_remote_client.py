#!/usr/bin/env python3
'''
example_Remote-Client.py - This minimum working example will test that
the client PC can successfully contact the remote server PC.
Make sure the host vairable has the correct IP address
'''

# Package used to insert a short wait time between data polls
import time

import MultiPyVu as mpv

# Both the client and server must be running on the same machine for
# 'local' operation.
host = "172.00.00.1"
port = 5000
client = mpv.Client(host, port)
# Start the client
# client.open()
# with mpv.Server() as server:
#     with mpv.Client() as client:
#
#         # A basic loop that demonstrates communication between client/server
#         for t in range(5):
#             # Polls MultiVu for the temperature, field, and their respective states
#             T, sT = client.get_temperature()
#             F, sF = client.get_field()
#
#             # Relay the information from MultiVu
#             message = f'The temperature is {T}, status is {sT}; the field is {F}, status is {sF}. '
#             print(message)
#
#             # collect data at roughly 2s intervals
#             time.sleep(2)
