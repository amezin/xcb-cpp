'''Conversions between C names and C++ namespaces'''

class CxxRoot(object):

    def __init__(self):
        self.content = []

    def __str__(self):
        return ''.join(str(item) for item in self.content)

    def path(self, path):
        if not path:
            return self
        for item in self.content:
            if hasattr(item, 'name') and getattr(item, 'name') == path[0]:
                return item.path(path[1:])
        new_namespace = CxxNamespace(path[0])
        self.content.append(new_namespace)
        return new_namespace.path(path[1:])


class CxxNamespace(CxxRoot):

    def __init__(self, name):
        CxxRoot.__init__(self)
        self.name = name

    def __str__(self):
        name = '' if self.name == '' else self.name + ' '
        return 'namespace {}\n{{\n{}}}\n'.format(name, CxxRoot.__str__(self))


NAMESPACES = ['big_requests', 'composite', 'damage', 'dpms', 'dri2', 'dri3',
              'glx', 'present', 'randr', 'record', 'render', 'res',
              'screensaver', 'shape', 'shm', 'sync', 'xc_misc', 'xevie',
              'xf86dri', 'xfixes', 'xinerama', 'input', 'xkb', 'x_print',
              'test', 'xv', 'xvmc']

NAMESPACE_EXCEPTIONS = ['xcb_input_focus_t']


def remove_common_prefix(name, other):
    name_split = name.split('_')
    other_split = other.split('_')
    for i in range(len(name_split)):
        if i >= len(other_split) or other_split[i] != name_split[i]:
            return '_'.join(name_split[i:])


def split_name(name):
    if name.startswith('xcb_'):
        xcb_name = name[len('xcb_'):]
        if name in NAMESPACE_EXCEPTIONS:
            return ('xcb', xcb_name)
        for namespace in NAMESPACES:
            if xcb_name.startswith(namespace + '_'):
                return ('xcb', namespace, xcb_name[len(namespace) + 1:])
        return ('xcb', xcb_name)
    return (name,)


def qname(splitname):
    if isinstance(splitname, str):
        return qname(split_name(splitname))
    return '::'.join(splitname)


class Name(object):

    def __init__(self, full_name):
        self.full = full_name
        self.split = split_name(full_name)
        self.short = self.split[-1]
        self.qualified = qname(self.split)

    def __str__(self):
        return self.full
