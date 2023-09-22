AUTHOR = 'Олег Прокофьев'
SITENAME = 'Блог Олега Прокофьева'
SITESUBTITLE = 'Пишу на темы:'
SITEURL = 'http://127.0.0.1:8000'

PATH = 'content'

TIMEZONE = 'Europe/Moscow'

DEFAULT_LANG = 'ru'

THEME = 'themes/simple'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'https://getpelican.com/'),
         ('Python.org', 'https://www.python.org/'),
         ('Jinja2', 'https://palletsprojects.com/p/jinja/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('You can add links in your config file', '#'),
          ('Another social link', '#'),)

DEFAULT_PAGINATION = 20

STATIC_PATHS = ('images', 'misc')

EXTRA_PATH_METADATA = {'misc/CNAME': {'path': 'CNAME'},}

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

SHOW_AUTHOR = False

GOOGLE_TAG_ID = 'G-3GRRGS2JQX'
YANDEX_METRIKA_ID = '95028658'
