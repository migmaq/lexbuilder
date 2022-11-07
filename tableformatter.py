import markupsafe
import util
from util import deref
#import openpyxl

class TableFormatter(object):
    """A TableFormatter is a convenient way to render an instance list
    to a html table.

    Has some weird power we don't need for MMO + should be more integrated
    with the entity model stuff - but we mostly repurposed this from
    something else ... so there you go.
    """
    
    def __init__ (self, cellFormatters=[], detailRowFormatter=None, groupTitleFormatter=None, everyRowIsNewGroup=False, suppressHeadRow=False,
                  cssClass='entity-browser', caption=None, note=None, properties=None):
        self.cellFormatters = cellFormatters[:]
        self.detailRowFormatter = detailRowFormatter
        self.groupTitleFormatter = groupTitleFormatter
        self.everyRowIsNewGroup = everyRowIsNewGroup
        self.suppressHeadRow = suppressHeadRow
        self.cssClass = cssClass
        self.caption = caption
        self.note = note
        self.properties = properties or {}

    @property
    def colspan (self):
        return len(self.cellFormatters)

    def formatTable (self, rows, clazz=None):
        clazz = clazz or self.cssClass

        lines = []
        if self.note:
            lines.append ('<div class="important-note">{note}</div>'.format (note=markupsafe.escape (self.note)))
        lines.append ('<table class="{clazz}">'.format (clazz=clazz))
        if self.caption:
            lines.append ('<caption>{caption}</caption>'.format (caption=markupsafe.escape (self.caption)))
        if not self.suppressHeadRow:
            lines.append ('<thead>')
            lines.append (self.formatHeadRow ())
            lines.append ('</thead>')
        lines.append ('<tbody>')

        currentGroupBeginRow = None
        currentGroupTitle = None
        groupLines = []
        groupRows = []
        
        for row in rows:

            # If we have a group formatter, give it a chance to start a new group
            if self.groupTitleFormatter:
                newGroupTitle = self.groupTitleFormatter.format (row)
                if newGroupTitle != currentGroupTitle or self.everyRowIsNewGroup:

                    # Format header line for group that was just completed (if we had a previous group)
                    if currentGroupBeginRow:
                        lines.append (self.formatGroupBeginRow (currentGroupBeginRow, currentGroupTitle, groupRows))

                    # Flush output lines for group that was just completed
                    lines += groupLines

                    # Start new group with current begin row and group title
                    groupLines = []
                    groupRows = []
                    currentGroupBeginRow = row
                    currentGroupTitle = newGroupTitle

            # Format a normal row
            groupLines.append (self.formatRow (row))

            # Optionally format a detail row
            if self.detailRowFormatter:
                groupLines.append (self.formatDetailRow (row))

            groupRows.append (row)

        # Format header line for group that was just completed (if we have a current group)
        if currentGroupBeginRow:
            lines.append (self.formatGroupBeginRow (currentGroupBeginRow, currentGroupTitle, groupRows))

        # Flush output lines for group that was just completed
        lines += groupLines

        lines.append ('</tbody>')
        lines.append ('</table>')

        return '\n'.join (lines)

    def formatHeadRow (self):
        lines = []
        lines.append ('<tr>')
        for c in self.cellFormatters:
            lines.append ('<th>'+str(c.formatTitle ())+'</th>')
        lines.append ('</tr>')
        return '\n'.join (lines)

    def formatRow (self, row):
        lines = []
        lines.append (self.formatRowBegin (row))
        for c in self.cellFormatters:
            if isinstance (c, CellFormatterThatReceivesTableProperties):
                formattedValue = c.format (row, self.properties)
            else:
                formattedValue = c.format (row)
            cellCssClass = c.getCssClass ()
            l = '<td'+(' class="'+cellCssClass+'"' if cellCssClass else '')+'>'+str(formattedValue)+'</td>'
            lines.append (l)
        lines.append (self.formatRowEnd (row))
        return '\n'.join (lines)
    
    def formatRowBegin (self, row):
        return '<tr>'

    def formatRowEnd (self, row):
        return '</tr>'

    def formatDetailRow (self, row):
        return self.formatDetailRowBegin (row)+\
            str (self.detailRowFormatter.format (row))+\
            self.formatDetailRowEnd (row)
    
    def formatDetailRowBegin (self, row):
        return '<tr><td colspan={colspan} class=detail>'.format (colspan=self.colspan)

    def formatDetailRowEnd (self, row):
        return '</tr>'

    def formatGroupBeginRow (self, row, groupTitle, groupRows):
        return u"""<tr><td colspan={colspan} class=groupBegin><h2>{title} ({groupSize})</h2></tr>""".format\
            (colspan=self.colspan, title=groupTitle, groupSize=len(groupRows))


    # def exportTable (self, rows, fileName):
    #     from openpyxl import Workbook
    #     wb = Workbook()
    #     ws = wb.active

    #     # self.caption ??? - seems not to be used - but might be nice.
        
    #     currentGroupTitle = None

    #     exportedHeadRow = self.exportHeadRow ()
    #     if exportedHeadRow:
    #         ws.append (exportedHeadRow)

    #     for row in rows:

    #         # If we have a group formatter, give it a chance to start a new group
    #         if self.groupTitleFormatter:
    #             newGroupTitle = self.groupTitleFormatter.format (row)
    #             if newGroupTitle != currentGroupTitle or self.everyRowIsNewGroup:
    #                 currentGroupTitle = newGroupTitle
    #                 ws.append ([currentGroupTitle])

    #         # Format a normal row
    #         exportedRow = self.exportRow (row)
    #         if exportedRow:
    #             ws.append (exportedRow)

    #         # Optionally format a detail row
    #         if self.detailRowFormatter:
    #             pass  # not supported on export for now

    #     wb.save (fileName)
        
    def exportHeadRow (self):
        return [c.formatTitle () for c in self.cellFormatters if c.export]

    def exportRow (self, row):
        return [c.getExportValue (row) for c in self.cellFormatters if c.export]
    
    def clone ():
        return TableFormatter (self.cellFormatters, self.detailRowFormatter, self.groupTitleFormatter)

    def get (self, ref):
        return self.cellFormatters[self.getIndex(ref)]

    def append (self, cell):
        self.cellFormatters.append (cell)
        return self

    def remove (self, ref):
        self.cellFormatters.pop (self.getIndex (ref))
        return self

    def insertBefore (self, ref, cell):
        self.cellFormatters.insert (self.getIndex (ref), cell)
        return self

    def insertAfter (self, ref, cell):
        self.cellFormatters.insert (self.getIndex (ref)+1, cell)
        return self

    def getIndex (self, ref):
        """Return the index of a cell giving a reference which may be an index,
        a name or a cell.
        """
        if isinstance(ref, int):
            return ref
        elif isinstance(ref, str):
            name = ref
        elif isinstance(ref, CellFormatter):
            name = ref.name
        else:
            raise RuntimeError ('Unrecognized reference '+ref)

        for i in range (0, len(self.cellFormatters)):
            if self.cellFormatters[i].name == name:
                return i
        else:
            raise RuntimeError ('Unable to find cell named '+name)
            

