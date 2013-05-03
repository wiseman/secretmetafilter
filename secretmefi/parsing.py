import datetime
import itertools
import logging
import re
import urlparse

from lxml import etree
from lxml import cssselect
from lxml import html as lxml_html

from secretmefi import data

logger = logging.getLogger(__name__)

PAGE_DATE_FMT = '%B %d'
NUM_COMMENTS_RE = re.compile('([0-9]+) comment')
PAGE_POST_TIMESTAMP_RE = re.compile(' at ([0-9]+:[0-9]+ (?:AM|PM))  -')
PAGE_POST_TIMESTAMP_FMT = '%I:%M %p'


class Error(Exception):
  pass


def stringify_children(node):
  parts = ([node.text] +
           list(itertools.chain(
             *([c.text, etree.tostring(c, encoding=unicode), c.tail]
               for c in node.getchildren()))) +
           [node.tail])
  # filter removes possible Nones in texts and tails
  return ''.join(filter(None, parts))


COMMENT_TIMESTAMP_RE = re.compile(
  'posted by .* at ([0-9]+:[0-9]+ (?:AM|PM) +on [A-Za-z]+ [0-9]+)')

POST_TIMESTAMP_RE = re.compile(
  '^([A-Za-z]+ [0-9]+, [0-9]+ [0-9]+:[0-9]+ (?:AM|PM)).*')


class MetafilterPostPageParser(object):
  def __init__(self, base_url=None, html=None):
    self.post = None
    self._parse(base_url, html)

  def _parse(self, base_url, html):
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
      for anchor in comment_div.xpath('.//a'):
        if 'href' in anchor.attrib:
          anchor.attrib['href'] = urlparse.urljoin(
            base_url, anchor.get('href'))
        if 'target' in anchor.attrib:
          del anchor.attrib['target']
      timestamp_span = cssselect.CSSSelector('span.smallcopy')(comment_div)[-1]
      timestamp_str = COMMENT_TIMESTAMP_RE.match(
        timestamp_span.text_content()).group(1)
      comment_time = datetime.datetime.strptime(
        timestamp_str, '%I:%M %p  on %B %d')
      comment_time = comment_time.replace(year=post_time.year)
      comments.append(data.Comment(
        html=etree.tostring(comment_div, encoding=unicode),
        posted_time=comment_time))
    logger.info('Found %s comments at %s', len(comments), base_url)
    self.post = data.Post(
      url=base_url,
      title=post_title,
      posted_time=post_time,
      num_comments=len(comments),
      comments=comments)


class MetafilterIndexPageParser(object):
  """Parses a Metafilter index page.  Sets the posts field to be a list
  of Posts that contain only the following info:

    url
    posted_time
    num_comments
  """
  def __init__(self, base_url=None, html=None, now=None):
    self.posts = []
    self._now = now or datetime.datetime.now()
    self._parse(base_url, html)

  def _parse(self, base_url, html):
    post_date = None
    for ele_type, element in self._page_iter(html):
      if ele_type == 'date':
        post_date = datetime.datetime.strptime(
          element.text_content().strip(), PAGE_DATE_FMT)
        post_date = post_date.replace(year=self._now.year)
      elif ele_type == 'post':
        if not post_date:
          raise Error('Saw post before finding post date.')
        self._parse_post(base_url, post_date, element)

  def _parse_post(self, base_url, post_date, element):
    last_smallcopy = element.xpath("(span[@class='smallcopy'])[last()]")[0]
    last_a = last_smallcopy.xpath("(a)[last()]")[0]
    post_url = urlparse.urljoin(base_url, last_a.get('href'))
    match = NUM_COMMENTS_RE.search(last_a.text_content())
    num_comments = int(match.group(1))
    smallcopy = last_smallcopy.text_content()
    match = PAGE_POST_TIMESTAMP_RE.search(smallcopy)
    post_timestamp = datetime.datetime.strptime(
      match.group(1), PAGE_POST_TIMESTAMP_FMT)
    post_timestamp = post_timestamp.replace(
      year=post_date.year, month=post_date.month, day=post_date.day)
    post = data.Post(
      url=post_url,
      num_comments=num_comments,
      posted_time=post_timestamp)
    self.posts.append(post)

  def _page_iter(self, html):
    tree = lxml_html.document_fromstring(html)
    for element in tree.iter():
      if element.tag == 'h2':
        yield ('date', element)
      elif (element.tag == 'div' and 'class' in element.attrib and
            'post' in element.attrib['class'].split()):
        yield ('post', element)
