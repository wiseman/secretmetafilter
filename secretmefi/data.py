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
    if self.comments is None:
      comments_val = 'null'
    else:
      comments_val = json.dumps([c.to_dict() for c in self.comments])
    return PostModel(
      key_name=self.url,
      url=self.url,
      title=self.title,
      posted_time=self.posted_time,
      num_comments=self.num_comments,
      last_comment_time=self.last_comment_time(),
      comments=comments_val)

  def last_comment_time(self):
    if self.comments:
      return self.comments[-1].posted_time
    else:
      return None

  def to_dict(self):
    if self.comments is None:
      comments_val = None
    else:
      comments_val = [c.to_dict() for c in self.comments]
    return {
      'url': self.url,
      'title': self.title,
      'posted_time': self.posted_time,
      'num_comments': self.num_comments,
      'last_comment_time': self.last_comment_time(),
      'comments': comments_val
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
  last_comment_time = db.DateTimeProperty()
  comments = db.TextProperty()


def save_post(post):
  logger.info(
    'Saving post %s with %s comments.', post.url, post.num_comments)
  post.comments = post.comments[-5:]
  post_model = post.to_model()
  post_model.put()


def get_posts(urls):
  logger.info('looking up %s', urls)
  keys = [db.Key.from_path('PostModel', url) for url in urls]
  post_models = db.get(keys)
  logger.info('post models=%s', post_models)
  posts = [Post.from_model(p) for p in post_models if p]
  return posts


class HtmlModel(db.Model):
  html = db.TextProperty()