#def optEscape (v, escape=False):
#    return markupsafe.escape (v) if escape else v

class CellFormatter(object):

    defaultTitle = None
    export = True
    
    def __init__ (self, name=None, title=None, escape=True):
        self.name = name
        self.title = title
        self.escape = escape

    def getCssClass (self):
        return None
    
    def formatTitle (self):
        return markupsafe.escape (self.title or 
                                  util.upperFirstLetter (util.camelCaseToWords (self.name)) or
                                  self.defaultTitle or '')

    def getValue (self, row):
        #if not self.name: print 'BOO', repr (self)
        return deref (row, self.name)

    def getExportValue (self, row):
        return self.getValue (row)
    
    def format (self, row):
        raise RuntimeError ('no formatter defined for '+self.__class__.__name__)

    def optEscape (self, v):
        return markupsafe.escape (v) if self.escape else v

    def getTargetUrl (self, row):
        return 'foo.html'
    
class CellFormatterThatReceivesTableProperties(CellFormatter):
    def format (self, row, tableProperties={}):
        raise RuntimeError ('no formatter defined for '+self.__class__.__name__)
    

class StringFormatter(CellFormatter):
    def format (self, row):
        value = self.getValue (row)
        if value is None: return ''
        return self.optEscape (value)

class IntFormatter(CellFormatter):
    def getCssClass (self): return 'textAlignRight'
    def format (self, row):
        value = self.getValue (row)
        if value is None: return ''
        return str(value)

class BoolFormatter(CellFormatter):
    def format (self, row):
        value = self.getValue (row)
        return {True: 'Yes', False: 'No', None: ''}.get (value, str (value))

class DateFormatter(CellFormatter):
    def format (self, row):
        value = self.getValue (row)
        return util.ymd (value)

