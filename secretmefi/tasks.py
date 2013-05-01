import datetime
import logging
import re
import string
import urllib2
import urlparse
import uuid

import bs4
from google.appengine.api import memcache
from google.appengine.api import taskqueue
import webapp2

logger = logging.getLogger(__name__)


METAFILTER_INDEX_URL = string.Template(
  'http://metafilter.com/index.cfm?page=$page_num')

MAX_POST_AGE = datetime.timedelta(days=3)

USER_AGENT = ('Mozilla/5.0 (compatible; secretmefibot/0.1; '
              '+http://secretmefi.appspot.com/bot.html)')


def fetch_url(url):
  opener = urllib2.build_opener()
  opener.addheaders = [('User-agent', USER_AGENT)]
  response = opener.open(url)
  return response


class IndexPageScraperWorker(webapp2.RequestHandler):
  def post(self):
    page_num = self.request.get('page_num')
    logger.info('%s scraping index page %s', self, page_num)
    post_urls = scrape_index_page(page_num)
    cookie = uuid.uuid4()
    for post_url in post_urls[0:5]:
      taskqueue.add(
        url='/task/PostPageScraperWorker',
        params={
          'url': post_url,
          'index_page_num': page_num,
          'scraper_cookie': cookie
        })


class PostPageScraperWorker(webapp2.RequestHandler):
  def post(self):
    post_url = self.request.get('url')
    index_page_num = self.request.get('index_page_num')
    cookie = self.request.get('scraper_cookie')
    logger.info('%s scraping post page %s', self, post_url)
    post_title, post_time, comments = scrape_post_page(
      post_url)
    age = datetime.datetime.now() - post_time
    if (age < MAX_POST_AGE and
        not memcache.get(index_page_num, namespace=cookie)):
      memcache.set(index_page_num, True, namespace=cookie, time=3600)
      next_page_num = int(index_page_num) + 1
      logger.info(
        'Found an old post (%s) on index page %s, queuing index page %s',
        age, index_page_num, next_page_num)
      taskqueue.add(
        url='/task/IndexPageScraperWorker',
        params={
          'page_num': next_page_num
          })


def scrape_post_page(url):
  result = urllib2.urlopen(url)
  if result.getcode() == 200:
    post_title, post_time, comments = parse_post_page(url, result.read())
    return post_title, post_time, comments


COMMENT_TIMESTAMP_RE = re.compile(
  'posted by .* at ([0-9]+:[0-9]+ (?:AM|PM) +on [A-Za-z]+ [0-9]+)')


def parse_post_page(url, html):
  soup = bs4.BeautifulSoup(html)
  title_h1 = soup.find('h1', class_='posttitle')
  post_title = title_h1.contents[0]
  logger.info('post title=%s', post_title)
  date_div = soup.find('span', class_='smallcopy')
  date_str = date_div.contents[0].strip()
  post_time = datetime.datetime.strptime(date_str, '%B %d, %Y')
  logger.info('post time=%s', post_time)
  # The last <div class="comments"> says "You are not currently logged
  # in."
  comments = []
  comment_divs = soup.find_all('div', class_='comments')[:-1]
  for comment_div in comment_divs:
    if comment_div.find('script'):
      # It's an ad :(
      continue
    # Fixup anchors.
    #logger.info('%s', comment_div)
    for anchor in comment_div.find_all('a'):
      if 'href' in anchor:
        anchor['href'] = urlparse.urljoin(
          url, anchor['href'])
      del anchor['target']
    timestamp_span = comment_div.find_all('span', class_='smallcopy')[-1]
    timestamp_str = COMMENT_TIMESTAMP_RE.match(
      timestamp_span.get_text()).group(1)
    #logger.info('%s', timestamp_str)
    comment_time = datetime.datetime.strptime(
      timestamp_str, '%I:%M %p  on %B %d')
    comment_time = comment_time.replace(year=post_time.year)
    #logger.info('%s', comment_time)
    comments.append(comment_div.prettify())
  logger.info('Found %s comments at %s', len(comments), url)
  return post_title, post_time, comments


def scrape_index_page(page_num):
  url = METAFILTER_INDEX_URL.substitute(page_num=page_num)
  result = urllib2.urlopen(url)
  if result.getcode() == 200:
    post_urls = parse_index_page(url, result.read())
    return post_urls


def parse_index_page(base_url, html):
  soup = bs4.BeautifulSoup(html)
  post_urls = []
  for div in soup.find_all('div', class_='posttitle'):
    a = div.find('a')
    post_url = urlparse.urljoin(base_url, a.get('href'))
    post_urls.append(post_url)
  return post_urls



def save_posts(posts):
  pass
