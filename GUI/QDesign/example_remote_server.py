#!/usr/bin/env python3
'''
example_Remote-Server.py - For remote operation; this script must be
running on the on the control PC along with the MultiVu executable.
'''

import sys

import MultiPyVu as mpv


def server(flags: str = ''):
    user_flags = []
    if flags == '':
        user_flags = sys.argv[1:]
    else:
        msg = 'No flags detected; using hard-coded IP address'
        msg += 'for remote access.'
        print(msg)

        # This value comes from the server PC's self-identified IPV4
        # address and needs to be manually input
        user_flags = ['-ip=172.19.159.4']

    # Opens the server connection
    s = mpv.Server(user_flags, keep_server_open=True)
    s.open()


if __name__ == '__main__':
    server()
