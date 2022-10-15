# Dependencies

To make it more likely that Lexbuilder will still run in a few
decades without hassle, we eschew the usual 'depend on everything'
party, use as few dependencies as possible, and include them fully in
this directory.

Lexbuilder should be able to run with no external dependencies other
than the Python Standard Library.

# bottle.py

"Bottle is a fast, simple and lightweight WSGI micro web-framework for
Python. It is distributed as a single file module and has no
dependencies other than the Python Standard Library."

https://raw.githubusercontent.com/bottlepy/bottle/master/bottle.py

# nestedtext

"NestedText is a file format for holding structured data to be entered,
edited, or viewed by people. It organizes the data into a nested
collection of dictionaries, lists, and strings without the need for
quoting or escaping. A unique feature of this file format is that it
only supports one scalar type: strings.  While the decision to eschew
integer, real, date, etc. types may seem counter intuitive, it leads
to simpler data files and applications that are more robust."

https://github.com/KenKundert/nestedtext

# inform

A support library required by 'nestedtext' by the same author.

"Library of print utilities used when outputting messages for the user from command-line programs"

https://github.com/KenKundert/inform
