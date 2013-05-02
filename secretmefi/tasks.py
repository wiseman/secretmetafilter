import datetime
import itertools
import logging
import re
import robotparser
import string
import urllib2
import urlparse

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from lxml import etree
from lxml import cssselect
from lxml import html as lxml_html
import webapp2

from secretmefi import data

logger = logging.getLogger(__name__)


METAFILTER_ROBOT_RULES_URL = 'http://metafilter.com/robots.txt'

METAFILTER_INDEX_URL = string.Template(
  'http://metafilter.com/index.cfm?page=$page_num')

MAX_POST_AGE = datetime.timedelta(days=31)

MIN_POST_AGE = datetime.timedelta(days=7)

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
    index_posts = scrape_index_page(page_num)
    index_post_num_comments = {p.url: p.num_comments for p in index_posts}
    db_posts = data.get_posts([p.url for p in index_posts])
    db_post_num_comments = {p.url: p.num_comments for p in db_posts}
    for url in index_post_num_comments:
      index_num_comments = index_post_num_comments.get(url)
      db_num_comments = db_post_num_comments.get(url, 0)
      if index_post_num_comments > db_post_num_comments:
        if url in db_post_num_comments:
          logger.info(
            'Queueing %s because it has %s comments now instead of %s',
            url, index_num_comments, db_num_comments)
        else:
          logger.info("Queueing %s because we haven't scraped it before.",
          url)
        taskqueue.add(
          url='/task/PostPageScraperWorker',
          params={'url': url})
      else:
        logger.info(
          'Skipping %s because it still has %s comments', url, db_num_comments)


class PostPageScraperWorker(webapp2.RequestHandler):
  def post(self):
    post_url = self.request.get('url')
    logger.info('%s scraping post page %s', self, post_url)
    post = scrape_post_page(post_url)
    age = datetime.datetime.now() - post.posted_time
    if age <= MAX_POST_AGE:
      if age >= MIN_POST_AGE:
        data.save_post(post)


def scrape_post_page(url):
  result = fetch_url(url)
  if result.getcode() == 200:
    post = parse_post_page(url, result.read())
    return post


COMMENT_TIMESTAMP_RE = re.compile(
  'posted by .* at ([0-9]+:[0-9]+ (?:AM|PM) +on [A-Za-z]+ [0-9]+)')

POST_TIMESTAMP_RE = re.compile(
  '^([A-Za-z]+ [0-9]+, [0-9]+ [0-9]+:[0-9]+ (?:AM|PM)).*')


def stringify_children(node):
  parts = ([node.text] +
           list(itertools.chain(
             *([c.text, etree.tostring(c), c.tail]
               for c in node.getchildren()))) +
           [node.tail])
  # filter removes possible Nones in texts and tails
  return ''.join(filter(None, parts))


def parse_post_page(url, html):
  tree = lxml_html.document_fromstring(html)
  title_h1 = cssselect.CSSSelector('h1.posttitle')(tree)[0]
  # This is ugly, but man I can't figure out a better way with lxml or
  # xpath.
  post_title = stringify_children(title_h1)
  br_pos = post_title.lower().find('<br')
  post_title = post_title[0:br_pos]
  logger.info('post title=%s', post_title)
  date_div = cssselect.CSSSelector('span.smallcopy')(tree)[0]
  date_str = POST_TIMESTAMP_RE.match(date_div.text_content()).group(1)
  post_time = datetime.datetime.strptime(date_str, '%B %d, %Y %I:%M %p')
  logger.info('post time=%s', post_time)
  # The last <div class="comments"> says "You are not currently logged
  # in."
  comments = []
  for comment_div in cssselect.CSSSelector('div.comments')(tree)[:-1]:
    if comment_div.xpath('script'):
      # It's an ad :(
      continue
    # Fixup anchors.
    for anchor in comment_div.xpath('a'):
      if 'href' in anchor.attrib:
        anchor.attrib['href'] = urlparse.urljoin(
          url, anchor.get('href'))
      if 'target' in anchor.attrib:
        del anchor.attrib['target']
    timestamp_span = cssselect.CSSSelector('span.smallcopy')(comment_div)[-1]
    timestamp_str = COMMENT_TIMESTAMP_RE.match(
      timestamp_span.text_content()).group(1)
    #logger.info('%s', timestamp_str)
    comment_time = datetime.datetime.strptime(
      timestamp_str, '%I:%M %p  on %B %d')
    comment_time = comment_time.replace(year=post_time.year)
    #logger.info('%s', comment_time)
    comments.append(data.Comment(
      html=etree.tostring(comment_div),
      posted_time=comment_time))
  logger.info('Found %s comments at %s', len(comments), url)
  return data.Post(
    url=url,
    title=post_title,
    posted_time=post_time,
    num_comments=len(comments),
    comments=comments)


def get_index_page_url(page_num):
  return METAFILTER_INDEX_URL.substitute(page_num=page_num)


def scrape_index_page(page_num):
  url = get_index_page_url(page_num)
  result = fetch_url(url)
  if result.getcode() == 200:
    posts = parse_index_page(url, result.read())
    logger.info('Found %s posts on %s', len(posts), url)
    return posts
  else:
    logger.error('Got HTTP code %s for %s', result.getcode(), url)
    return []


NUM_COMMENTS_RE = re.compile('([0-9]+) comment')


def parse_index_page(base_url, html):
  tree = lxml_html.document_fromstring(html)
  posts = []
  for title_div in cssselect.CSSSelector('div.post')(tree):
    last_smallcopy = title_div.xpath("(span[@class='smallcopy'])[last()]")[0]
    last_a = last_smallcopy.xpath("(a)[last()]")[0]
    post_url = urlparse.urljoin(base_url, last_a.get('href'))
    match = NUM_COMMENTS_RE.search(last_a.text_content())
    num_comments = int(match.group(1))
    posts.append(data.Post(url=post_url, num_comments=num_comments))
  return posts
