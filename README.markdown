# gmailbkp

Collection of scripts to maintain a local backup of your [Gmail][] emails.

[Gmail]: http://www.gmail.com

[http://github.com/goerz/gmailbkp](http://github.com/goerz/gmailbkp)

Author: [Michael Goerz](http://michaelgoerz.net)

This code is licensed under the [GPL](http://www.gnu.org/licenses/gpl.html)

## Install ##

Store the scripts anywhere in your `$PATH`

## Dependencies ##

* [procimap](http://github.com/goerz/procimap)


## Configuration ##

You should create a file `~/.gmailbkp.conf` in which you save the credentials
for you Gmail account. An example:

    [Gmail]
    type = IMAP
    mailbox = INBOX
    server = imap.gmail.com
    username = myname@gmail.com
    password = mysecretpassword


## Usage ##

The tools work in conjunction to keep a backup of your Gmail messages. Most
importantly, `gmailbkp-fetch.py` will download emails from your Gmail account
and store them locally. `gmailbkp-purge.py` will delete emails locally that
were deleted in your Gmail account. You have to run both of these to have a
full mirror of your Gmail account.

You may set up both of these file as a cron-job to run once day or so, e.g.

     0 20 * * * *  gmailbkp-fetch.py -s --maildir ~/GmailBackup
     0 22 * * * *  gmailbkp-purge.py --maildir ~/GmailBackup

This would maintain a backup of your emails in the `~/GmailBackup` folder. If
you want to keep a backup that protects you from accidental deletion, you might
only want to run `gmailbkp-fetch.py` scheduled, and run `gmailbkp-purge.py`
manually, if at all.

The remaining three scripts are for maintenance.

`gmailbkp-cleanrecord.py` removes entries from the record that reference
non-existing eml files (in case you have accidentally deleted some of the local
eml files, this allows you to you to re-download these files the next time you
run `gmailbkp-fetch.py`)

`gmailbkp-missing-emls.py` lists entries in the record that have no
correspondint eml file. This gives you a preview of the entries that would be
deleted by `gmailbkp-cleanrecord.py`.

`gmailbkp-showmissing.py` lists the emails that are present on the server, but
not in the local record. These emails will be downloaded the next time you run
`gmailbkp-fetch.py`.

The full usage of the five scripts is as follows.

### gmailbkp-fetch.py ###

    Usage: gmailbkp-fetch.py [options] [FOLDER]

    Download all the messages in a Gmail acccount to eml files in the given
    FOLDER. Keep track of emails and labels in a record file

    Options:
      -h, --help         show this help message and exit
      -v                 Show status messages
      -c CONFIG          Use config file (default: ~/.gmaibkp.conf)
      -r RECORD          record file (default: record.txt). The filename is
                         relative to the given FOLDER
      -p                 Print names of newly created eml files
      -s                 Add the labels '[Gmail]/Trash' and '[Gmail]/Spam' to the
                         exclude list.
      --include=INCLUDE  Skip the labels NOT in this list (comma separated)
      --exclude=EXCLUDE  Skip the labels in this list (comma separated)
      --search=SEARCH    Only store emails that match the specified search. The
                         search string should be like the search syntax of the
                         IMAP search command (RFC3501). E.g. ('FLAGGED SINCE
                         1-Feb-1994 NOT FROM "Smith"'
      --maildir          Store eml files in a pseudo-maildir format. The folders
                         'new', 'cur', and 'tmp' will be created and all eml files
                         will be written to 'cur'. The name of the eml files are
                         not consistent with the maildir standard, but mutt will
                         be able to read the folder as a maildir mailbox
                         nonetheless
      --raise            Raise full exceptions

### gmailbkp-purge.py ###

    Usage: gmailbkp-purge.py [options] [FOLDER]

    Remove all emails from the record that were deleted from the server.  Delete
    all eml files that are not referenced in the record.

    Options:
      -h, --help  show this help message and exit
      -v          Show status messages
      -c CONFIG   Use config file (default: ~/.gmaibkp.conf)
      -r RECORD   record file (default: record.txt)
      --local     Do not connect to the server. Only remove eml files that are not
                  referenced in the record, locally
      --maildir   Look for eml files inside the 'cur' subfolder of the given
                  FOLDER

### gmailbkp-cleanrecord.py ###

    Usage: gmailbkp-cleanrecord.py [options] [FOLDER]

    Remove all entries from the record file that link to non-exisiting eml  files

    Options:
      -h, --help  show this help message and exit
      -c CONFIG   Use config file (default: ~/.gmaibkp.conf)
      -r RECORD   record file (default: record.txt). The filename is relative to
                  the given FOLDER
      --maildir   Look for eml files inside the 'cur' subfolder of the given
                  FOLDER

### gmailbkp-missing-emls.py ###

    Usage: gmailbkp-missing-emls.py [options] [FOLDER]

    List all the eml files that are referenced in the record file but do not exist

    Options:
      -h, --help  show this help message and exit
      -c CONFIG   Use config file (default: ~/.gmaibkp.conf)
      -r RECORD   record file (default: record.txt). The filename is relative to
                  the given FOLDER
      --maildir   Look for eml files inside the 'cur' subfolder of the given
                  FOLDER

### gmailbkp-showmissing.py ###

    Usage: gmailbkp-fetch.py [options] [FOLDER]

    List all the messages in a Gmail acccount that are not in the record file

    Options:
      -h, --help         show this help message and exit
      -c CONFIG          Use config file (default: ~/.gmaibkp.conf)
      -r RECORD          record file (default: record.txt). The filename is
                         relative to the given FOLDER
      -s                 Add the labels '[Gmail]/Trash' and '[Gmail]/Spam' to the
                         exclude list.
      --include=INCLUDE  Skip the labels NOT in this list (comma separated)
      --exclude=EXCLUDE  Skip the labels in this list (comma separated)
      --search=SEARCH    Only store emails that match the specified search. The
                         search string should be like the search syntax of the
                         IMAP search command (RFC3501). E.g. ('FLAGGED SINCE
                         1-Feb-1994 NOT FROM "Smith"'
      --raise            Raise full exceptions
      --summary          Show a summary (sender, date, subject) of the missing
                         messages
