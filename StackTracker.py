#!/usr/bin/env python
import sys
from PyQt4 import QtGui

def main():
    from stacktracker.ui.dialogs import StackTracker
    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    st = StackTracker(app)
    app.exec_()
    del st
    sys.exit()

if __name__ == "__main__":
    main()
