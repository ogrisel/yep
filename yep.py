#!/usr/bin/env python
"""Yep Extension Profiler

Yep is a tool to profile compiled code (C/C++/Fortran) from the Python
interpreter. It uses the google-perftools CPU profiler and depends on
pprof for visualization.

See http://pypi.python.org/pypi/yep for more info.
"""

_CMD_USAGE = """usage: python -m yep [options] scriptfile [arg] ...

This will create a file scriptfile.prof that can be analyzed with
pprof (google-pprof on Debian-based systems).
"""


#       .. find google-perftools ..
import ctypes.util
google_profiler = ctypes.util.find_library('profiler')
if google_profiler:
    libprofiler = ctypes.CDLL(google_profiler)
else:
    raise ImportError(
        'Unable to find libprofiler, please make sure google-perftools '
        'is installed on your system'
        )

__version__ = '0.2'

def start(file_name=None):
    """
    Start the CPU profiler.

    Parameters
    ----------
    fname : string, optional
       Name of file to store profile count. If not given, 'out.prof'
       will be used
    """
    if file_name is None:
        file_name = 'out.prof'
    status = libprofiler.ProfilerStart(file_name)
    if status < 0:
        raise ValueError('Profiler did not start')


def stop():
    """Stop the CPU profiler"""
    libprofiler.ProfilerStop()


def main():
    import sys, os, __main__
    from optparse import OptionParser
    parser = OptionParser(usage=_CMD_USAGE)
    parser.add_option('-o', '--outfile', dest='outfile',
        help='Save stats to <outfile>', default=None)
    parser.add_option('-v', '--visualize', action='store_true',
        dest='visualize', help='Visualize result at exit',
        default=False)
    parser.add_option('-c', '--callgrind', action='store_true',
        dest='callgrind', help='Output file in callgrind format',
        default=False)


    if not sys.argv[1:] or sys.argv[1] in ("--help", "-h"):
        parser.print_help()
        sys.exit(2)

    (options, args) = parser.parse_args()
    sys.argv[:] = args

#       .. get file name ..
    main_file = os.path.abspath(args[0])
    if options.outfile is None:
        options.outfile = os.path.basename(main_file) + '.prof'
    if not options.callgrind:
        out_file = options.outfile
    else:
        import tempfile
        tmp_file = tempfile.NamedTemporaryFile()
        out_file = tmp_file.name
    if not os.path.exists(main_file):
        print('Error:', main_file, 'does not exist')
        sys.exit(1)

#       .. execute file ..
    sys.path.insert(0, os.path.dirname(main_file))
    start(out_file)
    exec(compile(open(main_file).read(), main_file, 'exec'),
         __main__.__dict__)
    stop()

    if any((options.callgrind, options.visualize)):
        from subprocess import call
        try:
            res = call(['google-pprof', '--help'])
        except OSError:
            res = 1
        pprof_exec = ('google-pprof', 'pprof')[res != 0]

        if options.visualize:
#       .. strip memory address, 32 bit-compatile ..
            sed_filter = '/[[:xdigit:]]\{8\}$/d'
            call("%s --cum --text %s %s | sed '%s' | less" % \
                 (pprof_exec, sys.executable, options.outfile, sed_filter),
                 shell=True)

        if options.callgrind:
            call("%s --callgrind %s %s > %s" % \
                 (pprof_exec, sys.executable, out_file, options.outfile),
                 shell=True)
            tmp_file.close()


if __name__ == '__main__':
    main()
