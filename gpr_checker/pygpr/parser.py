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

from pygpr.errors import Message_Handler
from pygpr.lexer import Token, GPR_Lexer
from pygpr.parsing import Parser_Base
from pygpr import ast


class GPR_Parser(Parser_Base):
    def __init__(self, mh, stab, filename, externals):
        assert isinstance(mh, Message_Handler)
        assert isinstance(stab, ast.Symbol_Table)
        assert isinstance(filename, str)
        assert isinstance(externals, dict)
        super().__init__(mh          = mh,
                         lexer       = GPR_Lexer(mh, filename),
                         token_kinds = Token.KINDS,
                         keywords    = Token.KEYWORDS)

        self.stab      = stab
        self.project   = None
        self.package   = None
        self.externals = externals

        self.dependencies         = []
        self.limited_dependencies = []

    def parse_name(self):
        self.match("IDENTIFIER")
        tokens = [self.ct]
        while self.peek("DOT") and len(tokens) < 3:
            self.match("DOT")
            self.match("IDENTIFIER")
            tokens.append(self.ct)
        return ast.Unresolved_Reference(tokens)

    def parse_gpr(self):
        # Process file pragmas
        skip_project_reason = None
        while True:
            if self.peek("PRAGMA_SKIP_FILE"):
                self.match("PRAGMA_SKIP_FILE")
                if skip_project_reason:
                    self.mh.warning(self.ct.location,
                                    "duplicate skip file pragma")
                skip_project_reason = self.ct.value

            else:
                break

        self.parse_project_declaration(skip_project_reason)
        self.match_eof()

        scope = ast.Scope(self.stab)
        self.project.execute(self.mh, scope)
        assert len(scope.scopes) == 1

    def parse_context_clause(self):
        assert self.project is None
        while self.peek_kw("limited") or self.peek_kw("with"):
            self.parse_with_clause()

    def parse_with_clause(self):
        if self.peek_kw("limited"):
            self.match_kw("limited")
            dep_list = self.limited_dependencies
        else:
            dep_list = self.dependencies

        self.match_kw("with")
        self.match("STRING")
        dep_list.append(self.ct)
        while self.peek("COMMA"):
            self.match("COMMA")
            self.match("STRING")
            dep_list.append(self.ct)
        self.match("SEMICOLON")

    def parse_project_declaration(self, skip_project_reason):
        assert self.project is None
        assert isinstance(skip_project_reason, str) or \
            skip_project_reason is None

        # qualifier
        qualifiers = {
            "abstract"      : False,
            "aggregate"     : False,
            "library"       : False,
            "configuration" : False
        }

        if self.peek_kw("abstract"):
            self.match_kw("abstract")
            qualifiers["abstract"] = True
        elif self.peek("IDENTIFIER"):
            self.match("IDENTIFIER")
            if self.ct.value not in qualifiers:
                self.mh.error(self.ct.location,
                              "unknown project qualifier %s" % self.ct.value)
            qualifiers[self.ct.value] = True
            if self.peek("IDENTIFIER"):
                self.match("IDENTIFIER")
                if self.ct.value not in qualifiers:
                    self.mh.error(self.ct.location,
                                  "unknown project qualifier %s" %
                                  self.ct.value)
                qualifiers[self.ct.value] = True

        self.match_kw("project")
        self.match("IDENTIFIER")
        self.project = ast.Project(self.ct, qualifiers, skip_project_reason)
        self.stab.register(self.mh, self.project)

        if self.peek_kw("extends"):
            self.match_kw("extends")
            if self.peek_kw("all"):
                self.match_kw("all")
                self.project.all_extension = True
            self.match("IDENTIFIER")
            self.project.set_parent(self.stab.lookup(self.mh, self.ct))

        self.match_kw("is")

        self.parse_declarative_items(self.project)

        self.match_kw("end")
        self.match("IDENTIFIER")
        if self.project.name != self.ct.value:
            self.mh.error(self.ct.location,
                          "end token mismatch, should be %s" %
                          self.project.name)
        self.match("SEMICOLON")

    def parse_declarative_items(self, n_project):
        assert isinstance(n_project, ast.Project)

        while not self.peek_kw("end"):
            if self.peek_simple_declarative_item():
                n_stmt = self.parse_simple_declarative_item(n_project)
                n_project.statements.add(n_stmt)

            elif self.peek_kw("type"):
                n_stmt = self.parse_enumeration_declaration(n_project)

            else:
                self.parse_package_declaration()

    def peek_simple_declarative_item(self):
        return (self.peek("IDENTIFIER") or
                self.peek_kw("for") or
                self.peek_kw("case") or
                self.peek_kw("null"))

    def parse_simple_declarative_item(self, n_region):
        assert isinstance(n_region, ast.Defining_Region)

        if self.peek("IDENTIFIER"):
            self.match("IDENTIFIER")
            t_def = self.ct
            if self.peek("COLON"):
                self.match("COLON")
                n_typ = self.parse_name().resolve_as_type(self.mh,
                                                          self.stab,
                                                          self.project.symbols)
                if not isinstance(n_typ, ast.Enumeration):
                    # The only types supported are enums, so if we get
                    # anything else here it's a serious issue
                    self.mh.ice_loc(self.ct.location,
                                    "%s (%s) is not an enumeration" %
                                    (n_typ.name,
                                     n_typ.__class__.__name__))
            else:
                n_typ = None
            self.match("ASSIGN")
            n_expr = self.parse_expression(n_typ)
            self.match("SEMICOLON")
            n_var = ast.Variable(t_def, n_expr)
            return ast.Variable_Declaration(n_var)

        elif self.peek_kw("for"):
            # attribute_declaration
            return self.parse_attribute_declaration(n_region)

        elif self.peek_kw("case"):
            return self.parse_case_construction(n_region)

        else:
            # empty_declaration
            self.match_kw("null")
            t_loc = self.ct
            self.match("SEMICOLON")
            return ast.Null_Statement(t_loc.location)

    def parse_case_construction(self, n_region):
        assert isinstance(n_region, ast.Defining_Region)
        self.match_kw("case")
        n_var_ref = self.parse_name()
        n_case_stmt = ast.Case_Statement(n_var_ref)

        self.match_kw("is")
        while self.peek_kw("when"):
            self.match_kw("when")
            error_loc = self.ct.location
            if self.peek_kw("others"):
                self.match_kw("others")
                conditions = set()
            else:
                self.match("STRING")
                conditions = set([self.ct])
                while self.peek("BAR"):
                    self.match("BAR")
                    self.match("STRING")
                    conditions.add(self.ct)
            n_action = ast.Case_Action(error_loc, conditions, n_region)
            self.match("ARROW")

            while self.peek_simple_declarative_item():
                n_stmt = self.parse_simple_declarative_item(n_region)
                n_action.statements.add(n_stmt)

            n_case_stmt.add_action(self.mh, n_action)

        self.match_kw("end")
        self.match_kw("case")
        self.match("SEMICOLON")

        return n_case_stmt

    def parse_attribute_declaration(self, n_region):
        assert isinstance(n_region, ast.Defining_Region)

        self.match_kw("for")
        self.match("IDENTIFIER")
        t_def = self.ct

        if self.peek("BRA"):
            self.match("BRA")
            if self.peek_kw("others"):
                self.match_kw("others")
            else:
                self.match("STRING")
            t_index = self.ct
            self.match("KET")
        else:
            t_index = None

        self.match_kw("use")
        n_expr = self.parse_expression()
        self.match("SEMICOLON")

        return ast.Attribute_Assignment(t_def, t_index, n_expr)

    def parse_expression(self, expected_type=None):
        assert isinstance(expected_type, ast.Type) or expected_type is None

        n_lhs = self.parse_term(expected_type)
        while self.peek("CONCATENATION") and expected_type is None:
            self.match("CONCATENATION")
            t_op = self.ct
            n_rhs = self.parse_term(expected_type)
            n_lhs = ast.String_List_Concatenation(t_op, n_lhs, n_rhs)

        return n_lhs

    def parse_term(self, expected_type=None):
        assert isinstance(expected_type, ast.Type) or expected_type is None

        if self.peek("STRING"):
            self.match("STRING")
            if isinstance(expected_type, ast.Enumeration):
                # TODO: validate
                n_typ = expected_type
            else:
                n_typ = ast.Builtin_String()
            return ast.String_Literal(self.ct, n_typ)

        elif self.peek("IDENTIFIER"):
            return self.parse_name()

        elif self.peek_kw("external"):
            self.match_kw("external")
            self.match("BRA")
            self.match("STRING")
            t_var = self.ct
            if self.peek("COMMA"):
                self.match("COMMA")
                self.match("STRING")
                default = self.ct.value
            else:
                default = None
            self.match("KET")

            if t_var.value in self.externals:
                value = self.externals[t_var.value]
            elif default is not None:
                self.mh.info(t_var.location,
                             "using default value '%s' for external %s" %
                             (default, t_var.value))
                value = default
            else:
                self.mh.error(t_var.location,
                              "external environment does not define %s" %
                              t_var.value)

            # pylint: disable=possibly-used-before-assignment
            return ast.External(location = t_var.location,
                                variable = t_var.value,
                                value    = value,
                                default  = default)

        elif self.peek("BRA"):
            self.match("BRA")
            rv = ast.String_List_Aggregate(self.ct)
            if not self.peek("KET"):
                while True:
                    rv.add_item(self.parse_term())
                    if self.peek("COMMA"):
                        self.match("COMMA")
                    else:
                        break
            self.match("KET")
            return rv

        else:
            self.mh.error(self.ct.location,
                          "expected string, reference or brackets")

    def parse_package_declaration(self):
        self.match_kw("package")
        self.match("IDENTIFIER")
        self.package = ast.Package(self.ct)
        n_decl = ast.Package_Declaration(self.package)
        self.project.statements.add(n_decl)

        if self.peek_kw("renames"):
            self.match_kw("renames")
            self.match("IDENTIFIER")
            n_other_proj = self.stab.lookup(self.mh, self.ct)
            self.match("DOT")
            self.match("IDENTIFIER")
            n_other_pkg = n_other_proj.symbols.lookup(self.mh, self.ct)
            self.match("SEMICOLON")
            self.package.set_parent(n_other_pkg)
            # TODO: Correct renaming semantics
            n_pkg = self.package
            self.package = None
            return n_pkg

        if self.peek_kw("extends"):
            self.match_kw("extends")
            self.match("IDENTIFIER")
            n_other_proj = self.stab.lookup(self.mh, self.ct)
            self.match("DOT")
            self.match("IDENTIFIER")
            n_other_pkg = n_other_proj.symbols.lookup(self.mh, self.ct)
            # TODO: Correct renaming/extension semantics
            self.package.set_parent(n_other_pkg)

        self.match_kw("is")
        while not self.peek_kw("end"):
            n_stmt = self.parse_simple_declarative_item(self.package)
            self.package.statements.add(n_stmt)
        self.match_kw("end")
        self.match("IDENTIFIER")
        if self.package.name != self.ct.value:
            self.mh.error(self.ct.location,
                          "end token mismatch, should be %s" %
                          self.package.name)
        self.match("SEMICOLON")
        self.package = None

    def parse_enumeration_declaration(self, n_project):
        assert isinstance(n_project, ast.Project)

        self.match_kw("type")
        self.match("IDENTIFIER")
        n_enum = ast.Enumeration(self.ct)
        n_project.symbols.register(self.mh, n_enum)
        self.match_kw("is")
        self.match("BRA")

        self.match("STRING")
        n_enum.add_literal(self.mh, self.ct)
        while not self.peek("KET"):
            self.match("COMMA")
            self.match("STRING")
            n_enum.add_literal(self.mh, self.ct)
        self.match("KET")
        self.match("SEMICOLON")

        return ast.Enumeration_Declaration(n_enum)
