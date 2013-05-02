import datetime
import urlparse
import re

from lxml import etree
from lxml import cssselect
from lxml import html as lxml_html

from secretmefi import data


PAGE_DATE_FMT = '%B %d'
NUM_COMMENTS_RE = re.compile('([0-9]+) comment')
PAGE_POST_TIMESTAMP_RE = re.compile(' at ([0-9]+:[0-9]+ (?:AM|PM))  -')
PAGE_POST_TIMESTAMP_FMT = '%I:%M %p'


class Error(Exception):
  pass


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
    for element in tree.iter('div', 'h2'):
      if element.tag == 'h2':
        yield ('date', element)
      elif (element.tag == 'div' and 'class' in element.attrib and
            'post' in element.attrib['class'].split()):
        yield ('post', element)
