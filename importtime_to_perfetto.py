"""
importtime to perfetto

Dump Python importtime stats in a perfetto-friendly json file.

See also https://github.com/kmichel/python-importtime-graph

importtime format looks like this:

import time: self [us] | cumulative | imported package
import time:       101 |        101 |   _io
import time:        22 |         22 |   marshal
import time:       275 |        275 |   posix
import time:       427 |        824 | _frozen_importlib_external
import time:       609 |        609 |   time
import time:        90 |        699 | zipimport
import time:        45 |         45 | faulthandler
import time:        27 |         27 |     _codecs
import time:       193 |        220 |   codecs
import time:       451 |        451 |   encodings.aliases
import time:       588 |       1259 | encodings
import time:       187 |        187 | encodings.utf_8
import time:        57 |         57 | _signal
import time:        19 |         19 |     _abc
import time:        89 |        107 |   abc
import time:       109 |        216 | io
import time:       226 |        226 |       types
import time:        43 |         43 |         _operator
import time:       287 |        329 |       operator
import time:       420 |        420 |           _collections_abc
import time:        69 |         69 |           itertools
import time:       182 |        182 |           keyword
import time:       200 |        200 |           reprlib
import time:        38 |         38 |           _collections
import time:       580 |       1486 |         collections
import time:        31 |         31 |         _functools
import time:       583 |       2099 |       functools
import time:       957 |       3610 |     enum
import time:        94 |         94 |       _sre
import time:       225 |        225 |         re._constants
import time:       283 |        508 |       re._parser
import time:       163 |        163 |       re._casefix

# ????
import time:   2142919 |    2143469 |     schrodinger.application.scisol.packages.csp.common.constants


time stamps are emitted after the import is complete, so dependencies are
in backwards order - _frozen_importlib_external imports _io, marshal, posix

"""


import json


def parse_importtime(data):
    """
    Read the data from python3 -X importtime into start times and durations
    
    """

    # Should yield: start time, duration, name
    # times all in microseconds
    
    # previous end time
    stack = [0]
    # if it's the same level or lower as previous, then the start time
    # is after the previous end time. if it's deeper, then it's the same
    # as the previous start time.
    max_time = 0

    for line in data:
        if 'import time:' not in line or 'self [us]' in line:
            continue
        parts = line.split("|")
        if len(parts) != 3:
            continue
        # always use cumulative time - viewer will calculate self time
        # self_time = int(parts[0].split(":")[1].strip())
        cumulative = int(parts[1].strip())
        name = parts[2].strip()

        # -X importtime indents by 2 spaces each time
        indent = len(parts[2].rstrip()) - len(name) - 1
        indent /= 2
        name = name.lstrip()

        while indent > len(stack) - 1:
            stack.append(stack[-1])
        while indent < len(stack) - 1:
            stack.pop(-1)

        prev_end = stack[-1]
        start_time = prev_end
        stack[-1] = start_time + cumulative
        max_time = max(max_time, stack[-1])
    
        yield start_time, cumulative, name, indent
    yield 0, max_time, '__main__', 0


def importtime_to_perfetto(data):
    traceEvents = []
    for event in parse_importtime(data):
        start_time, duration, name, indent = event
        traceEvents.append({
            'name': name,
            'cat': 'import',
            'ph': 'X',
            'ts': start_time,
            'dur': duration,
            'pid': 1,
            'tid': 1,
            'args': { 'indent': indent }
        })
    return dict(traceEvents=traceEvents)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Convert python -X importtime output to perfetto json")
    parser.add_argument('input', type=argparse.FileType('r'))
    parser.add_argument('output')
    opts = parser.parse_args(argv)  

    with opts.input:
        structured_data = importtime_to_perfetto(opts.input)
    with open(opts.output, 'w') as output_file:
        json.dump(structured_data, output_file, indent=2)

if __name__ == "__main__":
    main()