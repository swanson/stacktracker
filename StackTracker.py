from PyQt4 import QtCore, QtGui, QtWebKit
from datetime import datetime, date
import json
import urllib2
from datetime import datetime, date
import time
import os
import copy

class QuestionItem(QtGui.QWidget):
    def __init__(self, title, id):
        QtGui.QListWidgetItem.__init__(self)

        self.setGeometry(QtCore.QRect(0,0,325,50))
        
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setFamily("Arial")

        self.label = QtGui.QLabel(self)
        self.label.setWordWrap(True)
        self.label.setGeometry(QtCore.QRect(15,0,253,50))
        self.label.setFont(font)

        self.stop_button = QtGui.QPushButton(self)
        self.stop_button.setGeometry(QtCore.QRect(265,12,25,25))
        self.stop_button.setFont(font)
        self.stop_button.setText("X")
        self.stop_button.clicked.connect(self.remove)

        self.label.setStyleSheet("background: #ff9900; border: 1px solid black; border-radius: 10px; margin: 2px; color: white;")
        self.stop_button.setStyleSheet("QPushButton{background: #cccccc; border: 1px solid black; border-radius: 5px; color: white;} QPushButton:hover{background: #c03434;}")

        self.label.setText(title)
        self.id = id

    def remove(self):
        self.emit(QtCore.SIGNAL('removeQuestion'), self.id)

    def __repr__(self):
        return "%s: %s" % (self.id, self.title)


class Question():
    def __init__(self, question_id):

        self.id = question_id
        
        api_base = 'http://api.stackoverflow.com/0.8/questions/'
        base = 'http://stackoverflow.com/questions/'
        self.url = base + self.id
        
        json_url = api_base + self.id + '/?key=Jv8tIPTrRUOqRe-5lk4myw'
        so_data = json.loads(urllib2.urlopen(json_url).read())
        self.title = so_data['questions'][0]['title']
        if len(self.title) > 50:
            self.title = self.title[:48] + '...'

    def __repr__(self):
        return "%s: %s" % (self.id, self.title)

