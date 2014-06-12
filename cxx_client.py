#!/usr/bin/env python

import string

indentation_step = "    "

def format_cxx_node(node, indentation=''):
    if isinstance(node, str):
        return "{i}{n}\n".format(i=indentation, n=node)
    return node.format(indentation)

class CxxNamespace(object):
    def __init__(self, name):
        self.name = name
        self.children = []

    def childNamespace(self, name):
        for child in self.children:
            if isinstance(child, CxxNamespace) and child.name == name:
                return child

        new = CxxNamespace(name)
        self.children.append(new)
        return new

    def path(self, path):
        if len(path) == 0:
            return self

        return self.childNamespace(path[0]).path(path[1:])

    def format(self, indentation=''):
        if self.children == []:
            return ""
        inner = [format_cxx_node(child, indentation) for child in self.children]
        return "{i}namespace {n}\n{i}{{\n\n{inner}{i}}}\n\n".format(i=indentation,
                                                                    n=self.name,
                                                                    inner="".join(inner))

class CxxLabel(object):
    def __init__(self, name):
        self.name = name

    def format(self, indentation=''):
        if indentation.endswith(indentation_step):
            indentation = indentation[:-len(indentation_step)]
        return "{i}{n}:\n".format(i=indentation, n=self.name)

class CxxClass(object):
    def __init__(self, name):
        self.name = name
        self.short_name = name.split('<', 1)[0]
        self.public = []
        self.protected = []
        self.private = []
        self.base = None
        self.keyword = 'class'

    def format(self, indentation=''):
        children = []
        if self.public != []:
            children += [CxxLabel("public")] + self.public
        if self.protected != []:
            children += [CxxLabel("protected")] + self.protected
        if self.private != []:
            children += [CxxLabel("private")] + self.private

        inner = [format_cxx_node(child, indentation + indentation_step) for child in children]
        base = (" : " + self.base) if self.base else ''

        return "{i}{k} {n}{b}\n{i}{{\n{inner}{i}}};\n\n".format(i=indentation,
                                                                k=self.keyword,
                                                                n=self.name,
                                                                b=base,
                                                                inner="".join(inner))

class CxxFunction(object):
    def __init__(self, signature):
        self.signature = signature
        self.body = []
        self.initializers = []

    def format(self, indentation=''):
        inner = [format_cxx_node(child, indentation + indentation_step) for child in self.body]
        extra = ''
        if self.initializers != []:
            initializer_indentation = indentation + indentation_step
            extra = "{i}: {v}\n".format(i=initializer_indentation,
                                        v=",\n{}  ".format(initializer_indentation).join(self.initializers))
        return "{i}inline {s}\n{e}{i}{{\n{inner}{i}}}\n\n".format(i=indentation,
                                                                  s=self.signature,
                                                                  inner="".join(inner),
                                                                  e=extra)

class CxxTemplate(object):
    def __init__(self, wrapped, args=''):
        self.args = args
        self.wrapped = wrapped

    def format(self, indentation=''):
        return "{i}template<{a}>\n{inner}".format(i=indentation,
                                                  a=self.args,
                                                  inner=format_cxx_node(self.wrapped, indentation))

std_ns = CxxNamespace("std")
xcb_ns = CxxNamespace("xcb")
cxx_root = [std_ns, xcb_ns]

fixes = {"explicit" : "_explicit",
         "class"    : "_class",
         "template" : "_template"}

def fix_name(name):
    if name in fixes.keys():
        return fixes[name]
    return name

def cxx_name(name):
    name = name[len("xcb_"):]
    prefix = c_client._ext(module.namespace.ext_name).lower()
    if prefix != "" and name.startswith(prefix):
        return "{}::{}".format(prefix, name[len(prefix)+1:])
    return name

def cxx_iterator(self):
    traits = CxxClass("iterator_traits<{}>".format(self.c_iterator_type))
    traits.keyword = "struct"
    traits.public = ["typedef ptrdiff_t difference_type;",
                     "typedef {} value_type;".format(self.c_type),
                     "typedef {} *pointer;".format(self.c_type),
                     "typedef {} &reference;".format(self.c_type),
                     "typedef forward_iterator_tag iterator_category;"]
    std_ns.children.append(CxxTemplate(traits))

    end_func = CxxFunction("{0} end(const {0} &self)".format(self.c_iterator_type))
    end_func.body = ["xcb_generic_iterator_t temp({}(self));".format(self.c_end_name),
                     "return *reinterpret_cast<{} *>(&temp);".format(self.c_iterator_type)]
    xcb_ns.children.append(end_func)

    pre_increment = CxxFunction("{0} &operator ++({0} &self)".format(self.c_iterator_type))
    pre_increment.body = ["{}(&self);".format(self.c_next_name), "return self;"]
    cxx_root.append(pre_increment)

    post_increment = CxxFunction("{0} operator ++({0} &self, int)".format(self.c_iterator_type))
    post_increment.body = ["{} copy(self);".format(self.c_iterator_type),
                           "{}(&self);".format(self.c_next_name),
                           "return copy;"]
    cxx_root.append(post_increment)

    star = CxxFunction("{} &operator *(const {} &self)".format(self.c_type,
                                                               self.c_iterator_type))
    star.body = ["return *self.data;"];
    cxx_root.append(star)

    equals = CxxFunction("bool operator ==(const {0} &a, const {0} &b)".format(self.c_iterator_type))
    equals.body = ["return a.data == b.data;"];
    cxx_root.append(equals)

    not_equals = CxxFunction("bool operator !=(const {0} &a, const {0} &b)".format(self.c_iterator_type))
    not_equals.body = ["return !(a == b);"];
    cxx_root.append(not_equals)

