# Secret Metafilter

Secret Metafilter is a web app that highlights
[Metafilter](http://metafilter.com/) discussions that are still active
on older posts.

It is a Google AppEngine app that periodically scrapes the past month
of Metafilter and renders an HTML display of the most recent
discussions that are still active.

You can see it running at
[http://secretmefi.appspot.com/](http://secretmefi.appspot.com/).

![Secret Metafilter screenshot](https://github.com/wiseman/secretmetafilter/raw/master/secretmefi.png
"Secret Metafilter screenshot")

## To run tests

```
$ virtualenv env
$ env/bin/pip install NoseGAE argparse distribute lxml nose wsgiref
$ env/bin/python env/bin/nosetests --with-gae --gae-lib-root=/usr/local/google_appengine --without-sandbox
```

