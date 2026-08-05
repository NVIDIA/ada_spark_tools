#!/usr/bin/env python3
#############################################################################
# GPR Checker
# SPDX-FileCopyrightText: Copyright (C) 2024-2026 NVIDIA CORPORATION &
#                         AFFILIATES. All rights reserved.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of the GPR Checker.
#
# GPR Checker is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GPR Checker is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GPR Checker. If not, see <https://www.gnu.org/licenses/>.
#############################################################################

from abc import ABCMeta, abstractmethod
from copy import copy

from pygpr.errors import Message_Handler, ICE, Location
from pygpr.lexer import Token


class Scope:
    def __init__(self, n_global):
        assert isinstance(n_global, Symbol_Table)
        self.scopes = [n_global]

    def push(self, n_table):
        assert isinstance(n_table, Symbol_Table)
        self.scopes.append(n_table)
        assert len(self.scopes) <= 3

    def pop(self):
        assert len(self.scopes) >= 2
        del self.scopes[-1]

    def contains_raw(self, name):
        assert isinstance(name, str)
        for n_table in reversed(self.scopes):
            if n_table.contains_raw(name):
                return True
        return False

    def contains(self, t_id):  # pragma: no cover
        # Currently not used
        assert isinstance(t_id, Token) and t_id.kind == "IDENTIFIER"
        for n_table in reversed(self.scopes):
            if n_table.contains(t_id):
                return True
        return False

    def lookup(self, mh, t_id):
        assert isinstance(mh, Message_Handler)
        assert isinstance(t_id, Token) and t_id.kind == "IDENTIFIER"
        for n_table in reversed(self.scopes[1:]):
            if n_table.contains(t_id):
                return n_table.lookup(mh, t_id)
        return self.scopes[0].lookup(mh, t_id)

    def register(self, mh, n_entity):
        assert isinstance(mh, Message_Handler)
        assert isinstance(n_entity, Entity)
        if self.contains_raw(n_entity.name) and \
           not self.scopes[-1].contains_raw(n_entity.name):
            mh.warning(n_entity.location,
                       "shadows definition from enclosing scope")
        self.scopes[-1].register(mh, n_entity)


class Dumpable(metaclass=ABCMeta):
    @abstractmethod
    def dump(self, indent=0):
        pass

    def write_header(self, indent, extra=None):
        if extra is None:
            self.write_indent(indent, self.__class__.__name__)
        else:
            self.write_indent(indent, "%s (%s)" % (self.__class__.__name__,
                                                   extra))

    @classmethod
    def write_indent(cls, indent, line):
        assert isinstance(indent, int) and indent >= 0
        assert isinstance(line, str)
        print(" " * (indent * 3) + line)


