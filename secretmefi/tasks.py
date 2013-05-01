import datetime
import logging
import re
import robotparser
import string
import urllib2
import urlparse
import uuid

import bs4
from google.appengine.api import memcache
from google.appengine.api import taskqueue
import webapp2

logger = logging.getLogger(__name__)


METAFILTER_ROBOT_RULES_URL = 'http://metafilter.com/robots.txt'

METAFILTER_INDEX_URL = string.Template(
  'http://metafilter.com/index.cfm?page=$page_num')

MAX_POST_AGE = datetime.timedelta(days=3)

USER_AGENT = 'secretmefibot'

FULL_USER_AGENT = ('Mozilla/5.0 (compatible; %s/0.1; '
                   '+http://secretmefi.appspot.com/bot.html)') % (
                     USER_AGENT)


def get_robot_rules():
  rules = memcache.get('robots.txt')
  if not rules:
    logger.info('Fetching robot rules at %s', METAFILTER_ROBOT_RULES_URL)
    rules = robotparser.RobotFileParser()
    rules.set_url(METAFILTER_ROBOT_RULES_URL)
    rules.read()
    memcache.set('robots.txt', rules, time=3600)
  return rules


def can_fetch_url(url):
  robot_rules = get_robot_rules()
  return robot_rules.can_fetch(USER_AGENT, url)


def fetch_url(url):
  if can_fetch_url(url):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', USER_AGENT)]
    response = opener.open(url)
    return response
  else:
    logger.info('Skipping URL %s due to exclusion by robots.txt', url)


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


class ScrapingHistory(object):
  @staticmethod
  def has_been_scraped(url, cookie):
    return memcache.get(url, namespace=cookie)

  @staticmethod
  def record_scrape(url, cookie):
    memcache.set(url, True, namespace=cookie, time=3600)



class PostPageScraperWorker(webapp2.RequestHandler):
  def post(self):
    post_url = self.request.get('url')
    index_page_num = self.request.get('index_page_num')
    cookie = self.request.get('scraper_cookie')
    logger.info('%s scraping post page %s', self, post_url)
    post_title, post_time, comments = scrape_post_page(
      post_url)
    age = datetime.datetime.now() - post_time
    index_url = get_index_page_url(index_page_num)
    if (age < MAX_POST_AGE and
        not ScrapingHistory.has_been_scraped(index_url, cookie)):
      ScrapingHistory.record_scrape(index_url, cookie)
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
  result = fetch_url(url)
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


def get_index_page_url(page_num):
  return METAFILTER_INDEX_URL.substitute(page_num=page_num)


def scrape_index_page(page_num):
  url = get_index_page_url(page_num)
  result = fetch_url(url)
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
