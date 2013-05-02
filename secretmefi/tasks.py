import datetime
import itertools
import jinja2
import logging
import os.path
import pretty_timedelta
import re
import robotparser
import string
import urllib2
import urlparse

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import db
from lxml import etree
from lxml import cssselect
from lxml import html as lxml_html
import webapp2

from secretmefi import data
from secretmefi import parsing


logger = logging.getLogger(__name__)
jinja = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.join(
    os.path.dirname(__file__), 'templates')))


def pretty_timedelta_filter(v):
  return pretty_timedelta.pretty_timedelta(v)

jinja.filters['pretty_timedelta'] = pretty_timedelta_filter


MAX_INDEX_PAGE_NUM = 50

METAFILTER_ROBOT_RULES_URL = 'http://metafilter.com/robots.txt'

METAFILTER_INDEX_URL = string.Template(
  'http://metafilter.com/index.cfm?page=$page_num')

MAX_POST_AGE = datetime.timedelta(days=31)
MIN_POST_AGE = datetime.timedelta(days=7)
MIN_COMMENT_AGE = datetime.timedelta(days=4)

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


class HtmlGeneratorWorker(webapp2.RequestHandler):
  def post(self):
    now = datetime.datetime.now()
    posts = db.GqlQuery(
      'SELECT * FROM PostModel WHERE '
      'last_comment_time >= :1 '
      'ORDER BY last_comment_time DESC',
      now - MIN_COMMENT_AGE)
    posts = [p for p in posts if now - p.posted_time > MIN_POST_AGE]
    posts = [data.Post.from_model(p) for p in posts]
    posts = [p.to_dict() for p in posts]
    logger.info('Displaying %s posts', len(posts))
    for p in posts:
      p['posted_timedelta'] = p['posted_time'] - now
    template = jinja.get_template('index.tmpl')
    template_values = {'posts': posts}
    html = template.render(template_values)
    html_model = data.HtmlModel(key_name='index.html')
    html_model.html = html
    html_model.put()


def post_age(post, now):
  return now - post.posted_time


class IndexPageScraperWorker(webapp2.RequestHandler):
  def post(self):
    page_num = int(self.request.get('page_num'))
    logger.info('Scraping index page %s', page_num)
    posts = scrape_index_page(page_num)
    # FOR DEBUGGING
    #posts = posts[0:5]
    now = datetime.datetime.now()
    # We can now decide whether to scrape the next index page: If we
    # don't see any posts that are older than our MAX_POST_AGE.
    scrape_next_index = True
    for post in posts:
      if post_age(post, now) > MAX_POST_AGE:
        logger.info('Aborting index scraping because of %s',
                    post.to_dict())
        scrape_next_index = False
        break
    scrape_next_index = scrape_next_index and page_num < MAX_INDEX_PAGE_NUM
    logger.info('Before filtering: %s posts', len(posts))
    # Filter out all posts that are too new.
    posts = [p for p in posts if post_age(p, now) > MIN_POST_AGE]
    logger.info('After filtering by MIN_POST_AGE: %s posts', len(posts))
    # Filter out all posts that are too old.
    posts = [p for p in posts if post_age(p, now) < MAX_POST_AGE]
    logger.info('After filtering by MAX_POST_AGE: %s posts', len(posts))
    if posts:
      # Now find posts that either haven't been seen before or whose
      # comment counts have changed.
      #
      # Build a map from url -> num_comments on the index page.
      index_post_num_comments = {p.url: p.num_comments for p in posts}
      # Build a map from url -> num_comments in the database.
      db_posts = data.get_posts([p.url for p in posts])
      db_post_num_comments = {p.url: p.num_comments for p in db_posts}
      for url in index_post_num_comments:
        index_num_comments = index_post_num_comments.get(url)
        db_num_comments = db_post_num_comments.get(url, 0)
        if index_num_comments > db_num_comments:
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
            'Skipping %s because it still has %s comments',
            url, db_num_comments)
    if scrape_next_index:
      next_page_num = page_num + 1
      logger.info('Queueing next index page (%s)', next_page_num)
      taskqueue.add(
        url='/task/IndexPageScraperWorker',
        params={'page_num': next_page_num})
    else:
      taskqueue.add(url='/task/HtmlGeneratorWorker')


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
             *([c.text, etree.tostring(c, encoding=unicode), c.tail]
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
      html=etree.tostring(comment_div, encoding=unicode),
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
    parser = parsing.MetafilterIndexPageParser(
      base_url=url,
      html=result.read())
    posts = parser.posts
    logger.info('Scraped info on %s posts from %s', len(posts), url)
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
