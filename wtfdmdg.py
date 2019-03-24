#
# wtfdmdg.py
#
# Where The Fuck Did My Day Go, dot pie
#
# A tool to help answer that question.
#

from PyQt5 import Qt, QtGui, QtWidgets, QtCore
import pyqtgraph as pg

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import sys
import re
import collections
import datetime
import time
import pickle
import os
import itertools
import pylab
from pathlib import Path

Task = collections.namedtuple( "Task", ( "ref", "begin", "end", "body" ) )

APPDATA_DIR = os.path.join( str( Path.home() ), ".local", "share", "wtfdmdg" )

CMAP = 'gist_rainbow'

def FILE_PATH( dt ):
    return os.path.join( APPDATA_DIR, datetime.datetime.strftime( dt, "%y-%m-%d.pickle" ) )

class WtfdmdgCommandParserInterface( object ):

    def getCommandLineHighlighter( self, document ):
        """
        Return a QSyntaxHighlighter
        """
        raise NotImplementedError

    def getTagBankHighlighter( self, document ):
        """
        Return a QSyntaxHighlighter
        """
        raise NotImplementedError

    def execute( self, session, line ):
        """
        Evaluate line and execute against session
        """
        raise NotImplementedError

    def getTaskTags( self, body ):
        """
        Return a dict mapping tag class to a list of tags, given
        the body of a task.
        """
        raise NotImplementedError

    def encodeTask( self, task ):
        """
        Return a command string that yields this task exactly
        """
        raise NotImplementedError

