from PyQt4 import QtCore, QtGui, QtWebKit, QtNetwork
from datetime import datetime, date
try:
    import json
except ImportError:
    import simplejson as json
import os
import re
import calendar
from Queue import Queue
from ui.extensions import QSpinBoxRadioButton, QLineEditWithPlaceholder, QuestionDisplayWidget
from core import WorkerThread, APIHelper, Question, Notification

class StackTracker(QtGui.QDialog):
    """
    The 'main' dialog window for the application.  Displays
    the list of tracked questions and has the input controls for
    adding new questions.
    """


    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self)
        self.parent = parent
        self.setWindowTitle("StackTracker")
        self.closeEvent = self.cleanUp
        self.setStyleSheet("QDialog{background: #f0ebe2;}")

        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.accepted.connect(self.serializeSettings)
        self.settings_dialog.accepted.connect(self.applySettings)
        self.settings_dialog.rejected.connect(self.deserializeSettings)
        self.deserializeSettings()

        self.setGeometry(QtCore.QRect(0, 0, 325, 400))
        self.setFixedSize(QtCore.QSize(350,400))

        self.display_list = QtGui.QListWidget(self)
        self.display_list.resize(QtCore.QSize(350, 350))
        self.display_list.setStyleSheet("QListWidget{show-decoration-selected: 0; background: black;}")
        self.display_list.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.display_list.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.display_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.display_list.clear()

        self.question_input = QLineEditWithPlaceholder(self)
        self.question_input.setGeometry(QtCore.QRect(15, 360, 240, 30))
        self.question_input.setPlaceholderText("Enter Question URL...")

        icon_path = os.path.join(os.path.dirname(__file__), '..', 'img', 'st_logo.png')
        icon = QtGui.QIcon(icon_path)
        self.setWindowIcon(icon)

        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setFamily("Arial")

        self.track_button = QtGui.QPushButton(self)
        self.track_button.setGeometry(QtCore.QRect(265, 360, 65, 30))
        self.track_button.setText("Track")
        self.track_button.clicked.connect(self.addQuestion)
        self.track_button.setFont(font)
        self.track_button.setStyleSheet("QPushButton{background: #e2e2e2; border: 1px solid #888888; color: black;} QPushButton:hover{background: #d6d6d6;}")

        self.tracking_list = []

        self.deserializeQuestions() #load persisted questions from tracking.json

        self.displayQuestions()

        self.queue_timer = QtCore.QTimer(self)
        self.queue_timer.timeout.connect(self.processQueue)
        self.notify_queue = Queue()


        self.notifier = QtGui.QSystemTrayIcon(icon, self)
        self.notifier.messageClicked.connect(self.popupClicked)
        self.notifier.activated.connect(self.trayClicked)
        self.notifier.setToolTip('StackTracker')

        self.tray_menu = QtGui.QMenu()
        self.show_action = QtGui.QAction('Show', None)
        self.show_action.triggered.connect(self.showWindow)

        self.settings_action = QtGui.QAction('Settings', None)
        self.settings_action.triggered.connect(self.showSettings)

        self.about_action = QtGui.QAction('About', None)
        self.about_action.triggered.connect(self.showAbout)

        self.exit_action = QtGui.QAction('Exit', None)
        self.exit_action.triggered.connect(self.exitFromTray)

        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.settings_action)
        self.tray_menu.addAction(self.about_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.exit_action)

        self.notifier.setContextMenu(self.tray_menu)
        self.notifier.show()

        self.worker = WorkerThread(self)
        self.connect(self.worker, QtCore.SIGNAL('updateQuestion'), self.updateQuestion)
        self.connect(self.worker, QtCore.SIGNAL('autoRemove'), self.removeQuestion)
        self.connect(self.worker, QtCore.SIGNAL('done'), self.startQueueProcess)

        self.applySettings()

        self.worker.start()

    def applySettings(self):
        """Send new settings to worker thread"""
        settings = self.settings_dialog.getSettings()
        interval = settings['update_interval'] * 1000 #convert to milliseconds
        self.worker.setInterval(interval)
        self.worker.applySettings(settings)

    def trayClicked(self, event):
        """Shortcut to show list of question, not supported in Mac OS X"""
        if event == QtGui.QSystemTrayIcon.DoubleClick:
            self.showWindow()

    def showWindow(self):
        """Show the list of tracked questions"""
        self.show()
        self.showMaximized()
        self.displayQuestions()

    def showSettings(self):
        """Show the settings dialog"""
        self.settings_dialog.show()

    def showAbout(self):
        """Show About Page, as if anyone actually cares about who made this..."""
        s = """
            <h3>StackTracker</h3>
            <p>A desktop notifier using the StackExchange API built with PyQt4</p>
            <p>Get alerts when answers or comments are posted to questions you are tracking.</p>
            <p><b>Created by Matt Swanson</b></p>
                        """
        QtGui.QMessageBox(QtGui.QMessageBox.Information, "About",  s).exec_()

    def showError(self, text):
        """
        Pop-up an error box with a message

        params:
            text => msg to display
        """
        QtGui.QMessageBox(QtGui.QMessageBox.Critical, "Error!", text).exec_()

    def exitFromTray(self):
        """Event handler for 'Exit' menu option"""
        self.serializeQuestions()
        self.serializeSettings()
        self.parent.exit()

    def cleanUp(self, event):
        """Perform last-minute operations before exiting"""
        self.serializeQuestions()
        self.serializeSettings()

    def serializeQuestions(self):
        """Persist currently tracked questions in external JSON file"""
        a = []
        for q in self.tracking_list:
            a.append(q.__dict__)
        
        #handler to convert datetime objects into epoch timestamps
        datetime_to_json = lambda obj: calendar.timegm(obj.utctimetuple()) if isinstance(obj, datetime) else None
        with open(os.path.join(os.path.dirname(__file__), '..', 'tracking.json'), 'w') as fp:
                json.dump({'questions':a}, fp, default = datetime_to_json, indent = 4)

    def deserializeQuestions(self):
        """Restore saved tracked questions from external JSON file"""
        try:
            with open(os.path.join(os.path.dirname(__file__), '..', 'tracking.json'), 'r') as fp:
                data = fp.read()
        except EnvironmentError:
            #no tracking.json file, return silently
            return

        question_data = json.loads(data)
        for q in question_data['questions']:
            rebuilt_question = Question(q['id'], q['site'], q['title'], q['created'], \
                                                q['last_queried'], q['already_answered'], \
                                                q['answer_count'], q['submitter'])
            self.tracking_list.append(rebuilt_question)

    def serializeSettings(self):
        """Persist application settings in external JSON file"""
        settings = self.settings_dialog.getSettings()
        with open(os.path.join(os.path.dirname(__file__), '..', 'settings.json'), 'w') as fp:
            json.dump(settings, fp, indent = 4)

    def deserializeSettings(self):
        """Restore saved application settings from external JSON file"""
        try:
            with open(os.path.join(os.path.dirname(__file__), '..', 'settings.json'), 'r') as fp:
                data = fp.read()
        except EnvironmentError:
            #no saved settings, return silently
            return

        self.settings_dialog.updateSettings(json.loads(data))

    def updateQuestion(self, question, most_recent, answer_count, new_answer, new_comment):
        """Update questions in the tracking list with data fetched from worker thread"""
        tracked = None
        for q in self.tracking_list:
            if q == question:
                tracked = q
                break

        if tracked:
            tracked.last_queried = most_recent
            tracked.answer_count = answer_count

            if new_answer and new_comment:
                self.addToNotificationQueue(Notification("New comment(s) and answer(s): %s" \
                                                            % tracked.title, tracked.url))
            elif new_answer:
                self.addToNotificationQueue(Notification("New answer(s): %s" \
                                                            % tracked.title, tracked.url))
            elif new_comment:
                self.addToNotificationQueue(Notification("New comment(s): %s" \
                                                            % tracked.title, tracked.url))

            self.displayQuestions()

    def popupClicked(self):
        """Open the question in user's default browser"""
        if self.popupUrl:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.popupUrl))

    def displayQuestions(self):
        """Render the currently tracked questions in the display list"""
        #hack to fix random disappearing questions
        self.display_list = QtGui.QListWidget(self)
        self.display_list.resize(QtCore.QSize(350, 350))
        self.display_list.setStyleSheet("QListWidget{show-decoration-selected: 0; background: black;}")
        self.display_list.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.display_list.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.display_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.display_list.clear()
        #/end hack

        n = 0
        for question in self.tracking_list:
            item = QtGui.QListWidgetItem(self.display_list)
            item.setSizeHint(QtCore.QSize(320, 95))
            self.display_list.addItem(item)
            qitem = QuestionDisplayWidget(question)
            self.connect(qitem, QtCore.SIGNAL('removeQuestion'), self.removeQuestion)
            self.display_list.setItemWidget(item, qitem)
            del item
            n = n + 1

        self.display_list.show()

    def removeQuestion(self, q, notify = False):
        """
        Remove a question from the tracking list

        params:
            notify => indicate if the user should be alerted that the
                      question is no longer being tracked, useful for
                      auto-removing
        """
        for question in self.tracking_list[:]:
            if question == q:
                self.tracking_list.remove(question)
                if notify:
                    self.addToNotificationQueue(Notification("No longer tracking: %s" \
                                                                % question.title))
                break
        self.displayQuestions()

    def extractDetails(self, url):
        """Strip out the site domain from given URL"""
        #todo: consider using StackAuth
        regex = re.compile("""(?:http://)?(?:www\.)?
                                (?P<site>(?:[A-Za-z\.])*\.[A-Za-z]*)
                                /.*?
                                (?P<id>[0-9]+)
                                /?.*""", re.VERBOSE)
        match = regex.match(url)
        if match is None:
            return None
        try:
            site = match.group('site')
            _id = match.group('id')
        except IndexError:
            return None
        return _id, site

    def addQuestion(self):
        """
        Add a new question to the list of tracked questions and render
        it on the display list
        """
        url = self.question_input.text()
        self.question_input.clear()
        details = self.extractDetails(str(url))
        if details:
            _id, site = details
        else:
            self.showError("Invalid URL format, please try again.")
            return
        q = Question(_id, site)
        if q not in self.tracking_list:
            q = Question(_id, site)
            self.tracking_list.append(q)
            self.displayQuestions()
        else:
            self.showError("This question is already being tracked.")
            return

    def addToNotificationQueue(self, notification):
        self.notify_queue.put(notification)

    def startQueueProcess(self):
        if not self.queue_timer.isActive():
            self.queue_timer.start(5000)
            self.processQueue()

    def processQueue(self):
        if self.notify_queue.empty():
            if self.queue_timer.isActive():
                self.queue_timer.stop()
        else:
            self.notify(self.notify_queue.get())

    def notify(self, notification):
        self.popupUrl = notification.url
        self.notifier.showMessage("StackTracker", notification.msg, 20000)


