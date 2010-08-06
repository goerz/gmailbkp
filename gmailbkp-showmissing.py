#!/usr/bin/env python
"""List all the messages in a Gmail acccount that are not in the record file"""
from ProcImap.ImapMailbox import ImapMailbox
from ProcImap.Utils.MailboxFactory import MailboxFactory
from ProcImap.Utils.Server import summary
import re
import os
import sys
from optparse import OptionParser

class DownloadError(Exception):
    """ Raised if the Mail Message was not downloaded correctly """
    pass

arg_parser = OptionParser(usage = "gmailbkp-fetch.py [options] [FOLDER]",
                            description = __doc__)

arg_parser.add_option('-c', action='store', dest='config',
                    default=os.environ['HOME']+"/.gmailbkp.conf", 
                    help="Use config file (default: ~/.gmaibkp.conf)")
arg_parser.add_option('-r', action='store', dest='record',
                    default='record.txt', help="record file (default: "
                    "record.txt). The filename is relative to the given FOLDER")
arg_parser.add_option('-s', action='store_true', dest='ignore_standard',
                    default=False, help="Add the labels '[Gmail]/Trash' "
                    "and '[Gmail]/Spam' to the exclude list.")
arg_parser.add_option('--include', action='store', dest='include',
                    default='', help="Skip the labels NOT in this list "
                    "(comma separated)")
arg_parser.add_option('--exclude', action='store', dest='exclude',
                    default='', help="Skip the labels in this list "
                    "(comma separated)")
arg_parser.add_option('--search', action='store', dest='search',
                    default='', help="Only store emails that match the "
                    "specified search. The search string should be like the "
                    "search syntax of the IMAP search command (RFC3501). E.g. "
                    "('FLAGGED SINCE 1-Feb-1994 NOT FROM \"Smith\"'")
arg_parser.add_option('--raise', action='store_true', dest='raise_exception',
                    default=False, help="Raise full exceptions")
arg_parser.add_option('--summary', action='store_true', dest='summary',
                    default=False, help="Show a summary (sender, date, "
                    "subject) of the missing messages")

options, args = arg_parser.parse_args(sys.argv)
if len(args) > 1:
    os.chdir(args[1])

mailboxes = MailboxFactory(options.config)

server = mailboxes.get_server('Gmail')

labels = server.list()
include = options.include.split(",")
exclude = options.exclude.split(",")
if options.ignore_standard:
    exclude.append('[Gmail]/Spam')
    exclude.append('[Gmail]/Trash')
if options.include == '': include = labels

record = {}
try:
    record_file = open(options.record)
    line_pattern = re.compile(r'(?P<luid>.*\.\d+) : (?P<filename>\d{4}-\d{2}-\d{2}_[0-9a-f]{56}\.eml)')
    for line in record_file:
        line_match = line_pattern.match(line)
        if line_match:
            record[line_match.group('luid')] = line_match.group('filename')
        else:
            print "Can't understand line in record file"
    record_file.close()
except IOError:
    pass

record_file = open(options.record, 'a')
mailbox = None
try:
    for label in labels:
        if not label in include: continue
        if label in exclude: continue
        if mailbox is None:
            mailbox = ImapMailbox((server, label))
        else:
            mailbox.switch(label)
        if options.search == '':
            uids = mailbox.get_all_uids()
        else:
            uids = mailbox.search(options.search)
        for uid in uids:
            if not record.has_key("%s.%s" % (label, uid)):
                descr = "%s.%s " % (label, uid)
                if options.summary:
                    s = summary(mailbox, uid, printuid=False, printout=False)[0]
                    descr += "\t" + s[3:]
                print descr
except KeyboardInterrupt:
    print ""
except Exception, errormessage:
    if options.raise_exception: raise
    print "Program ended with exception. Run again."
    print errormessage

record_file.close()
