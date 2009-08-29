#!/usr/bin/env python
"""Delete all emails from record.txt that are not on the server anymore"""
from ProcImap.ImapMailbox import ImapMailbox
from ProcImap.Utils.MailboxFactory import MailboxFactory
import re
import os
import sys
import shutil
from optparse import OptionParser

arg_parser = OptionParser(usage = "gmailbkp-fetch.py [options] [path]",
                            description = __doc__)

arg_parser.add_option('-v', action='store_true', dest='verbose',
                    default=False, help="Show status messages")
arg_parser.add_option('-c', action='store', dest='config',
                    default=os.environ['HOME']+"/.gmailbkp.conf", 
                    help="Use config file (default: ~/.gmaibkp.conf)")

options, args = arg_parser.parse_args(sys.argv)
if len(args) > 1:
    os.chdir(args[1])


mailboxes = MailboxFactory(options.config)

labeluids = []
try:
    server = mailboxes.get_server('Gmail')

    labels = server.list()

    # read in existing record
    existing = {}
    shutil.copy('record.txt', 'record.txt~')
    record_file = open('record.txt~')
    line_pattern = re.compile(r'(?P<luid>.*\.\d+) : (?P<filename>\d{4}-\d{2}-\d{2}_[0-9a-f]{56}\.eml)')
    for line in record_file:
        line_match = line_pattern.match(line)
        if line_match:
            existing[line_match.group('luid')] = line_match.group('filename')
        else:
            print "Can't understand line in record file"
    record_file.close()
    labeluids = existing.keys()
    labeluids.sort()


    # delete those labels from the record that are not on the server
    for labeluid in labeluids:
        record_label = re.split("\.\d+$", labeluid)[0]
        if record_label not in labels:
            del existing[labeluid]
            if options.verbose: print "Deleted %s (deleted label %s)" % (
                                      labeluid, record_label)
    labeluids = existing.keys()
    labeluids.sort()

    # delete missing uids
    label = ''
    mailbox = None
    uids = []
    for labeluid in labeluids:
        record_label = re.split("\.\d+$", labeluid)[0]
        if (label != record_label):
            label = record_label
            if mailbox is not None: mailbox.close()
            mailbox = ImapMailbox((server, label))
            uids = mailbox.get_all_uids()
        uid = int(re.split("^.*\.", labeluid)[1])
        if uid not in uids:
            del existing[labeluid]
            if options.verbose: print "Deleted %s" % labeluid
    if mailbox is not None: mailbox.close()
    labeluids = existing.keys()
    labeluids.sort()
except Exception, message:
    print "Program ended with exception. Run again."
    print message

# write out result
record_file = open('record.txt', 'w')
for labeluid in labeluids:
    print >>record_file, "%s : %s" % (labeluid, existing[labeluid])
record_file.close()
