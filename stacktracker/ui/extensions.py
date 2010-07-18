from PyQt4 import QtGui, QtCore
import os

class QLineEditWithPlaceholder(QtGui.QLineEdit):
    """
    Custom Qt widget that is required since PyQt does not yet
    support Qt4.7 -- which adds native placeholder text functionality to
    QLineEdits
    """
    def __init__(self, parent = None):
        QtGui.QLineEdit.__init__(self, parent)
        self.placeholder = None

    def setPlaceholderText(self, text):
        self.placeholder = text
        self.update()

    def paintEvent(self, event):
        """Overload paintEvent to draw placeholder text under certain conditions"""
        QtGui.QLineEdit.paintEvent(self, event)
        if self.placeholder and not self.hasFocus() and not self.text():
            painter = QtGui.QPainter(self)
            painter.setPen(QtGui.QPen(QtCore.Qt.darkGray))
            painter.drawText(QtCore.QRect(8, 1, self.width(), self.height()), \
                                QtCore.Qt.AlignVCenter, self.placeholder)
            painter.end()

class QSpinBoxRadioButton(QtGui.QRadioButton):
    """
    Custom Qt Widget that allows for a spinbox to be used in
    conjunction with a radio button
    """
    def __init__(self, prefix = '', suffix = '', parent = None):
        QtGui.QRadioButton.__init__(self, parent)
        self.prefix = QtGui.QLabel(prefix)
        self.prefix.mousePressEvent = self.labelClicked
        self.suffix = QtGui.QLabel(suffix)
        self.suffix.mousePressEvent = self.labelClicked

        self.spinbox = QtGui.QSpinBox()
        self.spinbox.setEnabled(self.isDown())
        self.toggled.connect(self.spinbox.setEnabled)

        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.prefix)
        self.layout.addWidget(self.spinbox)
        self.layout.addWidget(self.suffix)
        self.layout.addStretch(2)
        self.layout.setContentsMargins(25, 0, 0, 0)

        self.setLayout(self.layout)

    def labelClicked(self, event):
        self.toggle()

    def setPrefix(self, p):
        self.prefix.setText(p)

    def setSuffix(self, s):
        self.suffix.setText(s)

    def setSpinBoxSuffix(self, text):
        self.spinbox.setSuffix(" %s" % text)

    def setMinimum(self, value):
        self.spinbox.setMinimum(value)

    def setMaximum(self, value):
        self.spinbox.setMaximum(value)

    def setSingleStep(self, step):
        self.spinbox.setSingleStep(step)

    def value(self):
        return self.spinbox.value()

    def setValue(self, value):
        self.spinbox.setValue(value)

class QuestionDisplayWidget(QtGui.QWidget):
    """Custom Qt Widget to display pretty representations of Question objects"""
    def __init__(self, question, parent = None):
        QtGui.QWidget.__init__(self, parent)

        SITE_LOGOS = {'stackoverflow.com':'stackoverflow_logo.png',
                      'serverfault.com':'serverfault_logo.png',
                      'superuser.com':'superuser_logo.png',
                      'meta.stackoverflow.com':'metastackoverflow_logo.png',
                      'stackapps.com':'stackapps_logo.png'
                      }

        self.setGeometry(QtCore.QRect(0,0,320,80))
        self.setStyleSheet('QLabel {color: #cccccc;}')
        self.frame = QtGui.QFrame(self)
        self.frame.setObjectName('mainFrame')
        self.frame.setStyleSheet('#mainFrame {background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #333333, stop: 1 #4d4d4d);}')

        self.question = question

        font = QtGui.QFont()
        font.setPointSize(14)

        self.question_label = QtGui.QLabel(self.frame)
        self.question_label.setGeometry(QtCore.QRect(10, 7, 280, 50))
        self.question_label.setWordWrap(True)
        self.question_label.setFont(font)
        self.question_label.setText(question.title)
        self.question_label.setObjectName('question_label')
        self.question_label.setStyleSheet("#question_label{color: #83ceea;text-decoration:underline} #question_label:hover{color: #b9eafc;}")
        self.question_label.mousePressEvent = self.launchUrl

        self.remove_button = QtGui.QPushButton(self.frame)
        self.remove_button.setGeometry(QtCore.QRect(295, 7, 25, 25))
        self.remove_button.setText('X')
        self.remove_button.setFont(font)
        self.remove_button.setStyleSheet("QPushButton{background: #818185; border: 3px solid black; color: white; text-align: center;} QPushButton:hover{background: #c03434;}")
        self.remove_button.clicked.connect(self.remove)

        if question.site in SITE_LOGOS:
            #path = os.path.join('img', SITE_LOGOS[question.site])
            logo_path = os.path.join(os.path.dirname(__file__), '..', \
                                            'img', SITE_LOGOS[question.site])
            self.site_icon = QtGui.QLabel(self.frame)
            self.site_icon.setGeometry(QtCore.QRect(10, 60, 25, 25))
            self.site_icon.setStyleSheet("image: url(" + logo_path + "); background-repeat:no-repeat;")
        else:
            logo_path = os.path.join(os.path.dirname(__file__), '..', 'img', 'default.png')
            self.site_icon = QtGui.QLabel(self.frame)
            self.site_icon.setGeometry(QtCore.QRect(10, 60, 25, 25))
            self.site_icon.setStyleSheet("image: url(" + logo_path + "); background-repeat:no-repeat;")


        self.answers_label = QtGui.QLabel(self.frame)
        self.answers_label.setText('%s answer(s)' % question.answer_count)
        self.answers_label.setGeometry(QtCore.QRect(40, 65, 100, 20))

        if question.submitter is not None:
            self.submitted_label = QtGui.QLabel(self.frame)
            self.submitted_label.setText('asked by ' + question.submitter)
            self.submitted_label.setAlignment(QtCore.Qt.AlignRight)
            self.submitted_label.setGeometry(QtCore.QRect(120, 65, 200, 20))

    def remove(self):
        self.emit(QtCore.SIGNAL('removeQuestion'), self.question)

    def launchUrl(self, event):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.question.url))

