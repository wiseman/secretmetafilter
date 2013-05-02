import datetime
import os.path
import pprint
import unittest

from secretmefi import data
from secretmefi import parsing

THIS_DIR = os.path.dirname(__file__)


class MetafilterIndexPageParserTest(unittest.TestCase):
  def test_parsing(self):
    with open(os.path.join(THIS_DIR, 'metafilter-index-0.html'), 'rb') as f:
      html = f.read()
    parser = parsing.MetafilterIndexPageParser('http://metafilter.com/', html)
    posts = parser.posts
    self.assertEqual(len(posts), 50)
    self.assertEqual(
      posts[0].to_dict(),
      {
        'comments': None,
        'last_comment_time': None,
        'num_comments': 22,
        'posted_time': datetime.datetime(2013, 5, 2, 10, 45),
        'title': None,
        'url': 'http://metafilter.com/127644/Crossing-the-Red-Line'
      })
    with open(os.path.join(THIS_DIR, 'metafilter-index-1.html'), 'rb') as f:
      html = f.read()
    parser = parsing.MetafilterIndexPageParser('http://metafilter.com/', html)
    posts = parser.posts
    self.assertEqual(len(posts), 50)
    self.assertEqual(
      posts[0].to_dict(),
      {
        'comments': None,
        'last_comment_time': None,
        'num_comments': 38,
        'posted_time': datetime.datetime(2013, 4, 30, 6, 51),
        'title': None,
        'url': 'http://www.metafilter.com/127543/Is-too-much-news-bad-for-you'
      })


if __name__ == '__main__':
  unittest.main()
