#!/usr/bin/env python
import os

import texthon
import namespaces
import parse
import ast_util


def generate(header, template):

    class Method(object):

        def __init__(self, name, return_type, call_name):
            self.name = name
            self.return_type = return_type
            self.call_name = call_name

    class Arg(object):

        def __init__(self, name, type):
            assert isinstance(name, str)
            self.name = name
            self.type = type

        def __str__(self):
            return self.type.prefix + self.type.name.qualified + \
                   self.type.suffix + ' ' + self.name

    def struct_needs_wrapper(name):
        return name.endswith('_reply_t')

    def make_ref(type):
        assert struct_needs_wrapper(type.name.full), type.name.full
        assert ast_util.is_simple_type_decl(type.node)
        ref = ast_util.TypeDecl('::xcb::ref< ' + type.name.qualified + ' >')
        ref.base_type = type
        return ref

    def make_list(value_type, length_type):
        assert ast_util.is_simple_type_decl(value_type.node)
        assert ast_util.is_simple_type_decl(length_type.node)
        reference_type = value_type
        if struct_needs_wrapper(value_type.name.full):
            reference_type = make_ref(value_type)
        elif value_type.name.full == 'char':
            return ast_util.TypeDecl('::xcb::string< ' +
                                     length_type.name.qualified + ' >')
        typename = '::xcb::list< {}, {}, {} >'.format(value_type, length_type,
                                                      reference_type)
        return ast_util.TypeDecl(typename)

    def wrap_struct(struct):
        name = namespaces.Name(struct.name)
        methods = {}
        lists = []
        list_methods = []
        for func_name, func in header.functions.items():
            if len(func.args.params) != 1:
                continue
            arg = func.args.params[0]
            if not ast_util.is_pointer_to(arg.type, struct.name):
                continue
            assert ast_util.is_pointer_to_const(arg.type)
            method_name = namespaces.remove_common_prefix(func_name,
                                                          struct.name)
            assert not method_name in methods.keys()
            is_list = (ast_util.is_pointer(func.type) and
                       func_name + '_length' in header.functions.keys())

            if is_list:
                list_methods.append(method_name + '_length')
                list_methods.append(method_name + '_iterator')
                list_methods.append(method_name + '_end')
                length_func = header.functions[func_name + '_length']
                length_type = ast_util.return_type(length_func.type)
                value_type = ast_util.const_return_type(func.type.type)
                list_type = make_list(value_type, length_type)
                lists.append(Method(method_name, list_type, func_name))
            else:
                if (ast_util.is_simple_pointer(func.type) and
                    struct_needs_wrapper(func.type.type.declname)):
                    return_type = make_ref(ast_util.const_return_type(func.type.type))
                else:
                    return_type = ast_util.const_return_type(func.type)
                methods[method_name] = Method(method_name, return_type,
                                              func_name)
        for list_method in list_methods:
            methods.pop(list_method, None)
        fields = []
        for decl in struct.decls:
            assert not decl.name in methods.keys(), decl.name
            fields.append(Method(decl.name,
                                 ast_util.const_return_type(decl.type),
                                 decl.name))
        return template.struct_ref(name, methods, lists, fields)

    def wrap_request(func_name, func):
        return_type = ast_util.return_type(func.type)
        if (return_type.prefix != '' or
            return_type.suffix != '' or
            not return_type.name.short.endswith('_cookie_t') or
            len(func.args.params) < 1):
            return
        first = func.args.params[0]
        if not ast_util.is_pointer_to(first.type, 'xcb_connection_t'):
            return
        original_args = []
        for arg in func.args.params[1:]:
            original_args.append(Arg(arg.name, ast_util.return_type(arg.type)))
        transformed_args = []
        call_args = [arg.name for arg in original_args]
        for i, arg in enumerate(original_args):
            if (arg.name + '_len' in call_args and
                ast_util.is_simple_pointer(arg.type.node)):
                length_idx = call_args.index(arg.name + '_len')
                length_type = original_args[length_idx].type
                value_type = ast_util.return_type(arg.type.node.type)
                transformed_args.remove(original_args[length_idx])
                transformed_args.append(Arg(arg.name, make_list(value_type,
                                                                length_type)))
                call_args[length_idx] = arg.name + '.size()'
                call_args[i] = arg.name + '.data()'
            else:
                transformed_args.append(arg)
        has_reply = (return_type.name.full != 'xcb_void_cookie_t')
        if has_reply and func_name.full.endswith('_unchecked'):
            checked = False
            base_name = namespaces.Name(func_name.full[:-len('_unchecked')])
        elif not has_reply and func_name.full.endswith('_checked'):
            checked = True
            base_name = namespaces.Name(func_name.full[:-len('_checked')])
        else:
            base_name = func_name
            checked = has_reply
        if has_reply:
            reply_func_name = namespaces.Name(base_name.full + '_reply')
            reply_ptr = header.functions[reply_func_name.full].type
            assert ast_util.is_simple_pointer(reply_ptr)
            reply_t = make_ref(ast_util.return_type(reply_ptr.type))
        else:
            reply_func_name = None
            reply_t = None
        return template.request(func_name, transformed_args, call_args,
                                checked, return_type, reply_t, reply_func_name)

    root = namespaces.CxxRoot()
    xcb_namespace = root.path(['xcb'])

    for name in header.typedefs:
        root.path(name.split[:-1]).content.append(template.typedef(name))

    for name, struct in header.structs.items():
        if struct_needs_wrapper(name):
            xcb_namespace.content.append(wrap_struct(struct))

    for full_name, func in header.functions.items():
        name = namespaces.Name(full_name)
        wrapper = wrap_request(name, func)
        if wrapper:
            root.path(name.split[:-1]).content.append(wrapper)

    return template.header(header, root, parse.NAME_FIXES)


def process_command_line():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('xcb_header')
    parser.add_argument('--ast', action='store_true')
    return parser.parse_args()


def main():
    args = process_command_line()
    header = parse.parse_file(args.xcb_header)

    if args.ast:
        for node in header.nodes:
            node.show(attrnames=True, nodenames=True)
        return

    engine = texthon.Engine()
    basedir = os.path.dirname(__file__)
    template = engine.load_file(os.path.join(basedir, 'template.h'),
                                texthon.parser.Parser(directive_token='//'))
    engine.make()
    with open(header.file_name + 'pp', 'w') as file:
        file.write(generate(header, engine.modules[template.path]))


if __name__ == '__main__':
    main()
