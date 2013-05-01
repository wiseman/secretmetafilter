import datetime
import json
import logging

from google.appengine.ext import db
import webapp2

logger = logging.getLogger(__name__)

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class Post(object):
  def __init__(self, url=None, title=None, posted_time=None, num_comments=None,
               comments=None):
    self.url = url
    self.title = title
    self.posted_time = posted_time
    self.num_comments = num_comments
    self.comments = comments

  def to_model(self):
    return PostModel(
      key_name=self.url,
      url=self.url,
      title=self.title,
      posted_time=self.posted_time,
      num_comments=self.num_comments,
      comments=json.dumps([c.to_dict() for c in self.comments]))

  def to_dict(self):
    return {
      'url': self.url,
      'title': self.title,
      'posted_time': self.posted_time,
      'num_comments': self.num_comments,
      'comments': [c.to_dict() for c in self.comments]
      }

  @staticmethod
  def from_model(post_model):
    return Post(
      url=post_model.url,
      title=post_model.title,
      posted_time=post_model.posted_time,
      num_comments=post_model.num_comments,
      comments=[Comment.from_dict(d) for d in json.loads(post_model.comments)])


class Comment(object):
  def __init__(self, html=None, posted_time=None):
    self.html = html
    self.posted_time = posted_time

  def to_dict(self):
    return {
      'html': self.html,
      'posted_time': self.posted_time.strftime(DATETIME_FORMAT)
      }

  @staticmethod
  def from_dict(d):
    return Comment(
      html=d['html'],
      posted_time=datetime.datetime.strptime(
        d['posted_time'], DATETIME_FORMAT))


class PostModel(db.Model):
  url = db.LinkProperty()
  title = db.StringProperty()
  posted_time = db.DateTimeProperty()
  num_comments = db.IntegerProperty()
  comments = db.TextProperty()


def save_post(post):
  logger.info(
    'Saving post %s with %s comments.', post.url, post.num_comments)
  post.comments = post.comments[-5:]
  post_model = post.to_model()
  post_model.put()


def get_posts():
  logger.info('Fetching all posts')
  posts = [Post.from_model(p) for p in PostModel.all()]
  logger.info('Got %s posts.', len(posts))
  return posts