class StackTracker(QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("StackTracker")

        self.setGeometry(QtCore.QRect(0, 0, 325, 400))
        self.setFixedSize(QtCore.QSize(325,400))
        self.display_list = QtGui.QListWidget(self)
        self.display_list.resize(QtCore.QSize(325, 350))
        self.display_list.setStyleSheet("QListWidget{show-decoration-selected: 0; background: #818185;}")
        self.display_list.setSelectionMode(QtGui.QAbstractItemView.NoSelection)

        self.question_input = QtGui.QLineEdit(self)
        self.question_input.setValidator(QtGui.QIntValidator(self))
        self.question_input.setGeometry(QtCore.QRect(15, 360, 220, 30))
        self.question_input.setText("Enter Question ID...")
        #not supported until Qt4.7 
        #self.question_input.setPlaceholderText("Enter SO question ID...")

        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setFamily("Arial")

        self.track_button = QtGui.QPushButton(self)
        self.track_button.setGeometry(QtCore.QRect(245, 360, 65, 30))
        self.track_button.setText("Track")
        self.track_button.clicked.connect(self.addQuestion)
        self.track_button.setFont(font)
        self.track_button.setStyleSheet("QPushButton{background: #e2e2e2; border: 1px solid #888888; color: black;} QPushButton:hover{background: #d6d6d6;}")
        

        self.tracking_list = []
 
        self.test_questions = ['1711','2349378']
        for id in self.test_questions:
            q = Question(id)
            self.tracking_list.append(q)

        self.displayQuestions()

        key = "Jv8tIPTrRUOqRe-5lk4myw"
        self.answers_url = "http://api.stackoverflow.com/0.8/questions/2901879/answers?key=%s" % key
        self.comments_url = "http://api.stackoverflow.com/0.8/questions/2901879/comments?key=%s" % key

        self.origin_time = datetime.utcnow()
        
        path = os.getcwd() 
        self.notifier = QtGui.QSystemTrayIcon(QtGui.QIcon(path+'/st.png'), self)
        self.notifier.messageClicked.connect(self.popupClicked)
        self.notifier.show()

        self.worker = WorkerThread(self.tracking_list)
        self.connect(self.worker, QtCore.SIGNAL('newAnswer'), self.newAnswer)
        self.connect(self.worker, QtCore.SIGNAL('newComment'), self.newComment)
        self.worker.start()
        
    def newAnswer(self, question):
        self.popupUrl = question.url
        self.notify("New answer(s): %s" % question.title)

    def newComment(self, question):
        self.popupUrl = question.url
        self.notify("New comment(s): %s" % question.title)

    def popupClicked(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.popupUrl))

    def displayQuestions(self):
        self.display_list.clear()
        n = 0
        for question in self.tracking_list:
            item = QtGui.QListWidgetItem(self.display_list)
            item.setSizeHint(QtCore.QSize(100, 50))
            self.display_list.addItem(item)
            qitem = QuestionItem(question.title, question.id)
            self.connect(qitem, QtCore.SIGNAL('removeQuestion'), self.removeQuestion)
            self.display_list.setItemWidget(item, qitem)
            n = n + 1

    def removeQuestion(self, id):
        for question in self.tracking_list:
            if question.id == id:
                self.tracking_list.remove(question)
        self.displayQuestions()
        self.worker.updateTrackingList(self.tracking_list)

    def addQuestion(self):
        self.notify("New comment(s): What is the single most influential book every programmer should read?")
        id = self.question_input.text()
        try:
            int(id)
        except ValueError:
            self.question_input.setText("Enter Question ID...")
            return
        if len(id) > 0:
            q = Question(str(id))
            self.tracking_list.append(q)
            self.displayQuestions()
            self.worker.updateTrackingList(self.tracking_list)
        else:
            return
        self.question_input.setText("Enter Question ID...")

    def notify(self, msg):
        self.notifier.showMessage("StackTracker", msg, 20000)

class WorkerThread(QtCore.QThread):
    def __init__(self, tracking_list, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.tracking_list = tracking_list
        self.origin_time = datetime.utcnow()

    def run(self):
        self.fetch()
        self.timer = QtCore.QTimer()
        self.connect(self.timer, QtCore.SIGNAL('timeout()'), self.fetch, QtCore.Qt.DirectConnection)
        self.timer.start(20000)
        self.exec_()

    def __del__(self):
        print "del"
        self.exit()
        self.terminate()

    def updateTrackingList(self, tracking_list):
        self.tracking_list = tracking_list

    def fetch(self):
        answers_base = 'http://api.stackoverflow.com/0.8/questions/%s/answers?key=Jv8tIPTrRUOqRe-5lk4myw'
        comments_base = 'http://api.stackoverflow.com/0.8/questions/%s/comments?key=Jv8tIPTrRUOqRe-5lk4myw'

        tracked_questions = copy.deepcopy(self.tracking_list)
        for question in tracked_questions:
            answers_url = answers_base % question.id
            so_data = json.loads(urllib2.urlopen(answers_url).read())
            
            for answer in so_data['answers']:
                updated = datetime.utcfromtimestamp(answer['creation_date'])
                if updated > self.origin_time:
                    self.emit(QtCore.SIGNAL('newAnswer'), question)

            comments_url = comments_base % question.id
            so_data = json.loads(urllib2.urlopen(comments_url).read())
            
            for comment in so_data['comments']:
                updated = datetime.utcfromtimestamp(comment['creation_date'])
                if updated > self.origin_time:
                    self.emit(QtCore.SIGNAL('newComment'), question)

        self.origin_time = datetime.utcnow()

if __name__ == "__main__":
    
    import sys

    app = QtGui.QApplication(sys.argv)
    st = StackTracker(app)
    st.show()
    app.exec_()
    del st
    sys.exit()
