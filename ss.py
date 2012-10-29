#!/usr/bin/env python

import cgi
import os
from os import path
import traceback
import sys
import types
import mimetools

from urlparse import urlparse
from urlparse import parse_qs
from StringIO import StringIO
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer


port = 8000
iface = '0.0.0.0'
root_path = None


def parse_args():
    description='Silly Server for mocking real http servers'
    options = [
        {
            "dest": "root_dir",
            "required": False,
            "metavar": "/dir/somedir",
            "help": """Directory where your fake responses are waiting for me.
            If not provided - default response will be used everywhere.""",
            "type": str,
            "key": "-d",
        }, 
        {
            "dest": "port",
            "required": False,
            "metavar": "port",
            "help": "Port to listen on. Default is 8000.",
            "type": int,
            "key": "-p"
        }
    ]
    try:
        import argparse
        parser = argparse.ArgumentParser(description=description)
        for o in options:
            parser.add_argument(o["key"], dest=o["dest"], required=o["required"], metavar=o["metavar"],
                                help=o["help"], type=o["type"])
        return vars(parser.parse_args())
    except ImportError:
        import optparse
        parser = optparse.OptionParser(description=description)
        for o in options:
            parser.add_option(o["key"], dest=o["dest"], metavar=o["metavar"],
                              help=o["help"], type=o["type"])
        return vars(parser.parse_args()[0])


class DefaultReposnse(object):

    def __init__(self):
        self.status = 200
        self.content = "Hi, I'm default response."
        self.headers = []

    def get_status(self):
        return self.status

    def get_content(self):
        return self.content

    def get_headers(self):
        return self.headers


class Response(DefaultReposnse):

    def __init__(self, status=None, content=None, headers=None):
        super(Response, self).__init__()
        if status:
            self.status = status
        if content:
            self.content = content
        if headers:
            self.headers = headers


class ResponseBuilder(object):

    def __init__(self, root_path):
        if not root_path:
            self.root_path = None
        elif not path.exists(root_path):
            print "\nResponseBuilder: Root path does not exist. I will use default response everywhere.\n"
            self.root_path = None
        else:
            self.root_path = path.abspath(root_path)

    def _append_slash(self, p):
        if not p.endswith("/"):
            p += "/"
        return p

    def _get_content(self, filename):
        if (path.isfile(filename)):
            try:
                f = open(filename, "r")
                c = f.read()
                f.close()
                return c
            except Exception as e:
                print "Can't read '%s'" % filename
                print e
                print "\n"
        return None

    def _get_headers(self, filename):
        if (path.isfile(filename)):
            try:
                f = open(filename, "r")
                strip = lambda s: s if len(s)==0 else s[0]+s[1:].strip()
                headers_raw = "\r\n".join(map(strip, f.readlines()[1:]))
                f.close()
                res = []
                headers = mimetools.Message(StringIO(headers_raw)).dict
                for k in headers:
                    res.append(tuple([k, headers[k]])) 
                return res
            except Exception as e:
                print "Can't parse headers from '%s'" % filename
                print e
                print "\n"
        return None

    def _get_status(self, filename):
        if (path.isfile(filename)):
            try:
                f = open(filename, "r")
                l = f.readline()
                f.close()
                return int(l)
            except Exception as e:
                print "Can't get status from '%s'" % filename
                print e
                print "\n"
        return None

    def get_response(self, p, method):
        if not self.root_path:
            return Response()
        try:
            context = self._append_slash(self.root_path + p)
            context = path.abspath(context)
            if not self.root_path in context:
                raise Exception("Can't go into '%s' it's out of root dir '%s'." % (context, self.root_path))
            if not path.isdir(context):
                raise Exception("Directory '%s' does not exist." % context)
            content_filename = "%s/%s" % (context, method)
            content = self._get_content(content_filename)
            headers = self._get_headers(content_filename + "_H")
            status = self._get_status(content_filename + "_H")
            return Response(content=content, status=status, headers=headers)
        except Exception as e:
            print "\nResponseBuilder: oh, i got some error:"
            print e
            print "Using default response.\n"
            return Response()


class SillyMetaclass(type):

    def __new__(cls, name, bases, attrs):

        def get_wrapper(name, f):
            def wrapper(self, *args, **kwargs):
                print "-"*80
                path = self._get_path()
                method = self.command
                resp = self.response_builder.get_response(path, method)
                self._send_response(resp)
                self._log_get_params()
                f(self, *args, **kwargs)
                print "-"*80
            return wrapper

        for k in attrs:
            v = attrs[k]
            if k.startswith("do_") and isinstance(v, types.FunctionType):
                attrs[k] = get_wrapper(k, v)
        if object not in bases:
            bases += tuple([object])
        return super(SillyMetaclass, cls).__new__(cls, name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        kwargs["root_path"] = root_path
        super(SillyMetaclass, cls).__call__(*args, **kwargs)        


class SillyHandler(BaseHTTPRequestHandler):

    __metaclass__ = SillyMetaclass

    def __init__(self, *args, **kwargs):
        self.response_builder = ResponseBuilder(kwargs.pop("root_path", None))
        super(SillyHandler, self).__init__(*args, **kwargs)

    def _get_path(self):
        return urlparse(self.path).path

    def _get_query(self):
        return parse_qs(urlparse(self.path).query, keep_blank_values=True)

    def _send_response(self, response):
        self.send_response(response.get_status())
        headers = response.get_headers()
        for h in headers:
            self.send_header(h[0], h[1])
        self.end_headers()
        self.wfile.write(response.get_content())
        self.end_headers()

    def _log_get_params(self):
        q = self._get_query()
        if q:
            print "\nGot some GET params here:"
            for k in q:
                print "%s: %s" % (k, q[k])

    def _log_payload(self):
        ctype = self.headers.getheader('content-type')
        if not ctype:
            print "\nPayload: no content-type here, skip the body"
            return
        ctype, pdict = cgi.parse_header(ctype)
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            postvars = {}
        if postvars:
            print "\nGot some payload:"
            for k in postvars:
                print "%s: %s" % (k, postvars[k])

    def do_GET(self):
        pass

    def do_POST(self):
        self._log_payload()

    def do_HEAD(self):
        self._log_payload()

    def do_PUT(self):
        self._log_payload()

    def do_DELETE(self):
        self._log_payload()

    def do_TRACE(self):
        self._log_payload()

    def do_OPTIONS(self):
        self._log_payload()

    def do_PATCH(self):
        self._log_payload()


if __name__ == '__main__':
    try:
        args = parse_args()
        if args["root_dir"]:
            root_path = args["root_dir"]
        if args["port"]:
            port = args["port"]
        httpd = HTTPServer(tuple([iface, port]), SillyHandler)
        print "Starting..."
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "\n"
        print "-"*80
        print "Bye!"
    except Exception:
        print "\n\n"
        traceback.print_exc(file=sys.stdout)
        print "\n\nOH SHI..."