class WtfdmdgDefaultCommandParser( WtfdmdgCommandParserInterface ):

    REF   = r"(?:(?P<ref>(?:\d+)|\*):)?"
    BODY  = r"(?:(?P<body>.+))?"
    TIME  = r"(?:\d+)|n"
    BEGIN = r"(?:(?P<begin>" + TIME + "))?"
    END   = r"(?:(?P<end>" + TIME + "))?"
    TAG   = r"(/+)(\S+)"

    TAG_REGEX     = re.compile( TAG )
    LINE_REGEX    = re.compile( REF + BEGIN + "-?" + END + "\.?" + BODY )
    TAGBANK_REGEX = re.compile( r"\S+" )

    class CommandLineSyntaxHighlighter( QtGui.QSyntaxHighlighter ):
        def __init__( self, parser, document ):
            super( WtfdmdgDefaultCommandParser.CommandLineSyntaxHighlighter, self ).__init__( document )
            self.parser = parser
        def highlightBlock( self, block ):
            for rng, fmt in zip( self.parser._getRanges( block ), self.parser._getFormats() ):
                if rng[0] >= 0 and rng[1] >= 0:
                    self.setFormat( rng[0], rng[1], fmt )

    class TagBankSyntaxHighlighter( QtGui.QSyntaxHighlighter ):
        def __init__( self, parser, tagclass, document ):
            super( WtfdmdgDefaultCommandParser.TagBankSyntaxHighlighter, self ).__init__( document )
            self.parser = parser
            self.tagclass = tagclass
        def highlightBlock( self, block ):
            app = WtfdmdgApplication.instance()
            if self.tagclass is not app.getSelectedTagClass():
                # Nothing to do
                return
            tagRanges = self.parser._getTagBankRanges( block )
            tagColors = [ app.getTagColor( self.tagclass, block[ x[0]:x[1] ] ) for x in tagRanges ]
            for rng, clr in zip( tagRanges, tagColors ):
                if rng[0] >= 0 and rng[1] >= 0:
                    fmt = QtGui.QTextCharFormat()
                    fmt.setFontWeight( QtGui.QFont.Bold )
                    fmt.setForeground( QtGui.QColor( *clr ) )
                    self.setFormat( rng[0], rng[1], fmt )

    def getCommandLineHighlighter( self, document ):
        return WtfdmdgDefaultCommandParser.CommandLineSyntaxHighlighter( self, document )

    def getTagBankHighlighter( self, tagclass, document ):
        return WtfdmdgDefaultCommandParser.TagBankSyntaxHighlighter( self, tagclass, document )

    def execute( self, tasks, line ):
        app = WtfdmdgApplication.instance()
        ref, begin, end, body = self._getParts( line )
        begin = self._getDatetime( begin )
        end = self._getDatetime( end )
        if all( x is None for x in [ ref, begin, end, body ] ):
            print( "NOP" )
        elif ref is not None and all( x is None for x in ( begin, end, body ) ):
            if ref != "*":
                del tasks[ int( ref ) ]
        elif ( ref is None or int( ref ) not in app.session ) and any( x is not None for x in [ begin, end, body ] ):
            if body is None:
                # New tasks must always have body
                print( "NOP" )
            else:
                ref = int( ref or app.generateTaskId() )
                tasks[ int( ref ) ] = Task( ref, begin, end, body )
        elif ref != "*":
            a, b, c, d = tasks[ int( ref ) ]
            if begin is not None:
                b = begin
            if end is not None:
                c = end
            if body is not None:
                d = body
            tasks[ int( ref ) ] = Task( a, b, c, d )

    def getTaskTags( self, body ):
        tagtable = {}
        for tagmatch in WtfdmdgDefaultCommandParser.TAG_REGEX.findall( body ):
            tagclass = len( tagmatch[0] )
            tagtext = tagmatch[1].lower()
            if tagclass not in tagtable:
                tagtable[ tagclass ] = []
            if tagtext not in tagtable[ tagclass ]:
                tagtable[ tagclass ].append( tagtext )
        return tagtable

    def _getParts( self, line ):
        m = WtfdmdgDefaultCommandParser.LINE_REGEX.match( line )
        if m is None:
            return None
        return [ m.group( x ) for x in [ "ref", "begin", "end", "body" ] ]

    def _getRanges( self, line ):
        m = WtfdmdgDefaultCommandParser.LINE_REGEX.match( line )
        if m is None:
            return None
        return [ m.span( x ) for x in [ "ref", "begin", "end", "body" ] ]

    def _getTagBankRanges( self, line ):
        return [ m.span() for m in WtfdmdgDefaultCommandParser.TAGBANK_REGEX.finditer( line ) ]

    def _getFormats( self ):
        reff   = QtGui.QTextCharFormat()
        beginf = QtGui.QTextCharFormat()
        endf   = QtGui.QTextCharFormat()
        bodyf  = QtGui.QTextCharFormat()

        reff.setFontWeight( QtGui.QFont.Bold )

        beginf.setFontWeight( QtGui.QFont.Bold )
        beginf.setForeground( QtGui.QColor( 100, 100, 255 ) )

        endf.setFontWeight( QtGui.QFont.Bold )
        endf.setForeground( QtGui.QColor( 200, 200, 0 ) )

        bodyf.setForeground( QtGui.QColor( 255, 0, 0 ) )
        bodyf.setFontWeight( QtGui.QFont.Bold )

        return [ reff, beginf, endf, bodyf ]

    def _getDatetime( self, string ):
        if string is None:
            return None
        if string == "n":
            return datetime.datetime.now()
        if string.isdigit():
            if len( string ) <= 2:
                hr = int( string )
                mn = 0
            else:
                mn = int( string[-2:] )
                hr = int( string[ :-2 ] )
            dt = datetime.datetime.now()
            dt = dt.replace( hour=hr, minute=mn )
            return dt
        assert( False )
        return None

    def encodeTask( self, task ):
        text = ""
        if task.ref is not None:
            text += str( task.ref ) + ":"
        if task.begin is not None:
            text += datetime.datetime.strftime( task.begin, "%H%M" )
        if task.end is not None:
            text += "-" + datetime.datetime.strftime( task.end, "%H%M" )
        if task.body is not None:
            text += "." + task.body
        return text