class Symbol_Table(Dumpable):
    def __init__(self, parent=None, case_sensitive=True):
        assert isinstance(parent, Symbol_Table) or parent is None
        assert isinstance(case_sensitive, bool)
        self.parent         = parent
        self.symbols        = {}
        self.case_sensitive = case_sensitive

    def dump(self, indent=0):
        if not self.symbols:
            return
        self.write_header(indent)
        for n_ent in self.symbols.values():
            n_ent.dump(indent + 1)

    def canonical_name_raw(self, s):
        assert isinstance(s, str)
        return s if self.case_sensitive else s.lower()

    def canonical_name(self, entity):
        assert isinstance(entity, Entity)
        return self.canonical_name_raw(entity.name)

    def register(self, mh, entity):
        assert isinstance(mh, Message_Handler)
        assert isinstance(entity, Entity)
        cname = self.canonical_name(entity)
        if cname in self.symbols:
            mh.error(entity.location,
                     "%s is already defined at %s" %
                     (entity.name,
                      self.symbols[cname].location))
        self.symbols[cname] = entity

    def lookup(self, mh, t_ident):
        assert isinstance(mh, Message_Handler)
        assert isinstance(t_ident, Token) and t_ident.kind == "IDENTIFIER"
        cname = self.canonical_name_raw(t_ident.value)
        if cname in self.symbols:
            return self.symbols[cname]
        elif self.parent is not None:
            return self.parent.lookup(mh, t_ident)
        else:
            mh.error(t_ident.location,
                     "unknown symbol %s" % t_ident.value)

    def lookup_raw_assuming(self, name):
        assert self.contains_raw(name)
        cname = self.canonical_name_raw(name)
        if cname in self.symbols:
            return self.symbols[cname]
        elif self.parent is not None:
            return self.parent.lookup_raw_assuming(name)
        else:
            assert False

    def contains(self, t_ident):
        assert isinstance(t_ident, Token) and t_ident.kind == "IDENTIFIER"
        return self.contains_raw(t_ident.value)

    def contains_raw(self, name):
        assert isinstance(name, str)
        if self.canonical_name_raw(name) in self.symbols:
            return True
        elif self.parent is not None:
            return self.parent.contains_raw(name)
        else:
            return False

    def set_parent(self, parent):
        assert isinstance(parent, Symbol_Table)
        assert self.parent is None
        self.parent = parent

    def serialise(self):
        return [entity.serialise()
                for entity in self.symbols.values()]


class Node(Dumpable, metaclass=ABCMeta):
    def __init__(self, location):
        assert isinstance(location, Location)
        self.location = location


class Statement(Node, metaclass=ABCMeta):
    @abstractmethod
    def execute(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)


