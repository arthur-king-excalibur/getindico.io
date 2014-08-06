# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from __future__ import division, absolute_import, print_function

import fcntl
import re
import struct
import sys
import termios
import time


def strip_ansi(s, _re=re.compile(r'\x1b\[[;\d]*[A-Za-z]')):
    return _re.sub('', s)


def yesno(message):
    """
    A simple yes/no question (returns True/False)
    """
    inp = raw_input("%s [y/N] " % message)
    if inp == 'y' or inp == 'Y':
        return True
    else:
        return False


def terminal_size():
    h, w, hp, wp = struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
    return w, h


def conferenceHolderIterator(ch, verbose=True, deepness='subcontrib'):
    """
    Goes over all conferences, printing a status message (ideal for scripts)
    """

    def _eventIterator(conference, tabs):
        for contrib in conference.getContributionList():
            yield ('contrib', contrib)

            if deepness == 'subcontrib':
                for scontrib in contrib.getSubContributionList():
                    yield ('subcontrib', scontrib)

    idx = ch._getIdx()
    total = len(idx.keys())
    term_width = terminal_size()[0]
    start_time = time.time()
    fmt = cformat(
        '[%{cyan!}{:6}%{reset}/%{cyan}{}%{reset}  %{yellow!}{:.3f}%{reset}%  %{green!}{}%{reset}]  {:>8}  %{grey!}{}'
    )

    for i, (id_, conf) in enumerate(idx.iteritems(), 1):
        if verbose and (i % 10 == 0 or i == total):
            remaining_seconds = int((time.time() - start_time) / i * (total - i))
            remaining = '{:02}:{:02}'.format(remaining_seconds // 60, remaining_seconds % 60)
            title = conf.getTitle().replace('\n', ' ')
            text = fmt.format(i, total, (i / total * 100.0), remaining, id_, title)
            print('\r', ' ' * term_width, end='', sep='')
            # terminal width + ansi control code length - trailing reset code (4)
            print('\r', text[:term_width + len(text) - len(strip_ansi(text)) - 4], cformat('%{reset}'), end='', sep='')
            sys.stdout.flush()

        yield ('event', conf)
        if deepness in ['contrib', 'subcontrib']:
            for contrib in _eventIterator(conf, 0):
                yield contrib

    if verbose:
        print()


# Coloring

try:
    from termcolor import colored
except ImportError:
    def colored(text, *__, **___):
        """
        just a dummy function that returns the same string
        (in case termcolor is not available)
        """
        return text


def _cformat_sub(m):
    bg = 'on_{}'.format(m.group('bg')) if m.group('bg') else None
    attrs = ['bold'] if m.group('fg_bold') else None
    return colored('', m.group('fg'), bg, attrs=attrs)[:-4]


def cformat(string):
    """Replaces %{color} and %{color,bgcolor} with ansi colors.

    Bold foreground can be achieved by suffixing the color with a '!'
    """
    reset = colored('')
    string = string.replace('%{reset}', reset)
    string = re.sub(r'%\{(?P<fg>[a-z]+)(?P<fg_bold>!?)(?:,(?P<bg>[a-z]+))?}', _cformat_sub, string)
    if not string.endswith(reset):
        string += reset
    return string


# Error/warning/info message util methods

def error(message):
    """
    Print a red error message
    """
    print(colored(message, 'red'))


def warning(message):
    """
    Print a yellow warning message
    """
    print(colored(message, 'yellow'))


def info(message):
    """
    Print a blue information message
    """
    print(colored(message, 'cyan', attrs=['bold']))


def success(message):
    """
    Print a green success message
    """
    print(colored(message, 'green'))
