#!/usr/bin/env python

# six

import operator
import sys
import types

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

def _add_doc(func, doc):
    """Add documentation to a function."""
    func.__doc__ = doc


def _import_module(name):
    """Import module, returning the module after the last dot."""
    __import__(name)
    return sys.modules[name]


class _LazyDescr(object):

    def __init__(self, name):
        self.name = name

    def __get__(self, obj, tp):
        result = self._resolve()
        setattr(obj, self.name, result)
        # This is a bit ugly, but it avoids running this again.
        delattr(tp, self.name)
        return result


class MovedModule(_LazyDescr):

    def __init__(self, name, old, new=None):
        super(MovedModule, self).__init__(name)
        if PY3:
            if new is None:
                new = name
            self.mod = new
        else:
            self.mod = old

    def _resolve(self):
        return _import_module(self.mod)


class MovedAttribute(_LazyDescr):

    def __init__(self, name, old_mod, new_mod, old_attr=None, new_attr=None):
        super(MovedAttribute, self).__init__(name)
        if PY3:
            if new_mod is None:
                new_mod = name
            self.mod = new_mod
            if new_attr is None:
                if old_attr is None:
                    new_attr = name
                else:
                    new_attr = old_attr
            self.attr = new_attr
        else:
            self.mod = old_mod
            if old_attr is None:
                old_attr = name
            self.attr = old_attr

    def _resolve(self):
        module = _import_module(self.mod)
        return getattr(module, self.attr)



class _MovedItems(types.ModuleType):
    """Lazy loading of moved objects"""


_moved_attributes = [
    MovedAttribute("cStringIO", "cStringIO", "io", "StringIO"),
    MovedAttribute("filter", "itertools", "builtins", "ifilter", "filter"),
    MovedAttribute("map", "itertools", "builtins", "imap", "map"),
    MovedAttribute("reload_module", "__builtin__", "imp", "reload"),
    MovedAttribute("reduce", "__builtin__", "functools"),
    MovedAttribute("StringIO", "StringIO", "io"),
    MovedAttribute("xrange", "__builtin__", "builtins", "xrange", "range"),
    MovedAttribute("zip", "itertools", "builtins", "izip", "zip"),
    MovedAttribute("urlparse", "urlparse", "urllib.parse"),
    MovedAttribute("parse_qs", "urlparse", "urllib.parse"),

    MovedModule("builtins", "__builtin__"),
    MovedModule("configparser", "ConfigParser"),
    MovedModule("copyreg", "copy_reg"),
    MovedModule("http_cookiejar", "cookielib", "http.cookiejar"),
    MovedModule("http_cookies", "Cookie", "http.cookies"),
    MovedModule("html_entities", "htmlentitydefs", "html.entities"),
    MovedModule("html_parser", "HTMLParser", "html.parser"),
    MovedModule("http_client", "httplib", "http.client"),
    MovedModule("BaseHTTPServer", "BaseHTTPServer", "http.server"),
    MovedModule("CGIHTTPServer", "CGIHTTPServer", "http.server"),
    MovedModule("SimpleHTTPServer", "SimpleHTTPServer", "http.server"),
    MovedModule("cPickle", "cPickle", "pickle"),
    MovedModule("queue", "Queue"),
    MovedModule("reprlib", "repr"),
    MovedModule("socketserver", "SocketServer"),
    MovedModule("tkinter", "Tkinter"),
    MovedModule("tkinter_dialog", "Dialog", "tkinter.dialog"),
    MovedModule("tkinter_filedialog", "FileDialog", "tkinter.filedialog"),
    MovedModule("tkinter_scrolledtext", "ScrolledText", "tkinter.scrolledtext"),
    MovedModule("tkinter_simpledialog", "SimpleDialog", "tkinter.simpledialog"),
    MovedModule("tkinter_tix", "Tix", "tkinter.tix"),
    MovedModule("tkinter_constants", "Tkconstants", "tkinter.constants"),
    MovedModule("tkinter_dnd", "Tkdnd", "tkinter.dnd"),
    MovedModule("tkinter_colorchooser", "tkColorChooser",
                "tkinter.colorchooser"),
    MovedModule("tkinter_commondialog", "tkCommonDialog",
                "tkinter.commondialog"),
    MovedModule("tkinter_tkfiledialog", "tkFileDialog", "tkinter.filedialog"),
    MovedModule("tkinter_font", "tkFont", "tkinter.font"),
    MovedModule("tkinter_messagebox", "tkMessageBox", "tkinter.messagebox"),
    MovedModule("tkinter_tksimpledialog", "tkSimpleDialog",
                "tkinter.simpledialog"),
    MovedModule("urllib_robotparser", "robotparser", "urllib.robotparser"),
    MovedModule("winreg", "_winreg"),
]
for attr in _moved_attributes:
    setattr(_MovedItems, attr.name, attr)
del attr

moves = sys.modules["six.moves"] = _MovedItems("moves")

