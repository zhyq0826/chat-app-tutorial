# -*- coding:utf-8 -*-

import uuid
import logging

from tornado.options import define, options
import tornado.options
import tornado.escape
import tornado.web
from tornado import gen
from tornado.concurrent import Future


import setting
import turbo.register
import turbo.app
import turbo.log

turbo.app_config.web_application_setting.update(setting.WEB_APPLICATION_SETTING)

define("port", default=8888, type=int)


class MixinHandler(turbo.app.BaseHandler):
    pass


class BaseHandler(MixinHandler):

    _session = None

    def initialize(self):
        super(BaseHandler, self).initialize()
        self._params = self.parameter
        self._skip = 0
        self._limit = 0

    def prepare(self):
        super(BaseHandler, self).prepare()
        self._skip = abs(self._params['skip']) if self._params.get(
            'skip', None) else 0
        self._limit = abs(self._params['limit']) if self._params.get(
            'limit', None) else 20


class MessageBuffer(object):

    def __init__(self):
        self.waiters = set()
        self.cache = []
        self.cache_size = 200

    def wait_for_messages(self, cursor=None):
        # Construct a Future to return to our caller.  This allows
        # wait_for_messages to be yielded from a coroutine even though
        # it is not a coroutine itself.  We will set the result of the
        # Future when results are available.
        result_future = Future()
        if cursor:
            new_count = 0
            for msg in reversed(self.cache):
                if msg["id"] == cursor:
                    break
                new_count += 1
            if new_count:
                result_future.set_result(self.cache[-new_count:])
                return result_future
        self.waiters.add(result_future)
        return result_future

    def cancel_wait(self, future):
        self.waiters.remove(future)
        # Set an empty result to unblock any coroutines waiting.
        future.set_result([])

    def new_messages(self, messages):
        logging.info("Sending new message to %r listeners", len(self.waiters))
        for future in self.waiters:
            future.set_result(messages)
        self.waiters = set()
        self.cache.extend(messages)
        if len(self.cache) > self.cache_size:
            self.cache = self.cache[-self.cache_size:]


GLOBAL_MESSAGE_BUFFER = MessageBuffer()


class MainHandler(BaseHandler):

    def get(self):
        self.render("index.html", messages=GLOBAL_MESSAGE_BUFFER.cache)


class MessageNewHandler(BaseHandler):

    def post(self):
        message = {
            "id": str(uuid.uuid4()),
            "body": self.get_argument("body"),
        }
        # to_basestring is necessary for Python 3's json encoder,
        # which doesn't accept byte strings.
        message["html"] = tornado.escape.to_basestring(
            self.render_string("message.html", message=message))
        if self.get_argument("next", None):
            self.redirect(self.get_argument("next"))
        else:
            self.write(message)
        GLOBAL_MESSAGE_BUFFER.new_messages([message])


class MessageUpdatesHandler(BaseHandler):

    @gen.coroutine
    def post(self):
        cursor = self.get_argument("cursor", None)
        # Save the future returned by wait_for_messages so we can cancel
        # it in wait_for_messages
        self.future = GLOBAL_MESSAGE_BUFFER.wait_for_messages(cursor=cursor)
        messages = yield self.future
        if self.request.connection.stream.closed():
            return
        self.write(dict(messages=messages))

    def on_connection_close(self):
        GLOBAL_MESSAGE_BUFFER.cancel_wait(self.future)


turbo.register.register_group_urls('', [
    (r"/", MainHandler),
    (r"/a/message/new", MessageNewHandler),
    (r"/a/message/updates", MessageUpdatesHandler),
])


if __name__ == '__main__':
    tornado.options.parse_command_line()
    turbo.app.start(options.port)