class DateTimeFormatter(CellFormatter):
    def format (self, row):
        value = self.getValue (row)
        return value.strftime ('%I:%M %p %A %B %d') if value else ''

class PrimaryKeyLink (CellFormatter):

    def getExportValue (self, row):
        return str (self.getValue (row))

    def format (self, row):
        value = self.getValue (row)
        if value is None: return ''
        if value == '': value = '_'
        target = self.getTargetUrl(row)
        return '<a href="{href}">{label}</a>'.\
            format (href=target, label=self.optEscape (value))

class PrimaryKeyLinkWithPreview (CellFormatter):

    def getExportValue (self, row):
        return str (self.getValue (row))

    def format (self, row):
        value = self.getValue (row)
        if value is None: return ''
        if value == '': value = '_'
        return '<a href="{href}" class="previewController" data-preview-url="{href}">{label}</a>'.\
            format (href=row, 
                    label=self.optEscape (value))


class Preview (CellFormatter):
    export = False
    
    def __init__ (self, name='*', *args, **kwargs):
        super (Preview, self).__init__ (name, *args, **kwargs)
        
    def format (self, row):
        return '<span class=preview data-tooltip-url="{href}/tooltip">*</a>'.\
            format (href=row)


class EditButton (CellFormatter):
    export = False
    
    def __init__ (self, name, dialogName='editDialog', *args, **kwargs):
        super (EditButton, self).__init__ (name, *args, **kwargs)
        self.dialogName = dialogName

    def format (self, row):
        return '<a class="action noprint" data-action="{href}/{dialogName}">{label}</a>'.\
            format (href=row, dialogName=self.dialogName, label='Edit')


class DeleteButton (CellFormatter):
    export = False

    def format (self, row):
        return '<a class="action" data-action="{href}/setDeletedAction" data-confirm="Are you sure you want to delete?">{label}</a>'.\
            format (href=row, label='Delete')


class NoConfirmDeleteButton (CellFormatter):
    export = False

    def format (self, row):
        return '<a class="action" data-action="{href}/setDeletedAction">{label}</a>'.\
            format (href=row, label='Delete')


class OpenButton (CellFormatter):
    export = False

    def format (self, row):
        return '<a href="{href}">Open</a>'.format (href=row)


class LambdaFormatter(CellFormatter):
    def __init__ (self, name, fn, **kwargs):
        super(LambdaFormatter, self).__init__(name, **kwargs)
        self.fn = fn

    def getValue (self, row):
        return self.fn (row)
        
    def format (self, row):
        return self.optEscape (self.getValue (row))


class LambdaValueFormatter(CellFormatter):
    def __init__ (self, name, fn, filterNone=True, **kwargs):
        super(LambdaValueFormatter, self).__init__(name, **kwargs)
        self.fn = fn
        self.filterNone = filterNone

    def getValue (self, row):
        v = super(LambdaValueFormatter, self).getValue (row)
        if v is None and self.filterNone: return None
        return self.fn (v)
        
    def format (self, row):
        value = self.getValue (row)
        if value is None and self.filterNone: return ''
        return self.optEscape (self.fn (value))


class EnumFormatter(CellFormatter):
    def __init__ (self, name, enum, **kwargs):
        super(EnumFormatter, self).__init__(name, **kwargs)
        self.enum = enum

    def getExportValue (self, row):
        return self.enum.__label__ (self.getValue (row))
        
    def format (self, row):
        value = self.getValue (row)
        if value is None: return ''
        return self.enum.__label__ (value)


class ContentLinkFormatter(CellFormatter):

    def getExportValue (self, row):
        value = self.getValue (row)
        if value is None:
            return None
        elif hasattr (value, 'getAnchorText'):
            return value.getAnchorText ()
        else:
            return str (value)

    def format (self, row):
        value = self.getValue (row)
        if value is None: return ''
        if hasattr (value, 'getAnchorText'):
            label = value.getAnchorText ()
        else:
            label = value
        return '<a href="{href}">{label}</a>'.\
            format (href=value, label=self.optEscape (label))



def test ():

    class TestJob (object):
        def __init__ (self, title): self.title=title
        def getTitle (self): return self.title

    programTester = TestJob ('Program Tester')

    class TestPerson (object):
        def __init__ (self, name, job):
            self.name = name
            self.job = job

    f = TableFormatter ()
    f.append (StringFormatter ('name'))
    f.append (ContentLinkFormatter ('job'))

    print(f.formatTable ([TestPerson ('David', programTester),
                          TestPerson ('Lesley', programTester)]))

if __name__ == "__main__":
    test ()
