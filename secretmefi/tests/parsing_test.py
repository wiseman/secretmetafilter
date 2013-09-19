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


class MetafilterPostPageParserTest(unittest.TestCase):
  def test_parsing(self):
    self.maxDiff = None
    with open(os.path.join(THIS_DIR, 'post-page.html'), 'rb') as f:
      html = f.read()
    parser = parsing.MetafilterPostPageParser(
      'http://metafilter.com/post-page', html)
    post = parser.post
    self.assertEqual(
      post.to_dict(),
      {'comments': [{'html': u'<div class="comments">see, this was needed.<br><span class="smallcopy">posted by <a href="http://www.metafilter.com/user/153960">percor</a> at <a href="http://metafilter.com/127658/How-Having-a-Boyfriend-Can-Help-You-Get-the-Boyfriend-of-Your-Dreams#4957373">7:10 PM</a>  on May 2 </span></div>',
                     'posted_time': '2013-05-02 19:10:00'},
                    {'html': u'<div class="comments">Thank goodnes, something to replace the void that Sarah Haskins left in my life when she left Current.<br><span class="smallcopy">posted by <a href="http://www.metafilter.com/user/152152">windykites</a> at <a href="http://metafilter.com/127658/How-Having-a-Boyfriend-Can-Help-You-Get-the-Boyfriend-of-Your-Dreams#4957381">7:17 PM</a>  on May 2 [<a href="http://metafilter.com/favorited/2/4957381" style="font-weight:normal;" title="3 users marked this as favorite">3 favorites</a>] </span></div>',
                     'posted_time': '2013-05-02 19:17:00'},
                    {'html': u'<div class="comments"><em>L\xe2\x80\x99Or\xc3\xa9al Launches Line of Anti-Bullying Makeup for Young Girls</em><br><br>\r\nI laughed.<br><span class="smallcopy">posted by <a href="http://www.metafilter.com/user/80649">The Whelk</a> at <a href="http://metafilter.com/127658/How-Having-a-Boyfriend-Can-Help-You-Get-the-Boyfriend-of-Your-Dreams#4957383">7:19 PM</a>  on May 2 [<a href="http://metafilter.com/favorited/2/4957383" style="font-weight:normal;" title="1 user marked this as favorite">1 favorite</a>] </span></div>',
                     'posted_time': '2013-05-02 19:19:00'},
                    {'html': u'<div class="comments">Needs "Fat? Hate yourself!"<br><span class="smallcopy">posted by <a href="http://www.metafilter.com/user/23303">BrotherCaine</a> at <a href="http://metafilter.com/127658/How-Having-a-Boyfriend-Can-Help-You-Get-the-Boyfriend-of-Your-Dreams#4957396">7:37 PM</a>  on May 2 [<a href="http://metafilter.com/favorited/2/4957396" style="font-weight:normal;" title="1 user marked this as favorite">1 favorite</a>] </span></div>',
                     'posted_time': '2013-05-02 19:37:00'},
                    {'html': u'<div class="comments">Oh god, I laughed so hard I nearly peed myself when I saw the premise of the Rape in America interview. <br><br>\r\nIt\'s funny because the world is dumb.<br><span class="smallcopy">posted by <a href="http://www.metafilter.com/user/74248">phunniemee</a> at <a href="http://metafilter.com/127658/How-Having-a-Boyfriend-Can-Help-You-Get-the-Boyfriend-of-Your-Dreams#4957399">7:40 PM</a>  on May 2 </span></div>',
                     'posted_time': '2013-05-02 19:40:00'},
                    {'html': u'<div class="comments">I look forward to folks spreading these articles accidentally unironically:<br><br><a href="http://www.reductress.com/starting-early-inspiring-faith-and-gratitude-in-your-newborn-daughter/">"Challenge Your Daughter to Say One Nice Thing a Day, Even if It\xe2\x80\x99s Hard for Them."</a><br><span class="smallcopy">posted by <a href="http://www.metafilter.com/user/36760">anotherpanacea</a> at <a href="http://metafilter.com/127658/How-Having-a-Boyfriend-Can-Help-You-Get-the-Boyfriend-of-Your-Dreams#4957401">7:41 PM</a>  on May 2 </span></div>',
                     'posted_time': '2013-05-02 19:41:00'},
                    {'html': u'<div class="comments"><i>How Infidelity Can Spice Up Your Marriage </i><br><br>\r\nSome of this isn\'t even parody. I\'m confident I\'ve seen that one on a magazine cover in a checkout line at least once.     <br><br>\r\nAlso, "womanspiration" sounds like what an ex of mine used to humorously call "body dew".  As in, this isn\'t sweat, it\'s body dew.<br><span class="smallcopy">posted by <a href="http://www.metafilter.com/user/16431">George_Spiggott</a> at <a href="http://metafilter.com/127658/How-Having-a-Boyfriend-Can-Help-You-Get-the-Boyfriend-of-Your-Dreams#4957404">7:43 PM</a>  on May 2 </span></div>',
                     'posted_time': '2013-05-02 19:43:00'},
                    {'html': u'<div class="comments">Jenny Lawson (The Bloggess) tweeted about this this afternoon and crashed the site. It looks hilarious. Or shall I say "hysterical".<br><span class="smallcopy">posted by <a href="http://www.metafilter.com/user/103301">ThatCanadianGirl</a> at <a href="http://metafilter.com/127658/How-Having-a-Boyfriend-Can-Help-You-Get-the-Boyfriend-of-Your-Dreams#4957407">7:45 PM</a>  on May 2 </span></div>',
                     'posted_time': '2013-05-02 19:45:00'}],
       'last_comment_time': datetime.datetime(2013, 5, 2, 19, 45),
       'num_comments': 8,
       'posted_time': datetime.datetime(2013, 5, 2, 19, 2),
       'title': u'How Having a Boyfriend Can Help You Get the Boyfriend of Your Dreams',
       'url': 'http://metafilter.com/post-page'})


if __name__ == '__main__':
  unittest.main()
