import logging

from google.appengine.ext import db
import webapp2

logger = logging.getLogger(__name__)


class Post(db.Model):
  url = db.LinkProperty()
  title = db.StringProperty()
  posted_time = db.DateTimeProperty()


class Comment(db.Model):
  url = db.LinkProperty()
  author = db.StringProperty()
  posted_time = db.DateTimeProperty()
  body = db.StringProperty()
