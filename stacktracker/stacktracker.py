if __name__ == "__main__":
    import sys
    from PyQt4 import QtGui
    from ui.dialogs import StackTracker

    app = QtGui.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    st = StackTracker(app)
    app.exec_()
    del st
    sys.exit()