class SettingsDialog(QtGui.QDialog):
    """
    Settings window that allows the user to customize the application

    Currently supports auto-removing questions and changing the refresh
    interval.
    """
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.setFixedSize(QtCore.QSize(400,250))
        self.setWindowTitle('Settings')

        self.layout = QtGui.QVBoxLayout()

        self.auto_remove = QtGui.QGroupBox("Automatically remove questions?", self)
        self.auto_remove.setCheckable(True)
        self.auto_remove.setChecked(False)

        self.time_option = QSpinBoxRadioButton('After','of being added')
        self.time_option.setMinimum(1)
        self.time_option.setMaximum(1000)
        self.time_option.setSingleStep(1)
        self.time_option.setSpinBoxSuffix(" hour(s)")

        self.inactivity_option = QSpinBoxRadioButton('After', 'of inactivity')
        self.inactivity_option.setMinimum(1)
        self.inactivity_option.setMaximum(1000)
        self.inactivity_option.setSingleStep(1)
        self.inactivity_option.setSpinBoxSuffix(" hour(s)")

        self.auto_layout = QtGui.QVBoxLayout()
        self.auto_layout.addWidget(self.time_option)
        self.auto_layout.addWidget(self.inactivity_option)

        self.auto_remove.setLayout(self.auto_layout)

        self.update_interval = QtGui.QGroupBox("Update Interval", self)
        self.update_input = QtGui.QSpinBox()
        self.update_input.setMinimum(60)
        self.update_input.setMaximum(86400)
        self.update_input.setSingleStep(15)
        self.update_input.setSuffix(" seconds")
        self.update_input.setPrefix("Check for updates every ")

        self.update_layout = QtGui.QVBoxLayout()
        self.update_layout.addWidget(self.update_input)

        self.update_interval.setLayout(self.update_layout)

        self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Save)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.auto_remove)
        self.layout.addWidget(self.update_interval)
        self.layout.addStretch(2)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def updateSettings(self, settings):
        """Restore saved settings from a dictionary"""
        #todo throw this in a try block
        self.auto_remove.setChecked(settings['auto_remove'])
        if settings['on_time']:
            self.time_option.setValue(settings['on_time'])
            self.time_option.setChecked(True)
        if settings['on_inactivity']:
            self.inactivity_option.setValue(settings['on_inactivity'])
            self.inactivity_option.setChecked(True)
        self.update_input.setValue(settings['on_time'])

    def getSettings(self):
        """Returns a dictionary of currently selected settings"""
        settings = {}
        settings['auto_remove'] = self.auto_remove.isChecked()
        settings['on_time'] = self.time_option.value() if self.time_option.isChecked() else False
        settings['on_inactivity'] = self.inactivity_option.value() if self.inactivity_option.isChecked() else False
        settings['update_interval'] = self.update_input.value()

        return settings


