import datetime
import logging
import os.path

from google.appengine.api import taskqueue
import jinja2
import pretty_timedelta

import webapp2

from secretmefi import data
from secretmefi import tasks

logger = logging.getLogger(__name__)

jinja = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.join(
    os.path.dirname(__file__), 'templates')))


def pretty_timedelta_filter(v):
  return pretty_timedelta.pretty_timedelta(v)

jinja.filters['pretty_timedelta'] = pretty_timedelta_filter


MIN_AGE_DELTA = datetime.timedelta(days=7)


class MainPage(webapp2.RequestHandler):
  def get(self):
    now = datetime.datetime.now()
    posts = data.get_posts()
    posts = [p for p in posts if p.num_comments > 0]
    posts = [p for p in posts
             if p.comments[-1].posted_time - p.posted_time >= MIN_AGE_DELTA]
    posts = sorted(
      posts, key=lambda p: p.comments[-1].posted_time, reverse=True)
    posts = [p.to_dict() for p in posts]
    for p in posts:
      p['posted_timedelta'] = p['posted_time'] - now
    template = jinja.get_template('index.tmpl')
    template_values = {'posts': posts}
    self.response.write(template.render(template_values))


class AdminPage(webapp2.RequestHandler):
  def get(self):
    if self.request.headers.get('X-AppEngine-Cron', False):
      self.refresh_posts()
      self.response.write('OK')
    else:
      template = jinja.get_template('admin.tmpl')
      self.response.write(template.render())

  def post(self):
    self.refresh_posts()
    self.redirect('/admin')

  def refresh_posts(self):
    taskqueue.add(
      url='/task/IndexPageScraperWorker',
      params={'page_num': 0})


ROUTES = [
  ('/', MainPage),
  ('/admin', AdminPage),
  ('/task/IndexPageScraperWorker', tasks.IndexPageScraperWorker),
  ('/task/PostPageScraperWorker', tasks.PostPageScraperWorker)
  ]


def make_application():
  return  webapp2.WSGIApplication(
    ROUTES,
    debug=True)
