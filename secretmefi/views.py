import logging
import os.path

from google.appengine.api import taskqueue
import jinja2
import webapp2

from secretmefi import data
from secretmefi import tasks

logger = logging.getLogger(__name__)

jinja = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.join(
    os.path.dirname(__file__), 'templates')))


class MainPage(webapp2.RequestHandler):
  def get(self):
    posts = data.get_posts()
    posts = [p for p in posts if p.num_comments > 0]
    posts = sorted(posts, key=lambda p: p.comments[-1].posted_time, reverse=True)
    template = jinja.get_template('index.tmpl')
    template_values = {'posts': posts}
    self.response.write(template.render(template_values))


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
