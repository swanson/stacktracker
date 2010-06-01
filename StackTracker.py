from PyQt4 import QtCore, QtGui, QtWebKit
from datetime import datetime, date
try:
    import json
except ImportError:
    import simplejson as json
import urllib2
import os
import copy
import re
import time
import calendar

class QuestionItem(QtGui.QWidget):
    def __init__(self, title, id, site):
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

        background = StackTracker.SITES[site]
        self.label.setStyleSheet("background: %s; border: 1px solid black; border-radius: 10px; margin: 2px; color: white;" % (background))
        self.stop_button.setStyleSheet("QPushButton{background: #cccccc; border: 1px solid black; border-radius: 5px; color: white;} QPushButton:hover{background: #c03434;}")

        self.label.setText(title)
        self.id = id

    def remove(self):
        self.emit(QtCore.SIGNAL('removeQuestion'), self.id)

    def __repr__(self):
        return "%s: %s" % (self.id, self.title)


class Question():
    def __init__(self, question_id, site, title = None, last_queried = None):
        self.id = question_id
        self.site = site
        
        api_base = 'http://api.%s/%s' \
                        % (self.site, StackTracker.API_VER)
        base = 'http://%s/questions/' % (self.site)
        self.url = base + self.id

        self.answers_url = '%s/questions/%s/answers%s' \
                        % (api_base, self.id, StackTracker.API_KEY)
        self.comments_url = '%s/questions/%s/comments%s' \
                        % (api_base, self.id, StackTracker.API_KEY)
        
        json_url = '%s/questions/%s/%s' \
                        % (api_base, self.id, StackTracker.API_KEY)

        if title is None:
            so_data = json.loads(urllib2.urlopen(json_url).read())
            self.title = so_data['questions'][0]['title']
        else:
            self.title = title

        if len(self.title) > 50:
            self.title = self.title[:48] + '...'

        if last_queried is None:
            self.last_queried = datetime.utcnow()
        else:
            self.last_queried = datetime.utcfromtimestamp(last_queried)
        
    def __repr__(self):
        return "%s: %s" % (self.id, self.title)