class WtfdmdgApplication( QtWidgets.QApplication ):

    def __init__( self, argv, parser=None ):
        """
        Initialize application
        """
        super( WtfdmdgApplication, self ).__init__( argv )
        self.session = {}
        self.tagtable = {}
        self.selectedTask = None
        if parser is None:
            parser = WtfdmdgDefaultCommandParser()
        self._tagColorMap = pylab.get_cmap( CMAP )
        self._commandParser = parser
        self.loadFile()
        self._mainWindow = WtfdmdgMainWindow()
        self._mainWindow._commandTextEdit.setFocus()
        self.redraw()

    def loadFile( self, path=None ):
        """
        Load state from file.
        """
        path = path or FILE_PATH( datetime.datetime.now() )
        if os.path.exists( path ):
            self.session = pickle.load( open( path, 'rb' ) )
            self.__refreshTags()

    def dumpFile( self ):
        """
        Export state to file
        """
        if not os.path.exists( APPDATA_DIR ):
            os.makedirs( APPDATA_DIR )
        pickle.dump( self.session, open( FILE_PATH( datetime.datetime.now() ), 'wb' ) )

    def redraw( self ):
        """
        Redraw application
        """
        self._mainWindow._taskTable.redraw( self.session )
        self._mainWindow._tagTable.redraw( self.tagtable )
        self._mainWindow._timelineWidget.redraw()

    def processLine( self, line ):
        """
        Parse and process a line of input
        """
        self._commandParser.execute( self.session, line )
        self.__refreshTags()
        self.dumpFile()
        self.deselectTask()
        self.redraw()

    def checkTaskSelect( self, line ):
        """
        Check to see if we should select a task
        """
        ref, _, _, _ = self._commandParser._getParts( line )
        if ref is not None:
            if ref.isdigit():
                self.selectTaskByRef( int( ref ) )
            else:
                self.deselectTask()
        else:
            self.deselectTask()

    def getCommandLineHighlighter( self, doc ):
        """
        Apply highlighting to command line document
        """
        return self._commandParser.getCommandLineHighlighter( doc )

    def getTagBankHighlighter( self, tagclass, doc ):
        """
        Apply highlighting to tagbank document
        """
        return self._commandParser.getTagBankHighlighter( tagclass, doc )

    def getTagColor( self, tagclass, tag ):
        """
        Get (r,g,b) color for tag in tagclass
        """
        assert( tagclass in self.tagtable and tag in self.tagtable[ tagclass ] )
        i = self.tagtable[ tagclass ].index( tag.lower() )
        nc = len( self.tagtable[ tagclass ] )
        return [ 255 * x for x in ( self._tagColorMap( float( i ) / nc )[:-1] ) ]

    def getSession( self ):
        """
        Return the current session
        """
        return self.session

    def getTags( self ):
        """
        Get the tags dict
        """
        return self.tagtable

    def getTagsForTask( self, task ):
        """
        Get tags referenced by this task
        """
        if task.body is None:
            return {}
        return self._commandParser.getTaskTags( task.body )

    def getSelectedTags( self ):
        """
        Return the list of selected tags
        """
        return self._mainWindow._tagTable.getSelectedTags()

    def getSelectedTagClass( self ):
        """
        Get the currently selected tag class
        """
        # TODO shouldn't be reaching into the widget here
        selectedRows = WtfdmdgApplication.instance()._mainWindow._tagTable.selectionModel().selectedRows()
        assert( len( selectedRows ) <= 1 )
        if len( selectedRows ) == 0:
            return None
        return selectedRows[0].row() + 1

    def generateTaskId( self ):
        """
        Create a unique task id
        """
        if len( self.session ) == 0:
            return 0
        return max( self.session.keys() ) + 1

    def getTaskByIndex( self, index ):
        """
        Get a task by its order in the session.
        """
        return self.__getSortedTaskList()[ index ]

    def getSelectedTask( self ):
        """
        Return the currently selected task
        """
        if self.selectedTask is not None:
            return self.session[ self.selectedTask ]
        return None

    def getSelectedTaskIndex( self ):
        """
        Get the index of the selected task
        """
        if self.selectedTask is None:
            return None
        refs = [ x.ref for x in self.__getSortedTaskList() ]
        assert( self.selectedTask in refs )
        return refs.index( self.selectedTask )

    def selectTaskByRef( self, ref ):
        """
        Set selected task by ref ID
        """
        if ref in self.session:
            self.selectedTask = ref

    def reverseTask( self, task ):
        """
        Return command string for task
        """
        return self._commandParser.encodeTask( task )

    def stepTask( self, offset ):
        """
        Advance task by positive/negative index count. Advancing past end
        or before start clears selection. When selection is clear, moving
        backward goes to last index, and moving forward goes to first index.

        No selection can be thought of as a final "invisible" item.
        """
        refs = [ x.ref for x in self.__getSortedTaskList() ] + [ None ]
        assert( self.selectedTask in refs )
        curi = refs.index( self.selectedTask )
        self.selectedTask = refs[ ( curi + offset ) % len( refs ) ]

    def selectNextTask( self ):
        """
        Select the next task
        """
        self.stepTask( 1 )

    def selectPreviousTask( self ):
        """
        Select the previous task
        """
        self.stepTask( -1 )

    def deselectTask( self ):
        """
        Don't select any tasks
        """
        self.selectedTask = None

    def __getSortedTaskList( self ):
        """
        Return list of tasks, sorted by start time.
        """
        tasks = self.session.values()
        startedTasks =   [ t for t in tasks if t.begin is not None ]
        unstartedTasks = [ t for t in tasks if t.begin is None ]
        return ( unstartedTasks + sorted( startedTasks, key=lambda r: r.begin ) )

    def __mergeTags( self, tags ):
        """
        Given a dict mapping tag class to tag list, merge it
        into self.tagtable.
        """
        for cls in tags:
            if cls not in self.tagtable:
                self.tagtable[ cls ] = []
            for tag in tags[ cls ]:
                if tag not in self.tagtable[ cls ]:
                    self.tagtable[ cls ].append( tag )

    def __refreshTags( self ):
        """
        Search current session for any tags.
        """
        self.tagtable = {}
        for task in self.session.values():
            self.__mergeTags( self._commandParser.getTaskTags( task.body ) )

