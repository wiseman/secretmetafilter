import datetime
import logging
import os.path

from google.appengine.api import taskqueue
from google.appengine.ext import db
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


class MainPage(webapp2.RequestHandler):
  def get(self):
    html_model = db.get(db.Key.from_path('HtmlModel', 'index.html'))
    if html_model:
      self.response.write(html_model.html)
    else:
      self.response.write('The processing is occurring.  Check back later.')


class AdminPage(webapp2.RequestHandler):
  def get(self):
    if self.request.headers.get('X-AppEngine-Cron', False):
      self.refresh_posts()
      self.response.write('OK')
    else:
      template = jinja.get_template('admin.tmpl')
      template_values = {
        'message': self.request.get('msg', '')
      }
      self.response.write(template.render(template_values))

  def post(self):
    action = self.request.get('action')
    if action == 'Regenerate':
      self.refresh_html()
      self.redirect('/admin?msg=Regenerating+HTML')
    elif action == 'Rescrape':
      self.refresh_posts()
      self.redirect('/admin?msg=Rescraping+Metafilter')

  def refresh_posts(self):
    taskqueue.add(
      url='/task/IndexPageScraperWorker',
      params={'page_num': 0})

  def refresh_html(self):
    taskqueue.add(url='/task/HtmlGeneratorWorker')


ROUTES = [
  ('/', MainPage),
  ('/admin', AdminPage),
  ('/task/HtmlGeneratorWorker', tasks.HtmlGeneratorWorker),
  ('/task/IndexPageScraperWorker', tasks.IndexPageScraperWorker),
  ('/task/PostPageScraperWorker', tasks.PostPageScraperWorker)
  ]


def make_application():
  return  webapp2.WSGIApplication(
    ROUTES,
    debug=True)
