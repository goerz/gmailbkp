#!/usr/bin/env python
"""Remove all entries from the record file that link to non-exisiting eml 
files"""
import re
import os
import sys
import shutil
from optparse import OptionParser

class DownloadError(Exception):
    """ Raised if the Mail Message was not downloaded correctly """
    pass

arg_parser = OptionParser(usage = "gmailbkp-cleanrecord.py [options] [FOLDER]",
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

for line in sys.stdin:
    filenames.add(line.rstrip())

shutil.copy(options.record, "%s~" % options.record)
record_file = open("%s~" % options.record)
new_record_file = open(options.record, 'w')
line_pattern = re.compile(r'(?P<luid>.*\.\d+) : (?P<filename>\d{4}-\d{2}-\d{2}_[0-9a-f]{56}\.eml)')
for line in record_file:
    line_match = line_pattern.match(line)
    if line_match:
        if line_match.group('filename') in filenames:
            print "removing line '%s'" % line.rstrip()
        else:
            new_record_file.write(line)
    else:
        print "Can't understand line in record file"
record_file.close()
new_record_file.close()