class WtfdmdgMainWindow( QtWidgets.QMainWindow ):

    def __init__( self ):
        """
        Initialize application main window
        """
        super( WtfdmdgMainWindow, self ).__init__()

        # Create top-level layout
        topLevelLayout = QtWidgets.QVBoxLayout()
        topLevelLayout.setSpacing( 0 )
        topLevelLayout.setContentsMargins( 0, 0, 0, 0 )
        centralWidget = QtWidgets.QWidget();
        centralWidget.setLayout( topLevelLayout )
        self.setCentralWidget( centralWidget )

        anotherlayout = QtWidgets.QHBoxLayout()
        anotherlayout.setSpacing( 0 )
        anotherlayout.setContentsMargins( 0, 0, 0, 0 )

        anotherAnotherLayout = QtWidgets.QVBoxLayout()
        anotherAnotherLayout.setSpacing( 0 )
        anotherAnotherLayout.setContentsMargins( 0, 0, 0, 0 )

        # Add the widgets
        self._commandTextEdit = WtfdmdgCommandTextEdit()
        self._taskTable = WtfdmdgTaskTable()
        self._tagTable = WtfdmdgTagTable()
        self._timelineWidget = WtfdmdgTimelineWidget()

        anotherAnotherLayout.addWidget( self._tagTable )
        anotherAnotherLayout.addWidget( self._taskTable )
        anotherAnotherLayout.setStretch( 0, 1 )
        anotherAnotherLayout.setStretch( 1, 5 )

        anotherlayout.addLayout( anotherAnotherLayout )
        anotherlayout.addWidget( self._timelineWidget )
        anotherlayout.setStretch( 0, 2 )
        anotherlayout.setStretch( 1, 1 )

        topLevelLayout.addLayout( anotherlayout )
        topLevelLayout.addWidget( self._commandTextEdit )

        topLevelLayout.setStretch( 0, 999 )
        topLevelLayout.setStretch( 1, 1 )

        # Set title
        self.setWindowTitle( "Where The Fuck Did My Day Go?" )

        self.show()

class WtfdmdgCommandTextEdit( QtWidgets.QTextEdit ):

    def __init__( self ):
        """
        Initialize the command text edit.
        """
        super( WtfdmdgCommandTextEdit, self ).__init__()
        self.setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
        self._hilighter = WtfdmdgApplication.instance().getCommandLineHighlighter( self.document() )
        self.setFont( QtGui.QFontDatabase.systemFont( QtGui.QFontDatabase.FixedFont ) )
        self.setMinimumHeight( self.document().size().height() )

    def keyPressEvent( self, event ):
        """
        Capture some keys
        """
        if( event.key() == QtCore.Qt.Key_Return ):
            WtfdmdgApplication.instance().processLine( self.toPlainText() )
            self.clear()
        elif( event.key() == QtCore.Qt.Key_Down ):
            WtfdmdgApplication.instance().selectNextTask()
            task = WtfdmdgApplication.instance().getSelectedTask()
            self.preloadTask( task )
        elif( event.key() == QtCore.Qt.Key_Up ):
            WtfdmdgApplication.instance().selectPreviousTask()
            task = WtfdmdgApplication.instance().getSelectedTask()
            self.preloadTask( task )
        elif( event.key() == QtCore.Qt.Key_Escape ):
            self.clear()
        else:
            super( WtfdmdgCommandTextEdit, self ).keyPressEvent( event )

        WtfdmdgApplication.instance().checkTaskSelect( self.toPlainText() )

        WtfdmdgApplication.instance().redraw()

    def preloadTask( self, task ):
        """
        Set contents to this task
        """
        if task is None:
            self.setText( "" )
            return
        text = WtfdmdgApplication.instance().reverseTask( task )
        self.setText( text )

