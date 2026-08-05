#!/usr/bin/env python3
#############################################################################
# GPR Checker
# SPDX-FileCopyrightText: Copyright (C) 2025-2026 NVIDIA CORPORATION &
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

import sys

from pygpr.errors import Error, Message_Handler, Location
from pygpr.lkql_lexer import Token, LKQL_Lexer
from pygpr.parser import Parser_Base
from pygpr import lkql_ast as ast


class LKQL_Parser(Parser_Base):
    def __init__(self, mh, filename):
        assert isinstance(mh, Message_Handler)
        assert isinstance(filename, str)
        super().__init__(mh          = mh,
                         lexer       = LKQL_Lexer(mh, filename),
                         token_kinds = Token.KINDS,
                         keywords    = Token.KEYWORDS)

        self.contains_rules = False
        self.stab = ast.Symbol_Table()

    def parse_compilation_unit(self):
        decls = []
        while self.nt:
            n_stmt = self.parse_value_declaration()
            if n_stmt.name == "rules":
                self.contains_rules = True
            decls.append(n_stmt)
        self.match_eof()
        if not self.contains_rules:
            self.mh.error(Location(self.lexer.filename),
                          "rule file does not contain 'rules' value")
        return decls

    def parse_value_declaration(self):
        self.match_kw("val")
        self.match("IDENTIFIER")
        t_name = self.ct
        self.match("EQ")
        n_value = self.parse_expr()
        return ast.Value_Declaration(t_name, n_value)

    def parse_expr(self):
        if self.peek("AT"):
            return self.parse_object_literal(at = True)
        elif self.peek("C_BRA"):
            return self.parse_object_literal(at = False)
        elif self.peek("S_BRA"):
            return self.parse_list_literal()
        elif self.peek("BRA"):
            return self.parse_tuple_literal()
        elif self.peek("STRING"):
            return self.parse_string_literal()
        elif self.peek("INTEGER"):
            return self.parse_integer_literal()
        elif self.peek_kw("true") or self.peek_kw("false"):
            return self.parse_boolean_literal()
        else:
            self.mh.error(self.nt.location,
                          "expected object, list, tuple or string;"
                          " found %s instead" % self.nt.kind)

    def parse_object_literal(self, at):
        assert isinstance(at, bool)
        if at:
            self.match("AT")
            default_allowed = True
        else:
            default_allowed = False
        self.match("C_BRA")
        rv = ast.Object_Literal(self.ct.location,
                                default_allowed)

        if not self.peek("C_KET"):
            while True:
                n_key = self.parse_object_key()
                if not at or self.peek("COLON"):
                    self.match("COLON")
                    n_val = self.parse_expr()
                else:
                    n_val = None
                n_member = ast.Object_Member(n_key, n_val)
                rv.values.register(self.mh, n_member)

                if self.peek("C_KET"):
                    break
                else:
                    self.match("COMMA")

        self.match("C_KET")

        return rv

    def parse_object_key(self):
        self.match("IDENTIFIER")
        return ast.Object_Key(self.ct.location, self.ct.value)

    def parse_list_literal(self):
        self.match("S_BRA")
        rv = ast.List_Literal(self.ct.location)

        if not self.peek("S_KET"):
            while True:
                rv.values.append(self.parse_expr())
                if self.peek("S_KET"):
                    break
                else:
                    self.match("COMMA")

        self.match("S_KET")
        return rv

    def parse_tuple_literal(self):
        self.match("BRA")
        rv = ast.Tuple_Literal(self.ct.location)

        if not self.peek("KET"):
            while True:
                rv.values.append(self.parse_expr())
                if self.peek("KET"):
                    break
                else:
                    self.match("COMMA")

        self.match("KET")
        return rv

    def parse_string_literal(self):
        self.match("STRING")
        return ast.String_Literal(self.ct)

    def parse_integer_literal(self):
        self.match("INTEGER")
        return ast.Integer_Literal(self.ct)

    def parse_boolean_literal(self):
        if self.peek_kw("true"):
            self.match_kw("true")
        else:
            self.match_kw("false")
        return ast.Boolean_Literal(self.ct)


def sanity_test():
    parser = LKQL_Parser(Message_Handler(), sys.argv[1])

    try:
        for decl in parser.parse_compilation_unit():
            decl.dump()
    except Error:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(sanity_test())
