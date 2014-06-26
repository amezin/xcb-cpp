'''Helpers for working with pycparser AST'''

import pycparser
import pycparser.c_ast
import pycparser.c_generator

import namespaces


def to_string(ast):
    '''Generate C code for AST node'''
    return pycparser.c_generator.CGenerator().visit(ast)


class ParentRefBuilder(pycparser.c_ast.NodeVisitor):

    def generic_visit(self, node):
        # pylint: disable=unused-variable
        for child_name, child in node.children():
            child.parent = node
        super(ParentRefBuilder, self).generic_visit(node)


def setup_parent(node):
    '''Add 'parent' attribute to all children nodes'''
    ParentRefBuilder().visit(node)


class TypeDecl(object):

    def __init__(self, name):
        if isinstance(name, namespaces.Name):
            self.name = name
        else:
            self.name = namespaces.Name(name)
        self.prefix = ''
        self.suffix = ''
        self.node = None

    def __str__(self):
        return self.prefix + str(self.name) + self.suffix


class ReturnTypeGenerator(pycparser.c_ast.NodeVisitor):

    def generic_visit(self, node):
        assert False, 'Unexpected node type ' + type(node).__name__

    # pylint: disable=invalid-name,no-self-use
    def visit_IdentifierType(self, node):
        assert len(node.names) == 1
        return TypeDecl(namespaces.Name(node.names[0]))

    def visit_TypeDecl(self, node):  # pylint: disable=invalid-name
        decl = self.visit(node.type)
        decl.prefix += (' '.join(node.quals) + ' ' if node.quals else '')
        return decl

    def visit_Decl(self, node):  # pylint: disable=invalid-name
        return self.visit_TypeDecl(node)

    def visit_PtrDecl(self, node):  # pylint: disable=invalid-name
        decl = self.visit(node.type)
        decl.suffix = ' *' + \
        (' ' + ' '.join(node.quals) if getattr(node, 'quals', None) else '') \
        + decl.suffix
        return decl

    def visit_ArrayDecl(self, node):  # pylint: disable=invalid-name
        return self.visit_PtrDecl(node)


def return_type(node):
    result = ReturnTypeGenerator().visit(node)
    result.node = node
    return result

def is_simple_type_decl(type):
    return (isinstance(type, pycparser.c_ast.TypeDecl) and
            isinstance(type.type, pycparser.c_ast.IdentifierType))

def simple_type_equals(type, name):
    return (is_simple_type_decl(type)
            and type.quals == []
            and type.type.names == [name])

def is_pointer(type):
    return (isinstance(type, pycparser.c_ast.PtrDecl) or
            isinstance(type, pycparser.c_ast.ArrayDecl))

def is_simple_pointer(type):
    return is_pointer(type) and is_simple_type_decl(type.type)

def is_pointer_to(type, expect):
    return is_simple_pointer(type) and type.type.type.names == [str(expect)]

def is_const(type):
    return 'const' in getattr(type, 'quals', [])

def is_pointer_to_const(type):
    return is_pointer(type) and is_const(type.type)

def const_return_type(decl):
    type = return_type(decl)
    if is_pointer(decl) and not is_pointer_to_const(decl):
        type.prefix += 'const '
    return type

