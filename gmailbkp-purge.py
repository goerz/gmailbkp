#!/usr/bin/env python
"""Remove all emails from the record that were deleted from the server.
Delete all eml files that are not referenced in the record."""

try:
    from ProcImap.ImapMailbox import ImapMailbox
    from ProcImap.Utils.MailboxFactory import MailboxFactory
    procimap_loaded = True
except ImportError:
    print "ProcImap is not available. Cannot connect to Gmail server."
    print "Script will be limited to deleting eml files not present in the" \
           "record."
    procimap_loaded = False
import re
import os
import sys
import shutil
from glob import glob
from optparse import OptionParser

arg_parser = OptionParser(usage = "gmailbkp-purge.py [options] [FOLDER]",
                            description = __doc__)

arg_parser.add_option('-v', action='store_true', dest='verbose',
                    default=False, help="Show status messages")
arg_parser.add_option('-c', action='store', dest='config',
                    default=os.environ['HOME']+"/.gmailbkp.conf",
                    help="Use config file (default: ~/.gmaibkp.conf)")
arg_parser.add_option('-r', action='store', dest='record',
                    default='record.txt',
                    help="record file (default: record.txt)")
arg_parser.add_option('--local', action='store_true', dest='local',
                    default=False, help="Do not connect to the server. "
                    "Only remove eml files that are not referenced in the "
                    "record, locally")
arg_parser.add_option('--maildir', action='store_true', dest='maildir',
                    default=False, help="Look for eml files inside the 'cur' "
                    "subfolder of the given FOLDER")

options, args = arg_parser.parse_args(sys.argv)
if len(args) > 1:
    os.chdir(args[1])
if options.maildir:
    options.record = os.path.join('..', options.record)
    os.chdir('cur')


try:
    # read in record
    record = {}
    shutil.copy(options.record, "%s~" % options.record)
    record_file = open("%s~" % options.record)
    line_pattern = re.compile(
    r'(?P<luid>.*\.\d+) : ''(?P<filename>\d{4}-\d{2}-\d{2}_[0-9a-f]{56}\.eml)')
    for line in record_file:
        line_match = line_pattern.match(line)
        if line_match:
            record[line_match.group('luid')] = line_match.group('filename')
        else:
            print "Can't understand line in record file"
    record_file.close()
    labeluids = record.keys()
    labeluids.sort()

    if procimap_loaded and not options.local:
        # delete those labels from the record that are not on the server
        mailboxes = MailboxFactory(options.config)
        server = mailboxes.get_server('Gmail')
        labels = server.list()
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
    shutil.copy("%s~" % options.record, options.record)
    print "Program ended with exception. Run again."
    print message