def cxx_when_cookie_valid(body, invalidate=True):
    block = ["if (cookie_.sequence) {"]
    block += [(indentation_step + line) for line in body]
    if invalidate:
        block += [indentation_step + "cookie_.sequence = 0;"]
    block += ["}"]
    return block

def cxx_request_wrapper(class_name, cookie_type="xcb_void_cookie_t"):
    wrapper = CxxClass(class_name)

    wrapper.private = ["{0}(const {0} &);".format(wrapper.short_name),
                       "{0} &operator =(const {0} &);\n".format(wrapper.short_name),
                       "xcb_connection_t *connection_;",
                       "{} cookie_;".format(cookie_type)]

    wrapper.cookie_ctor = CxxFunction("{}({} cookie, xcb_connection_t *connection)".format(wrapper.short_name,
                                                                                           cookie_type))
    wrapper.cookie_ctor.initializers = ["connection_(connection)",
                                        "cookie_(cookie)"]
    wrapper.public.append(wrapper.cookie_ctor)

    wrapper.dtor = CxxFunction("~{}()".format(wrapper.short_name))
    wrapper.dtor.body = cxx_when_cookie_valid(["xcb_discard_reply(connection_, cookie_.sequence);"], False)
    wrapper.public.append(wrapper.dtor)

    wrapper.swap_func = CxxFunction("void swap({} &rhs)".format(wrapper.name))
    wrapper.swap_func.body = ["std::swap(connection_, rhs.connection_);",
                              "std::swap(cookie_, rhs.cookie_);"]
    wrapper.public.append(wrapper.swap_func)

    connection_func = CxxFunction("xcb_connection_t *connection() const")
    connection_func.body = ["return connection_;"]
    wrapper.public.append(connection_func)

    return wrapper

def cxx_request_checked(wrapper):
    wrapper.error_func = CxxFunction("const xcb_generic_error_t *error()")
    wrapper.public.append(wrapper.error_func)

    take_error_func = CxxFunction("xcb_generic_error_t *take_error()")
    take_error_func.body = ["error();",
                            "xcb_generic_error_t *ptr = error_;",
                            "error_ = NULL;",
                            "return ptr;"]
    wrapper.public.append(take_error_func)
    
    wrapper.private.append("xcb_generic_error_t *error_;")
    wrapper.cookie_ctor.initializers.append("error_(NULL)")
    if hasattr(wrapper, 'args_ctor'):
        wrapper.args_ctor.initializers.append("error_(NULL)")
    wrapper.dtor.body.append("std::free(error_);")
    wrapper.swap_func.body.append("std::swap(error_, rhs.error_);")
    if wrapper.error_func.body != []:
        return wrapper

    wrapper.error_func.body = cxx_when_cookie_valid(["error_ = xcb_request_check(connection_, cookie_);"])
    wrapper.error_func.body.append("return error_;")

def cxx_args_ctor(type, wrapper, call_name):
    arg_names = []
    args = []

    for arg in type.fields:
        if arg.visible:
            arg_names.append(fix_name(arg.c_field_name))
            args.append("{} {}{}".format(arg.c_field_const_type,
                                         arg.c_pointer.strip(),
                                         fix_name(arg.c_field_name)))
    extra_comma = ", " if args != [] else ""

    wrapper.args_ctor = CxxFunction("{}({}xcb_connection_t *connection)".format(wrapper.short_name,
                                                                                ", ".join(args) + extra_comma))
    wrapper.cookie_init = "{}(connection{})".format(call_name,
                                                    extra_comma + ", ".join(arg_names))
    wrapper.public.append(wrapper.args_ctor)

