# Copyright 2025 Claudionor N. Coelho Jr

import re
from pycparser import c_ast

native_types = ['char', 'int', 'short', 'long', 'long long', 'double', 'float', 'void']

class ConstEval(c_ast.NodeVisitor):
    def __init__(self):
        self.values = {}

    def visit_Constant(self, node):
        if node.type == 'int':
            return int(node.value)
        elif node.type == 'float':
            return float(node.value)
        elif node.type == 'char':
            return ord(node.value.strip("'"))
        else:
            raise ValueError(f"Unsupported constant type: {node.type}")

    def visit_ID(self, node):
        # Assuming identifiers are constants with pre-defined values for this example
        return self.values.get(node.name, 0)

    def visit_BinaryOp(self, node):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)
        op = node.op
        if op == '+':
            return left_val + right_val
        elif op == '-':
            return left_val - right_val
        elif op == '*':
            return left_val * right_val
        elif op == '/':
            return left_val / right_val
        elif op == '%':
            return left_val % right_val
        elif op == '<<':
            return left_val << right_val
        elif op == '>>':
            return left_val >> right_val
        elif op == '|':
            return left_val | right_val
        elif op == '&':
            return left_val & right_val
        elif op == '^':
            return left_val ^ right_val
        elif op == '&&':
            return int(bool(left_val) and bool(right_val))
        elif op == '||':
            return int(bool(left_val) or bool(right_val))
        else:
            raise ValueError(f"Unsupported binary operator: {op}")

    def visit_UnaryOp(self, node):
        operand_val = self.visit(node.expr)
        op = node.op
        if op == '+':
            return +operand_val
        elif op == '-':
            return -operand_val
        elif op == '~':
            return ~operand_val
        elif op == '!':
            return int(not operand_val)
        else:
            raise ValueError(f"Unsupported unary operator: {op}")

    def visit_Paren(self, node):
        return self.visit(node.expr)

    def evaluate(self, node):
        return self.visit(node)


def get_type_name(typ, new_types, user_defined_types):
    '''
        Extracts type name of a type. Type in C needs to have a prefix and a suffix.

        :param typ: Type of variable.
        :param new_types: types that are defined in typedef.
        :param user_defined_types: set of user defined types that need to be created.
        :return: prefix and suffix of type name.
    '''
    qualifiers = []
    if isinstance(typ, c_ast.Typedef):
        prefix, suffix = get_type_name(typ.type.type, new_types, user_defined_types)
        return f'typedef {prefix} {typ.name}', suffix
    if isinstance(typ, c_ast.TypeDecl):
        if isinstance(typ.quals, list):
            qualifiers.extend(typ.quals)
            type_name, suffix = get_type_name(typ.type, new_types, user_defined_types)
        return ' '.join(qualifiers) + ' ' + type_name if qualifiers else type_name, suffix
    elif isinstance(typ, c_ast.PtrDecl):
        if isinstance(typ.quals, list):
            qualifiers.extend(typ.quals)
        type_name, suffix = get_type_name(typ.type, new_types, user_defined_types)
        type_name += ' *'
        return ' '.join(qualifiers) + ' ' + type_name if qualifiers else type_name, suffix
    elif isinstance(typ, c_ast.ArrayDecl):
        evaluator = ConstEval()
        value = 0
        if typ.dim:
            value = evaluator.evaluate(typ.dim)
        size = f'[{value}]' if typ.dim else '[]'
        prefix, suffix = get_type_name(typ.type, new_types, user_defined_types)
        return prefix, size + suffix 
    elif isinstance(typ, c_ast.Typedef):
        return typ.name, ''
    elif isinstance(typ, c_ast.Struct):
        type_name = f'struct {typ.name}'
        user_defined_types.add(type_name)
        return type_name, ''
    elif isinstance(typ, c_ast.Union):
        type_name = f'union {typ.name}'
        user_defined_types.add(type_name)
        return type_name, ''
    elif isinstance(typ, c_ast.Enum):
        type_name = f'enum {typ.name}'
        user_defined_types.add(type_name)
        return type_name, ''
    elif isinstance(typ, c_ast.FuncDecl):
        prefix, suffix = get_type_name(typ.type, new_types, user_defined_types)
        return prefix, f'({suffix})'
    elif isinstance(typ, c_ast.IdentifierType):
        name = ' '.join(typ.names)
        if name not in native_types:
            new_types.add(' '.join(typ.names))
        return name, ''
    return 'unknown', ''

