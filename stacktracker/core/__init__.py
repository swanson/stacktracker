from PyQt4 import QtCore, QtGui, QtWebKit, QtNetwork
from datetime import timedelta, datetime, date
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
import sip
import StringIO, gzip
from Queue import Queue
class Question():
    """Application specific representation of a StackExchange question"""
    def __init__(self, question_id, site, title = None, created = None, \
                        last_queried = None, already_answered = None, \
                        answer_count = None, submitter = None):
        self.id = question_id
        self.site = site

        api_base = 'http://api.%s/%s' \
                        % (self.site, APIHelper.API_VER)
        base = 'http://%s/questions/' % (self.site)
        self.url = base + self.id

        self.json_url = '%s/questions/%s/%s' \
                        % (api_base, self.id, APIHelper.API_KEY)

        if title is None or answer_count is None or submitter is None or already_answered is None:
            so_data = APIHelper.callAPI(self.json_url)

        if title is None:
            self.title = so_data['questions'][0]['title']
        else:
            self.title = title

        if already_answered is None:
            self.already_answered = 'accepted_answer_id' in so_data['questions'][0]
        else:
            self.already_answered = already_answered

        if answer_count is None:
            self.answer_count = so_data['questions'][0]['answer_count']
        else:
            self.answer_count = answer_count

        if submitter is None:
            try:
                self.submitter = so_data['questions'][0]['owner']['display_name']
            except KeyError:
                self.submitter = None
        else:
            self.submitter = submitter

        if len(self.title) > 45:
            self.title = self.title[:43] + '...'

        if last_queried is None:
            self.last_queried = datetime.utcnow()
        else:
            self.last_queried = datetime.utcfromtimestamp(last_queried)

        if created is None:
            self.created = datetime.utcnow()
        else:
            self.created = datetime.utcfromtimestamp(created)

        self.answers_url = '%s/questions/%s/answers%s&min=%s' \
                        % (api_base, self.id, APIHelper.API_KEY, 
                                int(calendar.timegm(self.created.timetuple())))
                   
        self.comments_url = '%s/questions/%s/comments%s&min=%s' \
                        % (api_base, self.id, APIHelper.API_KEY, 
                                int(calendar.timegm(self.created.timetuple())))

    def __repr__(self):
        return "%s: %s" % (self.id, self.title)

    def __eq__(self, other):
        return ((self.site == other.site) and (self.id == other.id))



class Notification(object):
    def __init__(self, msg, url = None):
        self.msg = msg
        self.url = url

class APIHelper(object):
    """Helper class for API related functionality"""
    
    API_KEY = '?key=Jv8tIPTrRUOqRe-5lk4myw'
    API_VER = '1.0'

    @staticmethod
    def callAPI(url):
        """Make an API call, decompress the gzipped response, return json object"""
        request = urllib2.Request(url, headers={'Accept-Encoding': 'gzip'})
        req_open = urllib2.build_opener()
        gzipped_data = req_open.open(request).read()
        _buffer = StringIO.StringIO(gzipped_data)
        gzipper = gzip.GzipFile(fileobj=_buffer)
        return json.loads(gzipper.read())


class WorkerThread(QtCore.QThread):
    def __init__(self, tracker, parent = None):
        QtCore.QThread.__init__(self, parent)
        self.tracker = tracker
        self.interval = 60000
        self.settings = {}

    def run(self):
        self.timer = QtCore.QTimer()
        self.connect(self.timer, QtCore.SIGNAL('timeout()'), self.fetch, QtCore.Qt.DirectConnection)
        self.timer.start(self.interval)
        self.fetch()
        self.exec_()

    def __del__(self):
        self.exit()
        self.terminate()

    def setInterval(self, value):
        self.interval = value

    def applySettings(self, settings):
        self.settings = settings

    def fetch(self):
        for question in self.tracker.tracking_list[:]:
            new_answers = False
            new_comments = False
            most_recent = question.last_queried
            so_data = APIHelper.callAPI(question.answers_url)
            answer_count = so_data['total']
            for answer in so_data['answers']:
                updated = datetime.utcfromtimestamp(answer['creation_date'])
                if updated > question.last_queried:
                    new_answers = True
                    if updated > most_recent:
                        most_recent = updated

            so_data = APIHelper.callAPI(question.comments_url)
            for comment in so_data['comments']:
                updated = datetime.utcfromtimestamp(comment['creation_date'])
                if updated > question.last_queried:
                    new_comments = True
                    if updated > most_recent:
                        most_recent = updated

            self.emit(QtCore.SIGNAL('updateQuestion'), question, most_recent, answer_count, \
                                                    new_answers, new_comments)

        self.autoRemoveQuestions()
        self.emit(QtCore.SIGNAL('done'))

    def autoRemoveQuestions(self):
        if self.settings['auto_remove']:
            if self.settings['on_inactivity']:
                threshold = timedelta(hours = self.settings['on_inactivity'])
                for question in self.tracker.tracking_list[:]:
                    if datetime.utcnow() - question.last_queried > threshold:
                        self.emit(QtCore.SIGNAL('autoRemove'), question, True)
            elif self.settings['on_time']:
                threshold = timedelta(hours = self.settings['on_time'])
                for question in self.tracker.tracking_list[:]:
                    if datetime.utcnow() - question.created > threshold:
                        self.emit(QtCore.SIGNAL('autoRemove'), question, True)

