#!/usr/bin/env python
"""Delete all eml files that are not references in record"""
import re
import os
import sys
from glob import glob
from optparse import OptionParser

arg_parser = OptionParser(usage = "gmailbkp-purge.py [options] [path]",
                            description = __doc__)

arg_parser.add_option('-v', action='store_true', dest='verbose',
                    default=False, help="Show status messages")
arg_parser.add_option('-r', action='store', dest='record',
                    default='record.txt', 
                    help="record file (default: record.txt)")

options, args = arg_parser.parse_args(sys.argv)
if len(args) > 1:
    os.chdir(args[1])

try:
    # read in record
    filenames = set()
    record_file = open(options.record)
    line_pattern = re.compile(r'(?P<luid>.*\.\d+) : (?P<filename>\d{4}-\d{2}-\d{2}_[0-9a-f]{56}\.eml)')
    for line in record_file:
        line_match = line_pattern.match(line)
        if line_match:
            filenames.add(line_match.group('filename'))
        else:
            print "Can't understand line in record file"
    record_file.close()

    # delete those files that are not in filenames
    for filename in glob('*.eml'):
        if filename not in filenames:
            os.remove(filename)
            if options.verbose: print "Removed %s" % filename

except Exception, message:
    print "Program ended with exception. Run again."
    print message

