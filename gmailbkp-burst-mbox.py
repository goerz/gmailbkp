#!/usr/bin/env python
"""Burst the emails found in the mbox into eml files"""
import sys
import os
import re
import hashlib
from optparse import OptionParser
from mailbox import mbox

arg_parser = OptionParser(usage = "gmailbkp-burst-mbox.py [options] "
                                  +"mbox [path]", description = __doc__)

arg_parser.add_option('-v', action='store_true', dest='verbose',
                    default=False, help="Show status messages")
arg_parser.add_option('-l', action='store', dest='log',
                    default=None, help="Use log file from gmailbk-mkmbox "
                    "in order to restore to the original eml filenames. "
                    "If no log file is given, the eml files are stored as "
                    "<hash>.eml, where <hash> is the sha224 hash of the "
                    "message. If the original eml filename for a given "
                    "message, as read from the log file, does not end in "
                    "<hash>.eml, a warning is printed.")

options, args = arg_parser.parse_args(sys.argv)
path = ""

log_pattern = re.compile(r'^Stored (?P<filename>.*) as (?P<id>\d+)$')

filenames = {}
if options.log is not None:
    logfile = open(options.log)
    for line in logfile:
        log_match = log_pattern.match(line)
        if log_match:
            filenames[int(log_match.group('id'))] = log_match.group('filename')
    logfile.close()

warnings = 0
try:
    if len(args) >= 2:
        source_mbox = mbox(args[1])
        source_mbox.lock()
    else:
        arg_parser.print_help()
        sys.exit(2)
    if len(args) >= 3:
        path = os.chdir(args[2])
    for i, message in enumerate(source_mbox):
        msg_string = message.as_string()
        sha_name = "%s.eml" % hashlib.sha224(msg_string).hexdigest()
        filename = sha_name
        if options.log:
            try:
                filename = filenames[i]
                if not filename.endswith(sha_name):
                    print("WARNING: Message %i " % i
                    +"does not have the expected hash")
                    warnings += 1
            except KeyError:
                print "There is no filename in log for index %i" %i
        outfile = open(os.path.join(path, filename), 'w')
        outfile.write(msg_string)
        outfile.close()
        if options.verbose: print "Written message %s as %s" % (i, filename)
except Exception, message:
    print "Program ended with exception. Run again."
    print message
finally:
    if warnings > 0:
        print "There were %i warnings due to a hash mismatch." % warnings
        print "This can happen because newlines in front of MIME boundaries" \
              "were dropped. In this case, you can ignore the warnings." 
    source_mbox.close()