class StackTracker(QtGui.QMainWindow):
    
    SITES = {'stackoverflow.com':'#ff9900',
            'serverfault.com':'#ea292c',
            'superuser.com':'#00bff3',
            'meta.stackoverflow.com':'#a6a6a6',
            }

    API_KEY = '?key=Jv8tIPTrRUOqRe-5lk4myw'
    API_VER = '0.8'

    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("StackTracker")
        self.closeEvent = self.cleanUp

        self.setGeometry(QtCore.QRect(0, 0, 325, 400))
        self.setFixedSize(QtCore.QSize(325,400))
        self.display_list = QtGui.QListWidget(self)
        self.display_list.resize(QtCore.QSize(325, 350))
        self.display_list.setStyleSheet("QListWidget{show-decoration-selected: 0; background: #818185;}")
        self.display_list.setSelectionMode(QtGui.QAbstractItemView.NoSelection)

        self.question_input = QtGui.QLineEdit(self)
        self.question_input.setGeometry(QtCore.QRect(15, 360, 220, 30))
        self.question_input.setText("Enter Question URL...")
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
 
        self.deserializeQuestions() #load persisted questions from tracking.json

        self.displayQuestions()

        path = os.getcwd() 
        self.notifier = QtGui.QSystemTrayIcon(QtGui.QIcon(path+'/st.png'), self)
        self.notifier.messageClicked.connect(self.popupClicked)
        self.notifier.show()

        self.worker = WorkerThread(self.tracking_list)
        self.connect(self.worker, QtCore.SIGNAL('newAnswer'), self.newAnswer)
        self.connect(self.worker, QtCore.SIGNAL('newComment'), self.newComment)
        self.worker.start()

    def cleanUp(self, event):
        self.serializeQuestions()

    def serializeQuestions(self):
        datetime_to_json = lambda obj: calendar.timegm(obj.utctimetuple()) if isinstance(obj, datetime) else None
        a = []
        for q in self.tracking_list:
            a.append(q.__dict__)
 
        with open('tracking.json', 'w') as fp:
                json.dump({'questions':a}, fp, default = datetime_to_json, indent = 4)

    def deserializeQuestions(self):
        try:
            with open('tracking.json', 'r') as fp:
                data = fp.read()
        except EnvironmentError:
            #no tracking.json file
            return

        question_data = json.loads(data)
        for q in question_data['questions']:
            rebuilt_question = Question(q['id'], q['site'], q['title'], q['last_queried'])
            self.tracking_list.append(rebuilt_question)
    
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
            qitem = QuestionItem(question.title, question.id, question.site)
            self.connect(qitem, QtCore.SIGNAL('removeQuestion'), self.removeQuestion)
            self.display_list.setItemWidget(item, qitem)
            n = n + 1

    def removeQuestion(self, id):
        for question in self.tracking_list:
            if question.id == id:
                self.tracking_list.remove(question)
        self.displayQuestions()
        self.worker.updateTrackingList(self.tracking_list)

    def extractDetails(self, url):
        regex = re.compile("""(?:http://)?(?:www\.)?
                                (?P<site>(?:[A-Za-z\.])*\.[A-Za-z]*)
                                /.*?
                                (?P<id>[0-9]+)
                                /.*""", re.VERBOSE)
        match = regex.match(url)
       
        try:
            site = match.group('site')
            id = match.group('id')
        except IndexError:
            return None
        return id, site

    def addQuestion(self):
        url = self.question_input.text()
        details = self.extractDetails(str(url))
        if details:
            id, site = details
        else:
            #bad input
            return
        if id not in self.tracking_list:
            q = Question(id, site)
            self.tracking_list.append(q)
            self.displayQuestions()
            self.worker.updateTrackingList(self.tracking_list)
        else:
            #question already being tracked
            return
        self.question_input.setText("Enter Question URL...")

    def notify(self, msg):
        self.notifier.showMessage("StackTracker", msg, 20000)

class WorkerThread(QtCore.QThread):
    def __init__(self, tracking_list, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.tracking_list = tracking_list

    def run(self):
        self.fetch()
        self.timer = QtCore.QTimer()
        self.connect(self.timer, QtCore.SIGNAL('timeout()'), self.fetch, QtCore.Qt.DirectConnection)
        self.timer.start(20000)
        self.exec_()

    def __del__(self):
        self.exit()
        self.terminate()

    def updateTrackingList(self, tracking_list):
        self.tracking_list = tracking_list

    def fetch(self):
        #todo: better handling of multiple new answers with regards
        #notifications and timestamps

        #todo: sort by newest answers and break out once we get to the old answers
        #to speed up
        for question in self.tracking_list:
            new_answers = False
            new_comments = False
            most_recent = question.last_queried
            
            so_data = json.loads(urllib2.urlopen(question.answers_url).read())
            for answer in so_data['answers']:
                updated = datetime.utcfromtimestamp(answer['creation_date'])
                if updated > question.last_queried:
                    new_answers = True
                    if updated > most_recent:
                        most_recent = updated

            so_data = json.loads(urllib2.urlopen(question.comments_url).read())
            for comment in so_data['comments']:
                updated = datetime.utcfromtimestamp(comment['creation_date'])
                if updated > question.last_queried:
                    new_comments = True
                    if updated > most_recent:
                        most_recent = updated
            
            if new_answers:
                self.emit(QtCore.SIGNAL('newAnswer'), question)
            if new_comments:
                self.emit(QtCore.SIGNAL('newComment'), question)

            question.last_queried = most_recent

if __name__ == "__main__":
    
    import sys

    app = QtGui.QApplication(sys.argv)
    st = StackTracker(app)
    st.show()
    app.exec_()
    del st
    sys.exit()
