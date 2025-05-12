# Copyright (c) 2023 nggit

import re

from . import handlers
from .utils import getoptions


class Routes(dict):
    def __init__(self):
        self[0] = [
            (400, handlers.error_400, '400', {}),
            (404, handlers.error_404, '404', dict(request=None,
                                           globals=None,
                                           status=(404, b'Not Found'),
                                           stream=False)),
            # must be at the very end
            (500, handlers.error_500, '500', {})
        ]
        self[1] = [
            (
                b'^/+(?:\\?.*)?$',
                handlers.index, dict(status=(503, b'Service Unavailable'))
            )
        ]
        self[-1] = []

    def add(self, func, path='/', kwargs=None):
        # The path string before any modifications
        route_name = path

        if not kwargs:
            kwargs = getoptions(func)

        # If the path is a regex, it will start with ^ or end with $
        if path.startswith('^') or path.endswith('$'):
            pattern = path.encode('latin-1')
            self[-1].append((pattern, func, kwargs))
        else:
            path = path.split('?', 1)[0].strip('/').encode('latin-1')

            if b"<" in path:
                # capture the values within < and >
                path_vars = re.findall(rb'<([\w\:]+)>', path)

                # for each captured value,
                for v in path_vars:
                    # determine the variable name and char class
                    name, var_type = v.split(b':')
                    char_class = b"\w"

                    if var_type == "int":
                        char_class = b"\d"

                    # replace the <value> in the path with an appropriate named regex group 
                    path = path.replace(b'<%s>' % v, rb'(?P<%s>%s+)' % (name, char_class))


            if path == b'':
                key = 1
                pattern = self[1][0][0]
                self[key] = [(pattern, func, route_name, kwargs)]
            else:
                parts = path.split(b'/', 254)
                key = bytes([len(parts)]) + parts[0]
                pattern = b'^/+%s(?:/+)?(?:\\?.*)?$' % path

                if key in self:
                    self[key].append((pattern, func, route_name, kwargs))
                else:
                    self[key] = [(pattern, func, route_name, kwargs)]

    def compile(self):
        for key in self:
            for i, h in enumerate(self[key]):
                pattern, *handler = h

                if isinstance(pattern, bytes):
                    self[key][i] = (re.compile(pattern), *handler)
