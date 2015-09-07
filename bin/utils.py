#!/usr/bin/env python3

from datetime import datetime
import argparse
import sys


def log_msg(msg, dev='con', newline=True, date=True):
    if newline:
        msg += '\n'

    if date:
        date = str(datetime.strftime(datetime.now(), "%Y/%m/%d %H:%M:%S"))
        msg = date+': '+msg

    if dev == 'con':
        sys.stdout.write(msg)
        sys.stdout.flush()
    else:
        with open(dev,'a') as log_out:
            log_out.write(msg)


if __name__ == "__main__":
    log_msg('Util functions only. '+__file__+'...Done.')

