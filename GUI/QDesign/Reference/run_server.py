#!/usr/bin/env python3
"""

run_mv_server.py is a module for use on a computer running MultiVu.  It can
be used with MultiPyVu.Client to control a Quantum Design cryostat.

"""

import sys

import MultiPyVu as mpv


def server(flags: str = ''):
    '''
    This method deciphers the command line text, and the instantiates the
    MultiVuServer.

    Parameters
    ----------
    flags : str
        For a list of flags, use the help flag, '--help'.
        The default is ''.

    Returns
    -------
    None.

    '''

    user_flags = []
    if flags == '':
        user_flags = sys.argv[1:]
    else:
        user_flags = flags.split(' ')

    s = mpv.Server(user_flags, keep_server_open=True)
    s.open()


if __name__ == '__main__':
    server()
