import os
import sys
from tornado.util import ObjectDict

# server name
SERVER_NAME = 'chat-app-tutorial'

# server dir
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
# project dir
sys.path.append(SERVER_DIR)

# tornado web application settings
# details in
# http://www.tornadoweb.org/en/stable/web.html#tornado.web.Application.settings
WEB_APPLICATION_SETTING = ObjectDict(
    static_path=os.path.join(SERVER_DIR, "static"),
    template_path=os.path.join(SERVER_DIR, "templates"),
    xsrf_cookies=False,
    cookie_secret="3%$334ma?asdf2987^%23&^%$2",
    debug=True,
)

# turbo app setting
TURBO_APP_SETTING = ObjectDict(
    log=ObjectDict(
        log_path=os.path.join("", SERVER_NAME + '.log'),
        log_size=500 * 1024 * 1024,
        log_count=3,
    ),
    session_config=ObjectDict({
        'name': 'session-id',
        'secret_key': 'o387xn4ma?adfasdfa83284&^%$2'
    }),
)