class Package_Declaration(Statement):
    def __init__(self, n_package):
        super().__init__(n_package.location)
        self.n_package = n_package

    def dump(self, indent=0):
        self.write_header(indent)
        self.n_package.dump(indent + 1)

    def execute(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        scope.register(mh, self.n_package)
        scope.push(self.n_package.symbols)
        self.n_package.statements.execute(mh, scope)
        scope.pop()


class Variable_Declaration(Statement):
    def __init__(self, n_var):
        assert isinstance(n_var, Variable)
        super().__init__(n_var.location)
        self.n_var = n_var

    def dump(self, indent=0):
        self.write_header(indent)
        self.n_var.dump(indent + 1)

    def execute(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        self.n_var.resolve_symbols(mh, scope)
        self.n_var.set_concrete_value()
        top_scope = scope.scopes[-1]
        if not top_scope.contains_raw(self.n_var.name):
            scope.register(mh, self.n_var)


class Enumeration_Declaration(Statement):
    def __init__(self, n_typ):
        assert isinstance(n_typ, Enumeration)
        super().__init__(n_typ.location)
        self.n_typ = n_typ

    def dump(self, indent=0):
        self.write_header(indent)
        self.n_typ.dump(indent + 1)

    def execute(self, mh, scope):  # pragma: no cover
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        # Nothing to do since enum type we register immediately


class Attribute_Assignment(Statement):
    def __init__(self, t_attribute, t_index, n_value):
        assert isinstance(t_attribute, Token) and \
            t_attribute.kind == "IDENTIFIER"
        assert (isinstance(t_index, Token) and
                t_index.kind in ("KEYWORD", "STRING")) \
            or t_index is None
        assert isinstance(n_value, Expression)
        super().__init__(t_attribute.location)
        self.t_attribute = t_attribute
        self.t_index     = t_index
        self.n_value     = n_value

    def dump(self, indent=0):
        if self.t_index is None:
            self.write_header(indent, "%s" % self.t_attribute.value)
        else:
            self.write_header(indent, "%s (%s)" % (self.t_attribute.value,
                                                   self.t_index.value))
        self.n_value.dump(indent + 1)

    def execute(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)

        top_scope = scope.scopes[-1]

        self.n_value = self.n_value.resolve_symbols(mh, scope)
        if self.t_index is None:
            if top_scope.contains(self.t_attribute):
                n_attr = scope.lookup(mh, self.t_attribute)
                n_attr.n_value = self.n_value
            else:
                n_attr = Simple_Attribute(self.t_attribute,
                                          self.n_value)
                scope.register(mh, n_attr)
            n_attr.set_concrete_value()
        else:
            # TODO: Can you have a map attribute shadow? If so this
            # would put it in the wrong place.
            if top_scope.contains(self.t_attribute):
                n_attr = scope.lookup(mh, self.t_attribute)
            else:
                n_attr = Map_Attribute(self.t_attribute,
                                       self.n_value.n_typ)
                scope.register(mh, n_attr)
            if self.t_index.kind == "STRING":
                n_attr.n_value[self.t_index.value] = self.n_value
                n_attr.set_concrete_value(self.t_index.value)
            else:
                assert self.t_index.kind == "KEYWORD" and \
                    self.t_index.value == "others"
                n_attr.n_default = self.n_value
                n_attr.set_concrete_value(None)


class Case_Statement(Statement):
    def __init__(self, n_var):
        assert isinstance(n_var, Unresolved_Reference)
        super().__init__(n_var.location)
        self.n_var   = n_var
        self.actions = []
        self.default = None

    def dump(self, indent=0):
        self.write_header(indent, str(self.n_var))
        for n_action in self.actions:
            n_action.dump(indent + 1)
        if self.default is not None:
            self.default.dump(indent + 1)

    def add_action(self, mh, n_action):
        assert isinstance(mh, Message_Handler)
        assert isinstance(n_action, Case_Action)
        if len(n_action.conditions) >= 1:
            self.actions.append(n_action)
        elif self.default is None:
            self.default = n_action
        else:
            mh.error(n_action.location,
                     "duplicate others choice")

    def execute(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        self.n_var = self.n_var.resolve_symbols(mh, scope)
        assert isinstance(self.n_var, Reference)
        choice = self.n_var.target.concrete_value

        for n_action in self.actions:
            if n_action.matches(choice):
                n_action.execute(mh, scope)
                return

        if self.default is not None:
            self.default.execute(mh, scope)


class Case_Action(Statement):
    def __init__(self, location, conditions, enclosing_region):
        assert isinstance(conditions, set)
        assert all(isinstance(condition, Token) and condition.kind == "STRING"
                   for condition in conditions)
        super().__init__(location)
        self.conditions = conditions
        self.statements = Statement_List(enclosing_region)

    def dump(self, indent=0):
        self.write_header(indent, " | ".join(token.value
                                             for token in self.conditions))
        self.statements.dump(indent + 1)

    def matches(self, choice):
        assert isinstance(choice, str)
        for t_con in self.conditions:
            if t_con.value == choice:
                return True
        return False

    def execute(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        self.statements.execute(mh, scope)


class Null_Statement(Statement):
    def dump(self, indent=0):
        self.write_header(indent)

    def execute(self, mh, scope):  # pragma: no cover
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)


class Statement_List(Node):
    def __init__(self, enclosing_region):
        assert isinstance(enclosing_region, Defining_Region)
        super().__init__(enclosing_region.location)
        self.n_region   = enclosing_region
        self.statements = []

    def dump(self, indent=0):
        self.write_header(indent)
        for n_statement in self.statements:
            n_statement.dump(indent + 1)

    def add(self, n_statement):
        assert isinstance(n_statement, Statement)
        self.statements.append(n_statement)

    def execute(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        for n_statement in self.statements:
            n_statement.execute(mh, scope)


class Entity(Node):
    def __init__(self, location, name):
        assert isinstance(name, str)
        super().__init__(location)
        self.name = name

    def dump(self, indent=0):
        self.write_header(indent, self.name)


class Defining_Region(Entity):
    def __init__(self, t_def):
        assert isinstance(t_def, Token) and t_def.kind == "IDENTIFIER"
        super().__init__(t_def.location, t_def.value)

        self.parent     = None
        self.symbols    = Symbol_Table()
        self.statements = Statement_List(self)

    def set_parent(self, parent):
        assert isinstance(parent, self.__class__)
        assert self.parent is None
        self.parent = parent
        self.symbols.set_parent(parent.symbols)

    def dump(self, indent=0):
        super().dump(indent)
        self.statements.dump(indent + 1)
        self.symbols.dump(indent + 1)

    def execute(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        scope.push(self.symbols)
        self.statements.execute(mh, scope)
        scope.pop()

    def serialise(self):
        return {
            "kind"       : self.__class__.__name__,
            "name"       : self.name,
            "attributes" : {
                name: value.serialise()
                for name, value in self.symbols.symbols.items()
                if isinstance(value, (Simple_Attribute,
                                      Map_Attribute))
            }
        }

    def has_attribute(self, name):
        assert isinstance(name, str)
        return self.symbols.contains_raw(name)

    def get_attribute(self, name):
        assert self.has_attribute(name)
        return self.symbols.lookup_raw_assuming(name)


class Project(Defining_Region):
    def __init__(self, t_def, qualifiers, skip_reason=None):
        assert isinstance(qualifiers, dict)
        assert isinstance(skip_reason, str) or skip_reason is None
        super().__init__(t_def)

        self.qualifiers    = qualifiers
        self.all_extension = False
        self.skip_reason   = skip_reason

    def serialise(self):
        rv = super().serialise()
        rv["packages"] = {
            name: value.serialise()
            for name, value in self.symbols.symbols.items()
            if isinstance(value, Package)
        }
        return rv


class Package(Defining_Region):
    pass


class Type(Entity):
    pass


class String_Type(Type):
    pass


class Builtin_String(String_Type):
    def __init__(self):
        super().__init__(Location("<builtin>"),
                         "String")


class Enumeration(String_Type):
    def __init__(self, t_def):
        assert isinstance(t_def, Token) and t_def.kind == "IDENTIFIER"
        super().__init__(t_def.location, t_def.value)
        self.literals = {}

    def add_literal(self, mh, t_def):
        assert isinstance(mh, Message_Handler)
        assert isinstance(t_def, Token) and t_def.kind == "STRING"
        if t_def.value in self.literals:
            mh.error(t_def.location,
                     "duplicate literal definition of %s in %s" %
                     (t_def.value, self.name))
        self.literals[t_def.value] = t_def.location

    def dump(self, indent=0):
        super().dump()
        for literal in sorted(self.literals):
            self.write_indent(indent + 1, "Literal: %s" % literal)


# --- Currently unused ---
#
# class Map_Type(Type):
#     def __init__(self):
#         super().__init__(Location("<builtin>"),
#                          "Map")


class List_Type(Type):
    def __init__(self):
        super().__init__(Location("<builtin>"),
                         "String_List")


class Unresolved_Type(Type):
    def __init__(self):
        super().__init__(Location("<builtin>"),
                         "Unresolved_Type")


class Typed_Entity(Entity):
    def __init__(self, t_def, n_typ):
        assert isinstance(t_def, Token) and t_def.kind == "IDENTIFIER"
        assert isinstance(n_typ, Type)
        super().__init__(t_def.location, t_def.value)
        self.n_typ = n_typ

    def dump(self, indent=0):
        super().dump(indent)
        self.write_indent(indent + 1, "Type: %s" % self.n_typ.name)


class Simple_Attribute(Typed_Entity):
    def __init__(self, t_def, n_value):
        assert isinstance(n_value, Expression)
        super().__init__(t_def, n_value.n_typ)
        self.n_value        = n_value
        self.concrete_value = None

    def dump(self, indent=0):
        super().dump(indent)
        self.write_indent(indent + 1, "Value: %s" % self.n_value)
        if self.concrete_value is not None:
            self.write_indent(indent + 1, "Concrete: %s" %
                              repr(self.concrete_value))

    def set_concrete_value(self):
        self.concrete_value = self.n_value.evaluate()

    def serialise(self):
        return self.concrete_value


class Map_Attribute(Typed_Entity):
    def __init__(self, t_def, n_typ):
        assert isinstance(n_typ, Type)
        super().__init__(t_def, n_typ)
        self.n_value   = {}
        self.n_default = None

        self.concrete_value   = {}
        self.concrete_default = None

    def dump(self, indent=0):
        super().dump(indent)
        if self.n_default is not None:
            self.write_indent(indent + 1, "<others>: %s" % self.n_default)
        for name, value in self.n_value.items():
            self.write_indent(indent + 1, "%s: %s" % (name, value))
            if name in self.concrete_value:
                self.write_indent(indent + 1, "Concrete %s: %s" %
                                  (name, repr(self.concrete_value[name])))

    def set_concrete_value(self, index):
        assert isinstance(index, str) or \
            (index is None and
             isinstance(self.n_default, Expression))
        if index is None:
            # pylint: disable=no-member
            # False alarm from pylint
            self.concrete_default = self.n_default.evaluate()
        else:
            self.concrete_value[index] = self.n_value[index].evaluate()

    def serialise(self):
        rv = copy(self.concrete_value)
        if self.concrete_default is not None:
            rv["others"] = self.concrete_default
        return rv

    def get_value(self, index):
        if index in self.n_value:
            return self.n_value[index], self.concrete_value[index]
        elif self.n_default is not None:  # pragma: no cover
            # Will be needed in the future if we support more map features
            return self.n_default, self.concrete_default
        else:
            return None, None


class Variable(Typed_Entity):
    def __init__(self, t_def, n_value):
        assert isinstance(n_value, Expression)
        super().__init__(t_def, n_value.n_typ)
        self.n_value        = n_value
        self.concrete_value = None

    def evaluate(self):
        return self.n_value.evaluate()

    def dump(self, indent=0):
        super().dump(indent)
        self.write_indent(indent + 1, "Value: %s" % self.n_value)
        if self.concrete_value is not None:
            self.write_indent(indent + 1, "Concrete: %s" %
                              repr(self.concrete_value))

    def resolve_symbols(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        self.n_value = self.n_value.resolve_symbols(mh, scope)
        return self

    def set_concrete_value(self):
        self.concrete_value = self.n_value.evaluate()


class Expression(Node, metaclass=ABCMeta):
    def __init__(self, location, n_typ):
        assert isinstance(n_typ, Type)
        super().__init__(location)
        self.n_typ = n_typ

    def dump(self, indent=0):
        self.write_header(indent, str(self))

    @abstractmethod
    def evaluate(self):
        pass

    def resolve_symbols(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        return self


class Unresolved_Reference(Expression):
    def __init__(self, tokens):
        assert isinstance(tokens, list)
        assert all(isinstance(token, Token) and token.kind == "IDENTIFIER"
                   for token in tokens)
        super().__init__(tokens[-1].location, Unresolved_Type())
        self.tokens = tokens

    def __str__(self):
        return ".".join(token.value for token in self.tokens)

    def dump(self, indent=0):
        self.write_header(indent, str(self))

    def evaluate(self):
        raise ICE(self.location,
                  "attempting to evaluate unresolved reference %s" %
                  str(self))

    def resolve_symbols(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)

        if len(self.tokens) == 1:
            n_sym = scope.lookup(mh, self.tokens[0])

        else:
            raise ICE(self.location,
                      "references with %u elements NIY" % len(self.tokens))

        return Reference(self.location, n_sym)

    def resolve_as_type(self, mh, st_global, st_project):
        assert isinstance(mh, Message_Handler)
        assert isinstance(st_global, Symbol_Table)
        assert isinstance(st_project, Symbol_Table)

        if len(self.tokens) == 1:
            return st_project.lookup(mh, self.tokens[0])

        elif len(self.tokens) == 2:
            st_project = st_global.lookup(mh, self.tokens[0]).symbols
            return st_project.lookup(mh, self.tokens[1])

        else:
            mh.error(self.tokens[-1].location,
                     "cannot resolve type reference with %u components" %
                     len(self.tokens))


class Reference(Expression):
    def __init__(self, location, n_ent):
        assert isinstance(n_ent, Typed_Entity)
        super().__init__(location, n_ent.n_typ)
        self.target = n_ent

    def __str__(self):
        return self.target.name

    def evaluate(self):
        if isinstance(self.target, Variable):
            return self.target.evaluate()
        else:
            raise ICE(self.location,
                      "evaluation of %s (%s) not supported yet" %
                      (self.target.name,
                       self.target.__class__.__name__))


class External(Expression):
    def __init__(self, location, variable, value, default=None):
        assert isinstance(variable, str)
        assert isinstance(value, str)
        assert isinstance(default, str) or default is None
        super().__init__(location, Builtin_String())
        self.variable = variable
        self.value    = value
        self.default  = default

    def __str__(self):
        if self.default is not None:
            return 'external("%s", "%s")' % (self.variable, self.default)
        else:
            return 'external("%s")' % self.variable

    def evaluate(self):
        return self.value


class String_Literal(Expression):
    def __init__(self, t_lit, n_typ):
        assert isinstance(t_lit, Token) and t_lit.kind == "STRING"
        super().__init__(t_lit.location, n_typ)
        self.string_value = t_lit.value

    def __str__(self):
        return '"' + self.string_value.replace('"', '""') + '"'

    def evaluate(self):
        return self.string_value


class String_List_Aggregate(Expression):
    def __init__(self, t_def):
        assert isinstance(t_def, Token) and t_def.kind == "BRA"
        super().__init__(t_def.location, List_Type())
        self.items = []

    def add_item(self, n_item):
        assert isinstance(n_item, Expression)
        self.items.append(n_item)

    def __str__(self):
        return "(" + ", ".join(map(str, self.items)) + ")"

    def evaluate(self):
        return [item.evaluate() for item in self.items]

    def resolve_symbols(self, mh, scope):
        assert isinstance(mh, Message_Handler)
        assert isinstance(scope, Scope)
        new_items = [item.resolve_symbols(mh, scope)
                     for item in self.items]
        self.items = new_items
        return self


class String_List_Concatenation(Expression):
    def __init__(self, t_op, n_lhs, n_rhs):
        assert isinstance(t_op, Token) and t_op.kind == "CONCATENATION"
        assert isinstance(n_lhs, Expression)
        assert isinstance(n_rhs, Expression)
        super().__init__(t_op.location, Unresolved_Type())

        self.n_lhs = n_lhs
        self.n_rhs = n_rhs

    def __str__(self):
        return str(self.n_lhs) + " & " + str(self.n_rhs)

    def evaluate(self):
        lhs = self.n_lhs.evaluate()
        rhs = self.n_rhs.evaluate()
        return lhs + rhs

    def resolve_symbols(self, mh, scope):
        assert isinstance(scope, Scope)
        self.n_lhs = self.n_lhs.resolve_symbols(mh, scope)
        self.n_rhs = self.n_rhs.resolve_symbols(mh, scope)
        if isinstance(self.n_lhs.n_typ, String_Type) and \
           isinstance(self.n_rhs.n_typ, String_Type):
            self.n_typ = Builtin_String()
        else:
            self.n_typ = List_Type()
        return self

    def dump(self, indent=0):
        super().dump()
        self.write_indent(indent + 1,
                          "Type: %s" %
                          "%s & %s" % (
                              ("STRING"
                               if isinstance(self.n_lhs.n_typ, String_Type)
                               else "LIST"),
                              ("STRING"
                               if isinstance(self.n_rhs.n_typ, String_Type)
                               else "LIST")))
        self.n_lhs.dump(indent + 1)
        self.n_rhs.dump(indent + 1)
