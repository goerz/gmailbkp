#!/usr/bin/env python
"""
    Download all the messages in a Gmail acccount to eml files. Keep track of
    files in 'record.txt'
"""
from ProcImap.ImapMailbox import ImapMailbox
from ProcImap.Utils.MailboxFactory import MailboxFactory
import hashlib
import re
import os
import sys
from optparse import OptionParser

class DownloadError(Exception):
    """ Raised if the Mail Message was not downloaded correctly """
    pass

arg_parser = OptionParser(usage = "gmailbkp-fetch.py [options] [path]",
                            description = __doc__)

arg_parser.add_option('-v', action='store_true', dest='verbose',
                    default=False, help="Show status messages")
arg_parser.add_option('-c', action='store', dest='config',
                    default=os.environ['HOME']+"/.gmailbkp.conf", 
                    help="Use config file (default: ~/.gmaibkp.conf")
arg_parser.add_option('-p', action='store_true', dest='print_names',
                    default=False, help="Print names of newly created "
                    "eml files")
arg_parser.add_option('--include', action='store', dest='include',
                    default='', help="Skip the labels NOT in this list "
                    "(comma separated)")
arg_parser.add_option('--exclude', action='store', dest='exclude',
                    default='', help="Skip the labels in this list "
                    "(comma separated)")

options, args = arg_parser.parse_args(sys.argv)
if len(args) > 1:
    os.chdir(args[1])


mailboxes = MailboxFactory(options.config)

server = mailboxes.get_server('Gmail')

labels = server.list()
include = options.include.split(",")
exclude = options.exclude.split(",")
if options.include == '': include = labels

existing = {}
try:
    record_file = open('record.txt')
    line_pattern = re.compile(r'(?P<luid>.*\.\d+) : (?P<filename>\d{4}-\d{2}-\d{2}_[0-9a-f]{56}\.eml)')
    for line in record_file:
        line_match = line_pattern.match(line)
        if line_match:
            existing[line_match.group('luid')] = line_match.group('filename')
        else:
            print "Can't understand line in record file"
    record_file.close()
except IOError:
    pass

record_file = open('record.txt', 'a')
try:
    for label in labels:
        if not label in include: continue
        if label in exclude: continue
        mailbox = ImapMailbox((server, label))
        for uid in mailbox.get_all_uids():
            if existing.has_key("%s.%s" % (label, uid)):
                if options.verbose: print "Skip %s.%s" % (label, uid)
                continue
            size = mailbox.get_size(uid)
            message = mailbox.get(uid)
            msg_string = message.as_string()
            if message.size != size:
                message = "Expected to download %s bytes. " % size
                message += "Downloaded %s bytes. " % message.size
                raise DownloadError(message)
            filename = "%04i-%02i-%02i" % message.internaldate[:3]
            filename += "_%s.eml" % hashlib.sha224(msg_string).hexdigest()
            if not os.path.isfile(filename):
                outfile = open(filename, 'w')
                outfile.write(msg_string)
                outfile.close()
                if options.print_names: print filename
            print >>record_file, "%s.%s : %s" % (label, uid, filename)
            if options.verbose: print "Stored %s.%s" % (label, uid)
            record_file.flush()
        mailbox.close()
except KeyboardInterrupt:
    print ""
except Exception, message:
    print "Program ended with exception. Run again."
    print message

record_file.close()
