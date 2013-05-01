import itertools
import json
import logging
import os

from google.appengine.api import taskqueue
import webapp2

from secretmefi import tasks

logger = logging.getLogger(__name__)


class MainPage(webapp2.RequestHandler):
  def get(self):
    pass


class Test1Page(webapp2.RequestHandler):
  def get(self):
    taskqueue.add(
      url='/task/IndexPageScraperWorker',
      params={'page_num': 0})


ROUTES = [
  ('/', MainPage),
  ('/test1', Test1Page),
  ('/task/IndexPageScraperWorker', tasks.IndexPageScraperWorker),
  ('/task/PostPageScraperWorker', tasks.PostPageScraperWorker)
  ]


def make_application():
  return  webapp2.WSGIApplication(
    ROUTES,
    debug=True)
