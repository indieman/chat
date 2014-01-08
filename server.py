__author__ = 'indieman'

import os.path
import json

import tornado.ioloop
import tornado.web
from tornado import gen
from tornado.web import asynchronous
from bson.objectid import ObjectId
from tornado.options import parse_command_line, options, define

import motor
from schematics.exceptions import ValidationError

from models import Message

define("port", default=8888, help="run on the given port", type=int)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class ClearHandler(tornado.web.RequestHandler):
    def get(self):
        db = self.settings['db']
        db.messages.remove()


class MainHandler(tornado.web.RequestHandler):
    @asynchronous
    @gen.engine
    def get(self):
        db = self.settings['db']
        cursor = db.messages.find().sort([('_id', 1)])
        message_list = []
        while (yield cursor.fetch_next):
            message = cursor.next_object()
            message_list.append(message)
        self.render('index.html', messages=message_list)   

    @asynchronous
    @gen.engine
    def post(self):
        raw_message = {
            'nickname': self.get_argument('nickname', None),
            'body': self.get_argument('body', None),
        }
        message = Message(raw_message)
        try:
            message.validate()
            db = self.settings['db']
            message_id = yield motor.Op(db.messages.insert, message.to_primitive())
            message = message.to_primitive()
            message['_id'] = u'%s' % message_id

            message["html"] = tornado.escape.to_basestring(
                self.render_string("message.html", message=message))
            message['status'] = 'ok'
            self.write(message)
            self.finish()
        except ValidationError as e:
            error = e.message
            error['status'] = 'error'
            self.write(JSONEncoder().encode(error))
            print error
            self.finish()


class MessageUpdatesHandler(tornado.web.RequestHandler):
    @asynchronous
    @gen.engine
    def post(self):
        last_id = self.get_argument('lastId', None)

        if last_id is not None and last_id != u'undefined':
            new_messages = []
            cursor = self.settings['db'].messages.\
                find({'_id': {'$gt': ObjectId(last_id)}}).sort([('_id', 1)])
            while(yield cursor.fetch_next):
                message = cursor.next_object()
                message['html'] = tornado.escape.to_basestring(
                    self.render_string('message.html', message=message))
                new_messages.append(message)
            if new_messages:
                self.write(JSONEncoder().encode(new_messages))
                self.finish()
            else:
                self.finish()


if '__main__' == __name__:

    parse_command_line()
    db = motor.MotorClient().open_sync().onion
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/a/message/updates", MessageUpdatesHandler),
            (r"/clearall", ClearHandler),
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        db=db,
        xsrf_cookies=False
    )
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()