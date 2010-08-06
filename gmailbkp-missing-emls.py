#!/usr/bin/env python
"""List all the eml files that are referenced in the record file but do not
exist"""
import re
import os
import sys
from optparse import OptionParser

class DownloadError(Exception):
    """ Raised if the Mail Message was not downloaded correctly """
    pass

arg_parser = OptionParser(usage = "gmailbkp-missing-emls.py [options] [FOLDER]",
                            description = __doc__)

arg_parser.add_option('-c', action='store', dest='config',
                    default=os.environ['HOME']+"/.gmailbkp.conf", 
                    help="Use config file (default: ~/.gmaibkp.conf)")
arg_parser.add_option('-r', action='store', dest='record',
                    default='record.txt', help="record file (default: "
                    "record.txt). The filename is relative to the given FOLDER")
arg_parser.add_option('--maildir', action='store_true', dest='maildir',
                    default=False, help="Look for eml files inside the 'cur' "
                    "subfolder of the given FOLDER")

options, args = arg_parser.parse_args(sys.argv)
if len(args) > 1:
    os.chdir(args[1])
else:
    arg_parser.print_help()
    sys.exit(2)
if options.maildir:
    options.record = os.path.join('..', options.record)
    os.chdir('cur')

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

for emlfile in filenames:
    if not os.path.isfile(emlfile):
        print emlfile