class WtfdmdgTaskTable( QtWidgets.QTableWidget ):

    def __init__( self ):
        """
        Initialize task table widget
        """
        super( WtfdmdgTaskTable, self ).__init__()
        self.setColumnCount( 4 )
        self.setGridStyle( QtCore.Qt.NoPen )
        self.verticalHeader().setVisible( False )
        self.hv = QtWidgets.QHeaderView( QtCore.Qt.Horizontal, self )
        self.setHorizontalHeader( self.hv )
        self.hv.setSectionResizeMode( 0, QtWidgets.QHeaderView.ResizeToContents )
        self.hv.setSectionResizeMode( 1, QtWidgets.QHeaderView.ResizeToContents )
        self.hv.setSectionResizeMode( 2, QtWidgets.QHeaderView.ResizeToContents )
        self.hv.setSectionResizeMode( 3, QtWidgets.QHeaderView.Stretch )
        self.setHorizontalHeaderLabels( ( "Ref", "Begin", "End", "Body" ) )
        self.verticalHeader().setDefaultSectionSize( 15 )
        self.setEditTriggers( QtWidgets.QAbstractItemView.NoEditTriggers )
        self.setSelectionMode( QtWidgets.QAbstractItemView.NoSelection )
        self.redraw( {} )

    def redraw( self, session ):
        """
        Draw all items in session
        """
        app = WtfdmdgApplication.instance()

        selectedRow = app.getSelectedTaskIndex()

        self.setRowCount( len( session ) )

        for rowi in range( len( session ) ):
            task = app.getTaskByIndex( rowi )
            cols = range( 4 )
            vals = [
                str( task.ref ),
                str( "" if task.begin is None else datetime.datetime.strftime( task.begin, "%H:%M" ) ),
                str( "" if task.end is None else datetime.datetime.strftime( task.end, "%H:%M" ) ),
                str( task.body ) ]
            for c, v in zip( cols, vals ):
                i = QtWidgets.QTableWidgetItem( v )
                if rowi == selectedRow:
                    i.setBackground( QtGui.QBrush( QtGui.QColor( 230, 230, 230 ) ) )
                if task.begin is None or task.end is None:
                    fnt = QtGui.QFont()
                    fnt.setWeight( QtGui.QFont.Bold )
                    i.setFont( fnt )
                else:
                    i.setForeground( QtGui.QColor( 150, 150, 150 ) )
                self.setItem( rowi, c, i )

class WtfdmdgTagTable( QtWidgets.QTableWidget ):

    def __init__( self ):
        """
        Initialize task table widget
        """
        super( WtfdmdgTagTable, self ).__init__()
        self.setColumnCount( 2 )
        self.setGridStyle( QtCore.Qt.NoPen )
        self.verticalHeader().setVisible( False )
        self.hv = QtWidgets.QHeaderView( QtCore.Qt.Horizontal, self )
        self.setHorizontalHeader( self.hv )
        self.hv.setSectionResizeMode( 0, QtWidgets.QHeaderView.ResizeToContents )
        self.hv.setSectionResizeMode( 1, QtWidgets.QHeaderView.Stretch )
        self.setHorizontalHeaderLabels( ( "Class", "Tags" ) )
        self.verticalHeader().setDefaultSectionSize( 15 )
        self.setEditTriggers( QtWidgets.QAbstractItemView.NoEditTriggers )
        self.setSelectionBehavior( QtWidgets.QAbstractItemView.SelectRows )
        self.redraw( {} )

    def getSelectedTags( self ):
        """
        Return class and list of selected tags
        """
        tags = WtfdmdgApplication.instance().getTags()
        cls = WtfdmdgApplication.instance().getSelectedTagClass()
        if cls is not None:
            return tags[ cls ]
        return {}

    def redraw( self, tagtable ):
        """
        Draw all items in session
        """
        app = WtfdmdgApplication.instance()

        self.setRowCount( len( tagtable ) )

        for rowi, ( cls, tags ) in enumerate( tagtable.items() ):
            self.setItem( rowi, 0, QtWidgets.QTableWidgetItem( str( cls ) ) )

            # self.setItem( rowi, 1, QtWidgets.QTableWidgetItem( ", ".join( tags ) ) )
            te = QtGui.QTextEdit( " ".join( tags ) )
            te.setReadOnly( True )
            te.hl = app.getTagBankHighlighter( cls, te.document() )
            te.setMinimumHeight( te.document().size().height() )
            te.setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
            te.document().setDocumentMargin( 0 )
            te.setFrameStyle( QtGui.QFrame.NoFrame )
            self.setCellWidget( rowi, 1, te )

