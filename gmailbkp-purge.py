#!/usr/bin/env python
"""Delete all eml files that are not references in record"""
from ProcImap.ImapMailbox import ImapMailbox
from ProcImap.Utils.MailboxFactory import MailboxFactory
import re
import os
import sys
import shutil
from glob import glob
from optparse import OptionParser

arg_parser = OptionParser(usage = "gmailbkp-purge.py [options] [PATH]",
                            description = __doc__)

arg_parser.add_option('-v', action='store_true', dest='verbose',
                    default=False, help="Show status messages")
arg_parser.add_option('-c', action='store', dest='config',
                    default=os.environ['HOME']+"/.gmailbkp.conf", 
                    help="Use config file (default: ~/.gmaibkp.conf)")
arg_parser.add_option('-r', action='store', dest='record',
                    default='record.txt', 
                    help="record file (default: record.txt)")
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

try:

    server = mailboxes.get_server('Gmail')
    labels = server.list()

    # read in record
    record = {}
    shutil.copy(options.record, "%s~" % options.record)
    record_file = open("%s~" % options.record)
    line_pattern = re.compile(r'(?P<luid>.*\.\d+) : (?P<filename>\d{4}-\d{2}-\d{2}_[0-9a-f]{56}\.eml)')
    for line in record_file:
        line_match = line_pattern.match(line)
        if line_match:
            record[line_match.group('luid')] = line_match.group('filename')
        else:
            print "Can't understand line in record file"
    record_file.close()
    labeluids = record.keys()
    labeluids.sort()

    # delete those labels from the record that are not on the server
    for labeluid in labeluids:
        record_label = re.split("\.\d+$", labeluid)[0]
        if record_label not in labels:
            del record[labeluid]
            if options.verbose: print "Deleted %s (deleted label %s) " % (
                                      labeluid, record_label) + "from record"
    labeluids = record.keys()
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
            del record[labeluid]
            if options.verbose: print "Deleted %s from record" % labeluid
    if mailbox is not None: mailbox.close()
    labeluids = record.keys()
    labeluids.sort()

    # write out result
    record_file = open(options.record, 'w')
    for labeluid in labeluids:
        print >>record_file, "%s : %s" % (labeluid, record[labeluid])

    # delete those files that are not in filenames
    filenames = set(record.values())
    for filename in glob('*.eml'):
        if filename not in filenames:
            os.remove(filename)
            if options.verbose: print "Removed file %s" % filename

except Exception, message:
    print "Program ended with exception. Run again."
    print message

