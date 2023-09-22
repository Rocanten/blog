

# If your site is available via HTTPS, make sure SITEURL begins with https://
SITEURL = 'https://rocanten.ru'
RELATIVE_URLS = False

FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = 'feeds/{slug}.atom.xml'

DELETE_OUTPUT_DIRECTORY = True

AUTHOR = 'Олег Прокофьев'
SITENAME = 'Блог Олега Прокофьева'
SITESUBTITLE = 'Пишу на темы:'

PATH = 'content'

TIMEZONE = 'Europe/Moscow'

DEFAULT_LANG = 'ru'

THEME = 'themes/simple'

DEFAULT_PAGINATION = 20

STATIC_PATHS = ('images', 'misc')

EXTRA_PATH_METADATA = {'misc/CNAME': {'path': 'CNAME'},}

SHOW_AUTHOR = False

GOOGLE_TAG_ID = 'G-3GRRGS2JQX'
YANDEX_METRIKA_ID = '95028658'