class WtfdmdgTimelineWidget( pg.PlotWidget ):

    class DateAxis( pg.AxisItem ):

        def __init__( self, *args, **kwargs ):
            super( WtfdmdgTimelineWidget.DateAxis, self ).__init__( *args, **kwargs )
            fnt = WtfdmdgApplication.instance().font()
            self.setStyle( tickFont=fnt )

        def tickStrings( self, values, scale, spacing ):
            strings = []
            for v in values:
                # vs is the original tick value
                vs = v * scale
                vstr = time.strftime( "%H:%M", time.localtime( vs ) )
                strings.append( vstr )
            return strings

    def __init__( self ):
        """
        Initialize the timeline widget
        """
        ax = WtfdmdgTimelineWidget.DateAxis( orientation='left')
        super( WtfdmdgTimelineWidget, self ).__init__( axisItems={'left': ax } )
        self._barGraphItem = pg.BarGraphItem( x0=[], x1=[], y0=[], y1=[] )
        self.addItem( self._barGraphItem )
        self.getViewBox().setMouseEnabled( False, False )
        self.hideAxis( 'bottom' )
        self.invertY( True )

    def redraw( self ):
        """
        Plot everything
        """
        self.clear()

        tasks =  [ x for x in WtfdmdgApplication.instance().getSession().values() if x.begin is not None and x.end is not None ]
        tags = WtfdmdgApplication.instance().getSelectedTags()

        if len( tasks ) <= 0:
            return

        def activeAt( t0, t1 ):
            return [ x for x in tasks if not ( t1 < x.begin or t0 > x.end ) ]
        def numActiveAt( t0, t1 ):
            return len( activeAt( t0, t1 ) )
        importantTimes = sorted( set( x.begin for x in tasks ) | set( x.end for x in tasks ) )
        s = [ numActiveAt( x, x ) for x in importantTimes ]
        maxConcurrent = max( s )
        width = 1.0 / maxConcurrent

        columnAssignments = {}
        for task in tasks:
            columnAssignments[ task ] = None
        for task in tasks:
            conflicts = activeAt( task.begin, task.end )
            for i in range( maxConcurrent ):
                if i not in [ columnAssignments[ x ] for x in conflicts ]:
                    columnAssignments[ task ] = i
                    break

        x0 = []
        x1 = []
        y0 = []
        y1 = []
        brushes = []
        for task in sorted( tasks, key=lambda x: x.begin ):
            coeff = columnAssignments[ task ]
            x = coeff * width
            x0.append( x )
            x1.append( x + width )
            y0.append( time.mktime( task.begin.timetuple() ) )
            y1.append( time.mktime( task.end.timetuple() ) )
            brushes.append( self._getBrush( task ) )

        self._barGraphItem = pg.BarGraphItem( x0=x0, x1=x1, y0=y0, y1=y1, brushes=brushes )
        self.addItem( self._barGraphItem )

    def _getBrush( self, task ):
        """
        Construct brush for this task
        """
        app = WtfdmdgApplication.instance()
        selectedTagClass = WtfdmdgApplication.instance().getSelectedTagClass()
        allTags = WtfdmdgApplication.instance().getTags()
        theseTags = WtfdmdgApplication.instance().getTagsForTask( task )
        if selectedTagClass not in theseTags or len( theseTags[ selectedTagClass ] ) <= 0:
            # This task has no tags in currently selected class, so no color
            return pg.mkBrush( 200, 200, 200 )

        theseTags = theseTags[ selectedTagClass ]
        if len( theseTags ) == 1:
            # This task has a single tag in the current class, solid color
            return pg.mkBrush( *app.getTagColor( selectedTagClass, theseTags[0] ) )
        else:
            # This task has multiple colors in the current class, use a gradient
            nc = len( theseTags )
            gradient = QtGui.QLinearGradient( QtCore.QPointF( 0, 0 ), QtCore.QPointF( 1, 0 ) )
            gradient.setSpread( QtGui.QGradient.RepeatSpread )
            gradient.setCoordinateMode( QtGui.QGradient.ObjectMode );
            for i, t in enumerate( theseTags ):
                offset = float( i ) / ( nc - 1 )
                color = QtGui.QColor( *app.getTagColor( selectedTagClass, t ) )
                gradient.setColorAt( offset, color )
            return pg.mkBrush( QtGui.QBrush( gradient ) )

#
# DEBUG DRIVER
#
if __name__ == "__main__":
    sys.exit( WtfdmdgApplication( sys.argv ).exec_() )
