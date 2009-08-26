#!/usr/bin/env python
"""
    Download all the messages in a Gmail acccount to eml files. Keep track of
    files in 'record.txt'
"""
from ProcImap.ImapMailbox import ImapMailbox
from ProcImap.Utils.MailboxFactory import MailboxFactory
from mailbox import mbox
import sys
import hashlib
import re

mailboxes = MailboxFactory('/Users/goerz/.procimap/mailboxes.cfg')
server = mailboxes.get_server('Gmail')
labels = server.list()

existing = {}
record_file = open('record.txt')
line_pattern = re.compile(r'(?P<luid>.*\.\d+) : (?P<filename>\d{4}-\d{2}-\d{2}_[0-9a-f]{56}\.eml)')
for line in record_file:
    line_match = line_pattern.match(line)
    if line_match:
        existing[line_match.group('luid')] = line_match.group('filename')
    else:
        print "Can't understand line in record file"
record_file.close()

record_file = open('record.txt', 'a')
for label in labels:
    mailbox = ImapMailbox((server, label))
    for uid in mailbox.get_all_uids():
        if existing.has_key("%s.%s" % (label, uid)):
            print "Skip %s.%s" % (label, uid) # DEBUG
            continue
        message = mailbox.get(uid)
        msg_string = message.as_string()
        filename = "%04i-%02i-%02i" % message.internaldate[:3]
        filename += "_%s.eml" % hashlib.sha224(msg_string).hexdigest()
        outfile = open(filename, 'w')
        outfile.write(msg_string)
        outfile.close()
        print >>record_file, "%s.%s : %s" % (label, uid, filename)
        print "Stored %s.%s" % (label, uid) # DEBUG
        record_file.flush()
    mailbox.close()
record_file.close()
