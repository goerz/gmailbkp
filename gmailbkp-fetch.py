#!/usr/bin/env python
"""Download all the messages in a Gmail acccount to eml files. Keep track of
files in a record file"""
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

arg_parser = OptionParser(usage = "gmailbkp-fetch.py [options] [PATH]",
                            description = __doc__)

arg_parser.add_option('-v', action='store_true', dest='verbose',
                    default=False, help="Show status messages")
arg_parser.add_option('-c', action='store', dest='config',
                    default=os.environ['HOME']+"/.gmailbkp.conf", 
                    help="Use config file (default: ~/.gmaibkp.conf)")
arg_parser.add_option('-r', action='store', dest='record',
                    default='record.txt', help="record file (default: "
                    "record.txt). The filename is relative to the given PATH")
arg_parser.add_option('-p', action='store_true', dest='print_names',
                    default=False, help="Print names of newly created "
                    "eml files")
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
arg_parser.add_option('--maildir', action='store_true', dest='maildir',
                    default=False, help="Store eml files in a pseudo-maildir "
                    "format. The folders 'new', 'cur', and 'tmp' will be "
                    "created and all eml files will be written to 'cur'. The "
                    "name of the eml files are not consistent with the "
                    "maildir standard, but mutt will be able to read the "
                    "folder as a maildir mailbox nonetheless")

options, args = arg_parser.parse_args(sys.argv)
if len(args) > 1:
    os.chdir(args[1])
if options.maildir:
    if not os.path.isdir('tmp'): os.mkdir('tmp')
    if not os.path.isdir('cur'): os.mkdir('cur')
    if not os.path.isdir('new'): os.mkdir('new')
    options.record = os.path.join('..', options.record)
    os.chdir('cur')

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
try:
    for label in labels:
        if not label in include: continue
        if label in exclude: continue
        mailbox = ImapMailbox((server, label))
        if options.search == '':
            uids = mailbox.get_all_uids()
        else:
            uids = mailbox.search(options.search)
        for uid in uids:
            if record.has_key("%s.%s" % (label, uid)):
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
