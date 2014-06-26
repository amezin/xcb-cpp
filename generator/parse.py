import os

import pycparser
import ast_util
import namespaces

NAME_FIXES = {
    'explicit': '_explicit',
    'class': '_class',
    'template': '_template'
}


def preprocess(header_file, cpp_path='cpp'):
    gnu_extensions = {
        '__attribute__(x)': '',
        '__extension__': '',
        '__inline__': '',
        '__inline': '',
        '__restrict': '',
        '__const': ''
    }

    xcb_typedefs = '''
# 0 ""
typedef struct xcb_query_extension_reply_t xcb_query_extension_reply_t;
typedef struct xcb_setup_t xcb_setup_t;
'''

    cpp_args = ['-E']
    for key, value in (gnu_extensions.items() | NAME_FIXES.items()):
        cpp_args.append('-D' + key + '=' + value)

    return xcb_typedefs + \
        pycparser.preprocess_file(header_file, cpp_path, cpp_args)


def parse(source, file_name):
    cparser = pycparser.CParser()
    ast = cparser.parse(source, file_name)

    ast_util.setup_parent(ast)
    items = []
    for item in ast.ext:
        if item.coord.file == file_name:
            items.append(item)
    return items


class Header(object):

    class Builder(pycparser.c_ast.NodeVisitor):

        def __init__(self, header):
            super(Header.Builder, self).__init__()
            self._header = header

        def visit_Decl(self, node):
            if isinstance(node.type, pycparser.c_ast.FuncDecl):
                self._header.functions[node.name] = node.type
            elif isinstance(node.type, pycparser.c_ast.TypeDecl):
                self._header.variables[node.name] = node.type

        def visit_Struct(self, node):
            self._header.structs[node.name] = node

        def visit_Enum(self, node):
            self._header.enums[node.name] = node

        def visit_Union(self, node):
            self._header.unions[node.name] = node

        def visit_TypeDecl(self, node):
            self._header.typedefs.append(namespaces.Name(node.declname))
            self.generic_visit(node)

    def __init__(self, preprocessed_content, file_name):
        self.path = file_name
        self.file_name = os.path.basename(file_name)
        self.typedefs = []
        self.functions = {}
        self.structs = {}
        self.enums = {}
        self.unions = {}
        self.variables = {}
        self.nodes = parse(preprocessed_content, file_name)
        visitor = Header.Builder(self)
        for node in self.nodes:
            visitor.visit(node)


def parse_file(file_name, cpp_path='cpp'):
    return Header(preprocess(file_name, cpp_path), file_name)
