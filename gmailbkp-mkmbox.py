#!/usr/bin/env python
"""Read names of eml files from STDIN and store them in mbox"""
import sys
import os
from optparse import OptionParser
from mailbox import mbox

arg_parser = OptionParser(usage = "gmailbkp-mkmbox.py [options] mbox",
                            description = __doc__)

arg_parser.add_option('-v', action='store_true', dest='verbose',
                    default=False, help="Show delete messages. Messages about "
                    "stored eml files are always printed. You should pipe "
                    "them to a file so that you can restore the eml files "
                    "from the mbox later.")
arg_parser.add_option('-d', action='store_true', dest='delete',
                    default=False, help="Delete eml file after storing it "
                    "in the mbox")

options, args = arg_parser.parse_args(sys.argv)

stored = []

target_mbox = None
try:
    if len(args) == 2:
        target_mbox = mbox(args[1])
        target_mbox.lock()
    else:
        arg_parser.print_help()
        sys.exit(2)
    for eml_filename in sys.stdin:
        eml_filename = eml_filename.rstrip()
        eml_file = open(eml_filename)
        id = target_mbox.add(eml_file)
        eml_file.close()
        print "Stored %s as %s" % (eml_filename, id)
        if options.delete: stored.append(eml_filename)
    if options.delete:
        for eml_filename in stored:
            os.remove(eml_filename)
            if options.verbose: print "Deleted %s" % eml_filename
except Exception, message:
    print "Program ended with exception. Run again."
    print message
finally:
    if target_mbox is not None: target_mbox.close()
