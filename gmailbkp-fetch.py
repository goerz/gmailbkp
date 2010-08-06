#!/usr/bin/env python
"""Download all the messages in a Gmail acccount to eml files in the given
FOLDER. Keep track of emails and labels in a record file"""
from ProcImap.ImapMailbox import ImapMailbox
from ProcImap.Utils.MailboxFactory import MailboxFactory
import hashlib
import re
import os
import sys
import pydb
from optparse import OptionParser

class DownloadError(Exception):
    """ Raised if the Mail Message was not downloaded correctly """
    pass

arg_parser = OptionParser(usage = "gmailbkp-fetch.py [options] [FOLDER]",
                            description = __doc__)

arg_parser.add_option('-v', action='store_true', dest='verbose',
                    default=False, help="Show status messages")
arg_parser.add_option('-c', action='store', dest='config',
                    default=os.environ['HOME']+"/.gmailbkp.conf", 
                    help="Use config file (default: ~/.gmaibkp.conf)")
arg_parser.add_option('-r', action='store', dest='record',
                    default='record.txt', help="record file (default: "
                    "record.txt). The filename is relative to the given FOLDER")
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
arg_parser.add_option('--raise', action='store_true', dest='raise_exception',
                    default=False, help="Raise full exceptions")

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
            if record.has_key("%s.%s" % (label, uid)):
                if options.verbose: print "Skip %s.%s" % (label, uid)
                continue
            try:
                size = mailbox.get_size(uid)
                message = mailbox.get(uid)
            except Exception, errormessage:
                record_file.flush()
                if options.raise_exception: raise
                print "Skipped %s.%s due to Exception: %s" \
                    % (label, uid, errormessage)
                try:
                    mailbox.reconnect()
                except:
                    mailbox = ImapMailbox((server.clone(), label))
                continue
            if message.size != size:
                errormessage = "Expected to download %s bytes. " % size
                errormessage += "Downloaded %s bytes. " % message.size
                # retry
                try:
                    message = mailbox.get(uid)
                    size = mailbox.get_size(uid)
                except Exception, errormessage:
                    record_file.flush()
                    if options.raise_exception: raise
                    print "Skipped %s.%s due to Exception: %s" \
                        % (label, uid, errormessage)
                    try:
                        mailbox.reconnect()
                    except:
                        mailbox = ImapMailbox((server.clone(), label))
                    continue
                if message.size != size:
                    raise DownloadError(errormessage)
            if size == 0: raise DownloadError("Downloaded 0 bytes")
            msg_string = message.as_string()
            filename = "%04i-%02i-%02i" % message.internaldate[:3]
            filename += "_%s.eml" % hashlib.sha224(msg_string).hexdigest()
            if not os.path.isfile(filename):
                outfile = open(filename, 'w')
                outfile.write(msg_string)
                outfile.close()
                if options.print_names: print filename
            print >>record_file, "%s.%s : %s" % (label, uid, filename)
            if options.verbose: print "Stored %s.%s" % (label, uid)
except KeyboardInterrupt:
    print ""
except Exception, errormessage:
    if options.raise_exception: raise
    print "Program ended with exception. Run again."
    print errormessage

record_file.close()