def cxx_reply(type, checked=True):
    call_name = type.c_request_name if checked else type.c_unchecked_name
    q_name = cxx_name(call_name)
    name_parts = q_name.split("::", 2)
    if len(name_parts) > 1:
        ns = name_parts[0]
        class_name = name_parts[1]
    else:
        ns = ""
        class_name = q_name

    wrapper = cxx_request_wrapper(class_name, type.c_cookie_type)

    cxx_args_ctor(type, wrapper, type.c_request_name if checked else type.c_unchecked_name)
    wrapper.args_ctor.initializers = ["connection_(connection)",
                                      "cookie_({})".format(wrapper.cookie_init)]

    reply_func = CxxFunction("const {} *reply()".format(type.c_reply_type))
    get_reply = "{}(connection_, cookie_, {});".format(type.c_reply_name,
                                                       "&error_" if checked else "NULL")
    reply_func.body = cxx_when_cookie_valid(["reply_ = " + get_reply])
    reply_func.body.append("return reply_;")
    wrapper.public.append(reply_func)

    take_reply_func = CxxFunction("{} *take_reply()".format(type.c_reply_type))
    take_reply_func.body = ["reply();",
                            "{} *ptr = reply_;".format(type.c_reply_type),
                            "reply_ = NULL;",
                            "return ptr;"]
    wrapper.public.append(take_reply_func)

    deref_op = CxxFunction("const {} &operator *()".format(type.c_reply_type))
    deref_op.body = ["return *reply();"]
    wrapper.public.append(deref_op)

    access_op = CxxFunction("const {} *operator ->()".format(type.c_reply_type))
    access_op.body = ["return reply();"]
    wrapper.public.append(access_op)

    wrapper.private.append("{} *reply_;".format(type.c_reply_type))
    wrapper.cookie_ctor.initializers.append("reply_(NULL)")
    if hasattr(wrapper, 'args_ctor'):
        wrapper.args_ctor.initializers.append("reply_(NULL)")
    wrapper.dtor.body.append("std::free(reply_);")
    wrapper.swap_func.body.append("std::swap(reply_, rhs.reply_);")

    if checked:
        cxx_request_checked(wrapper)
        wrapper.error_func.body = ["reply();", "return error_;"]

    xcb_ns.path([ns]).children.append(wrapper)

import c_client

def cxx_open(self):
    c_client._ns = self.namespace

def cxx_close(self):
    with open(args.output, 'w') as header:
        header.write("#pragma once\n\n")
        header.write("#include <cstdlib>\n")
        header.write("#include <algorithm>\n\n")

        xcb_header = "xcb" if self == None else self.namespace.header

        if xcb_header != "xcb":
            header.write("#include \"xcb.hpp\"\n\n")
            header.write("extern \"C\"\n{\n")
            for problem in fixes.keys():
                header.write("#define {} {}\n".format(problem, fixes[problem]))

        header.write("#include <xcb/{}.h>\n".format(xcb_header))

        if xcb_header != "xcb":
            for problem in fixes.keys():
                header.write("#undef {}\n".format(problem))
            header.write("}\n")

        header.write("\n")

        for item in cxx_root:
            header.write(format_cxx_node(item))

def cxx_simple(self, name):
    c_client._c_type_setup(self, name, ())
    if self.name != name:
        cxx_iterator(self)

def cxx_enum(self, name):
    pass

def cxx_struct(self, name):
    c_client._c_type_setup(self, name, ())
    cxx_iterator(self)

def cxx_union(self, name):
    c_client._c_type_setup(self, name, ())
    cxx_iterator(self)

def cxx_request(self, name):
    c_client._c_type_setup(self, name, ())

    if self.reply:
        cxx_reply(self)
        cxx_reply(self, False)
    else:
        wrapper = CxxClass(self.c_checked_name[len("xcb_"):])
        wrapper.base = "public future_error"
        cxx_args_ctor(self, wrapper, self.c_checked_name)
        wrapper.args_ctor.initializers = ["{}({}, connection)".format("future_error",
                                                                      wrapper.cookie_init)]
        xcb_ns.children.append(wrapper)

def cxx_event(self, name):
    c_client._c_type_setup(self, name, ('event',))

def cxx_error(self, name):
    c_client._c_type_setup(self, name, ('error',))

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--xml')
parser.add_argument('output')
args = parser.parse_args()

output = {'open'    : cxx_open,
          'close'   : cxx_close,
          'simple'  : cxx_simple,
          'enum'    : cxx_enum,
          'struct'  : cxx_struct,
          'union'   : cxx_union,
          'request' : cxx_request,
          'event'   : cxx_event,
          'error'   : cxx_error,
          }

if args.xml:
    from xcbgen.state import Module
    from xcbgen.xtypes import *

    module = Module(args.xml, output)
    c_client.module = module
    module.register()
    module.resolve()
    module.generate()
else:
    future_error = cxx_request_wrapper("future_error", "xcb_void_cookie_t")
    cxx_request_checked(future_error)
    xcb_ns.children.append(future_error)
    std_ns.children.append(CxxTemplate("struct iterator_traits;\n",
                                       "typename Iterator"))
    cxx_close(None)
