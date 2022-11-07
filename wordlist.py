import mmodb
import io
from deps.bottle import html_escape as escape, html_quote, template
import textwrap
from tableformatter import *


def wordlist():

    f = TableFormatter()
    #f.append(StringFormatter('definition', title="Definition"))
    f.append(PrimaryKeyLink('definition', title="Definition"))

    db = mmodb.get_mmo_db()
    entries = db.entries.find()

    entries_table_html = f.formatTable(entries)

    return entries_table_html



    
