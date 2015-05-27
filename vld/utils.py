#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, division

import argparse
import logging

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


#Found on http://stackoverflow.com/a/566752/2646228
def get_terminal_size():
    import os
    env = os.environ

    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
                                                 '1234'))
        except:
            return
        return cr

    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])


def base_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbosity",
        action='count',
        help='Enable logging. If set twice, sets level to DEBUG.')
    return parser