def get_external_declarations_node(node, new_types, user_defined_types, obj_name_list=[]):
    '''
        Get declarations of objects to be put in 'extern' module in C.

        :param node: Node of ast.
        :param new_types: new user defined types, probably typedefs.
        :param user_defined_types: set of user types that need to be defined.
        :param obj_name_list: object names to extract types.

        :return: extern type definition.
    '''
    if isinstance(node, c_ast.FuncDef):
        #    isinstance(node.type, c_ast.FuncDecl) and 
        if (
            not obj_name_list or node.decl.name in obj_name_list
        ):
            func_prefix, func_suffix = get_type_name(node.decl.type.type, new_types, user_defined_types)
            if isinstance(func_suffix, type(None)): func_suffix = ''
            if func_suffix:
                func_prefix = f'({func_prefix}){func_suffix}'
            param_types = []
            if node.param_decls:
                param_decls = node.param_decls
            else:
                param_decls = node.decl.type.args
            for param in param_decls: #node.type.args.params:
                prefix, suffix = get_type_name(param.type, new_types, user_defined_types)
                if suffix:
                    param_type = f'({prefix}){suffix}'
                else:
                    param_type = prefix
                param_types.append(param_type)
            param_list = ', '.join(param_types)
            func_name = node.decl.name
            if func_prefix[-1] != '*': func_prefix += ' '
            return f'extern {func_prefix}{func_name}({param_list});'
    elif isinstance(node, c_ast.Decl) and not isinstance(node.type, c_ast.FuncDecl):
        name = node.name if node.name else node.type.name
        if not obj_name_list or name in obj_name_list:
            prefix, suffix = get_type_name(node.type, new_types, user_defined_types)
            if isinstance(suffix, type(None)): suffix = ''
            if prefix[-1] != '*': prefix += ' '
            decl_name = node.name
            if isinstance(decl_name, type(None)):
                return f'extern {prefix}{suffix};'
            else:
                return f'extern {prefix}{decl_name}{suffix.strip()};'
    elif isinstance(node, c_ast.Typedef):
        if not obj_name_list or node.name in obj_name_list:
            prefix, suffix = get_type_name(node.type, new_types, user_defined_types)
            if isinstance(suffix, type(None)): suffix = ''
            if prefix[-1] != '*': prefix += ' '
            return f'typedef {prefix}{node.name}{suffix};'
    return ""


def get_external_declarations(ast, obj_name_list):
    '''
        Gets external declarations of all ast.ext objects if they match obj_name_list.

        :param ast: ast of file.
        :param obj_name_list: names of functions.

        :return: list of extern function declarations
    '''
    user_defined_types = []
    func_decl = []
    while True:
        new_user_defined_types = set()
        new_types = set()
        new_decl = []
        for i, typ in enumerate(ast.ext):
            #for child_name, child in node.children():
            decl = get_external_declarations_node(typ, new_types, new_user_defined_types, obj_name_list)
            if decl: new_decl.append(decl)
        func_decl = new_decl + func_decl
        new_user_defined_types = list(set(new_user_defined_types).difference(user_defined_types))
        user_defined_types = list(new_user_defined_types) + user_defined_types
        if not new_types:
            break
        obj_name_list = list(new_types)

    for n in user_defined_types:
        print(n)
    user_defined_types = ['extern ' + n + ';' for n in user_defined_types]

    return user_defined_types + func_decl


def get_includes(f):
    all_includes = []
    with open(f, 'r') as file:
        include_regex = r'#include\s*(<.*?>)|#include\s*(".*?")'
        source = file.read()
        includes = re.findall(include_regex, source)
        for left, right in includes:
            if left and left not in all_includes: all_includes.append(left)
            if right and right not in all_includes: all_includes.append(right)

        return ['#include ' + n for n in all_includes]


def get_extern_refs(ast, filename, obj_name_list=[]):
    if isinstance(obj_name_list, tuple):
        obj_name_list = list(obj_name_list)

    if not isinstance(obj_name_list, list):
        obj_name_list = [obj_name_list]

    all_includes = [] #get_includes(filename)
    func_decl = get_external_declarations(ast, obj_name_list=obj_name_list)

    if func_decl:
        all_refs = all_includes + func_decl
    else:
        all_refs = []

    refs = '\n'.join(['    ' + n for n in all_refs])
    return refs