if PY3:
    def b(s):
        return s.encode("latin-1")
    def u(s):
        return s
    if sys.version_info[1] <= 1:
        def int2byte(i):
            return bytes((i,))
    else:
        # This is about 2x faster than the implementation above on 3.2+
        int2byte = operator.methodcaller("to_bytes", 1, "big")
    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO
else:
    def b(s):
        return s
    def u(s):
        return unicode(s, "unicode_escape")
    int2byte = chr
    import StringIO
    StringIO = BytesIO = StringIO.StringIO

if PY3:
    import builtins
    exec_ = getattr(builtins, "exec")


    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value


    print_ = getattr(builtins, "print")
    del builtins

else:
    def exec_(code, globs=None, locs=None):
        """Execute code in a namespace."""
        if globs is None:
            frame = sys._getframe(1)
            globs = frame.f_globals
            if locs is None:
                locs = frame.f_locals
            del frame
        elif locs is None:
            locs = globs
        exec("""exec code in globs, locs""")


    exec_("""def reraise(tp, value, tb=None):
    raise tp, value, tb
""")


    def print_(*args, **kwargs):
        """The new-style print function."""
        fp = kwargs.pop("file", sys.stdout)
        if fp is None:
            return
        def write(data):
            if not isinstance(data, basestring):
                data = str(data)
            fp.write(data)
        want_unicode = False
        sep = kwargs.pop("sep", None)
        if sep is not None:
            if isinstance(sep, unicode):
                want_unicode = True
            elif not isinstance(sep, str):
                raise TypeError("sep must be None or a string")
        end = kwargs.pop("end", None)
        if end is not None:
            if isinstance(end, unicode):
                want_unicode = True
            elif not isinstance(end, str):
                raise TypeError("end must be None or a string")
        if kwargs:
            raise TypeError("invalid keyword arguments to print()")
        if not want_unicode:
            for arg in args:
                if isinstance(arg, unicode):
                    want_unicode = True
                    break
        if want_unicode:
            newline = unicode("\n")
            space = unicode(" ")
        else:
            newline = "\n"
            space = " "
        if sep is None:
            sep = space
        if end is None:
            end = newline
        for i, arg in enumerate(args):
            if i:
                write(sep)
            write(arg)
        write(end)

def with_metaclass(meta, base=object):
    """Create a base class with a metaclass."""
    return meta("NewBase", (base,), {})

# end six


import cgi
from os import path
import traceback
import sys
import types
import email.parser

urlparse = moves.urlparse
parse_qs = moves.parse_qs
BaseHTTPServer = moves.BaseHTTPServer
BaseHTTPRequestHandler = BaseHTTPServer.BaseHTTPRequestHandler
HTTPServer = BaseHTTPServer.HTTPServer


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
            print_("\nResponseBuilder: Root path does not exist. I will use default response everywhere.\n")
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
                print_("Can't read '%s'" % filename)
                print_(e)
                print_("\n")
        return None

    def _get_headers(self, filename):
        if (path.isfile(filename)):
            try:
                f = open(filename, "r")
                strip = lambda s: s if len(s)==0 else s[0]+s[1:].strip()
                headers_raw = "\r\n".join(map(strip, f.readlines()[1:]))
                f.close()
                return email.parser.Parser().parsestr(headers_raw).items()
            except Exception as e:
                print_("Can't parse headers from '%s'" % filename)
                print_(e)
                print_("\n")
        return None

    def _get_status(self, filename):
        if (path.isfile(filename)):
            try:
                f = open(filename, "r")
                l = f.readline()
                f.close()
                return int(l)
            except Exception as e:
                print_("Can't get status from '%s'" % filename)
                print_(e)
                print_("\n")
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
            print_("\nResponseBuilder: oh, i got some error:")
            print_(e)
            print_("Using default response.\n")
            return Response()


class SillyMetaclass(type):

    def __new__(cls, name, bases, attrs):

        def get_wrapper(name, f):
            def wrapper(self, *args, **kwargs):
                print_("-"*80)
                path = self._get_path()
                method = self.command
                resp = self.response_builder.get_response(path, method)
                self._send_response(resp)
                self._log_get_params()
                f(self, *args, **kwargs)
                print_("-"*80)
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


class SillyHandler(with_metaclass(SillyMetaclass, base=BaseHTTPRequestHandler)):

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
            print_("\nGot some GET params here:")
            for k in q:
                print_("%s: %s" % (k, q[k]))

    def _log_payload(self):
        ctype = self.headers.getheader('content-type')
        if not ctype:
            print_("\nPayload: no content-type here, skip the body")
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
            print_("\nGot some payload:")
            for k in postvars:
                print_("%s: %s" % (k, postvars[k]))

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
        print_("Starting...")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print_("\n")
        print_("-"*80)
        print_("Bye!")
    except Exception:
        print_("\n\n")
        traceback.print_exc(file=sys.stdout)
        print_("\n\nOH SHI...")


