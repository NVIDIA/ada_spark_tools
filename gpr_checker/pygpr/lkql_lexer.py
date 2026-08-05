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

from pygpr.errors import Location, Message_Handler
from pygpr.parsing import Token_Base, Lexer_Base

# Language definition taken from
# https://github.com/AdaCore/langkit-query-language/blob/master/lkql/lkql.lkt


class Token(Token_Base):
    KINDS = frozenset([
        "COMMENT",
        "IDENTIFIER",
        "KEYWORD",
        "STRING",       # normal and multi-line
        "INTEGER",
        "DOT",
        "ELLIPSIS",
        "QUESTION_DOT",
        "QUESTION_BRACKET",
        "COMMA",
        "SEMI",
        "COLON",
        "UNDERSCORE",
        "DOUBLE_EX",    # !!
        "EQ",           # =
        "OPERATOR",     # ==, !=, <, <=, >, >=, +, -, *, /, &
        "AT",           # @
        "BAR",          # |
        "L_ARROW",      # <-
        "R_ARROW",      # =>
        "BOX",          # <>
        "BRA", "KET",
        "C_BRA", "C_KET",
        "S_BRA", "S_KET",
    ])

    KEYWORDS = frozenset([
        "and",
        "or",
        "let",
        "select",
        "from",
        "through",
        "when",
        "val",
        "import",
        "selector",
        "match",
        "rec",
        "for",
        "skip",
        "is",
        "in",
        "true",
        "false",
        "if",
        "else",
        "then",
        "not",
        "null",
        "new",
    ])


class LKQL_Lexer(Lexer_Base):
    PUNCTUATION = {
        "." : "DOT",
        "," : "COMMA",
        ";" : "SEMI",
        ":" : "COLON",
        "_" : "UNDERSCORE",
        "@" : "AT",
        "|" : "BAR",
        "(" : "BRA",
        ")" : "KET",
        "{" : "C_BRA",
        "}" : "C_KET",
        "[" : "S_BRA",
        "]" : "S_KET",
        "+" : "OPERATOR",
        "-" : "OPERATOR",
        "*" : "OPERATOR",
        "/" : "OPERATOR",
        "&" : "OPERATOR",
    }

    def token(self):
        while self.nc and self.nc.isspace():
            self.advance()
        self.advance()

        if self.cc is None:
            return None

        start_pos  = self.lexpos
        start_line = self.line_no
        start_col  = self.col_no

        kind = None
        value = None

        loc  = Location(self.filename, start_line, start_col)

        if self.cc == "#":
            kind = "COMMENT"
            while self.nc and self.nc != "\n":
                self.advance()

        elif self.cc.isalpha() and self.cc.isascii():
            kind = "IDENTIFIER"
            while self.nc and self.nc.isascii() and (self.nc.isalpha() or
                                                     self.nc.isdigit() or
                                                     self.nc == "_"):
                self.advance()

        elif self.cc.isdigit():
            kind = "INTEGER"
            while self.nc and self.nc.isdigit():
                self.advance()

        elif self.cc == '"':
            kind = "STRING"
            while self.nc:
                self.advance()
                if self.cc == '\\':
                    self.advance()
                elif self.cc == '"':
                    break

        elif self.cc == "=":
            if self.nc == "=":  # pragma: no cover
                kind = "OPERATOR"
                self.advance()
            elif self.nc == ">":  # pragma: no cover
                kind = "R_ARROW"
                self.advance()
            else:
                kind = "EQ"

        elif self.cc == "!" and self.nc == "!":  # pragma: no cover
            kind = "DOUBLE_EQ"
            self.advance()

        elif self.cc == "." and \
             self.nc == "." and \
             self.nnc == ".":  # pragma: no cover

            kind = "ELLIPSIS"
            self.advance()

        elif self.cc == "?" and self.nc == ".":  # pragma: no cover
            kind = "QUESTION_DOT"
            self.advance()

        elif self.cc == "?" and self.nc == "[":  # pragma: no cover
            kind = "QUESTION_BRACKET"
            self.advance()

        elif self.cc == "<":  # pragma: no cover
            if self.nc == "=":
                kind = "OPERATOR"
                self.advance()
            elif self.nc == "-":
                kind = "L_ARROW"
                self.advance()
            elif self.nc == ">":
                kind = "BOX"
                self.advance()
            else:
                kind = "OPERATOR"

        elif self.cc == ">":  # pragma: no cover
            kind = "OPERATOR"
            if self.nc == "=":
                self.advance()

        elif self.cc in LKQL_Lexer.PUNCTUATION:
            kind = LKQL_Lexer.PUNCTUATION[self.cc]

        else:  # pragma: no cover
            self.mh.error(loc, "unexpected character: %s" % repr(self.cc))

        text = self.content[start_pos:self.lexpos + 1]

        match kind:
            case "COMMENT":
                value = text[1:].strip()
            case "STRING":
                value = text[1:-1]
            case "INTEGER":
                value = int(text, 10)
            case "IDENTIFIER":
                value = text
                if value in Token.KEYWORDS:
                    kind = "KEYWORD"
                    value = value.lower()

        return Token(loc, kind, value)


def sanity_test():
    lexer = LKQL_Lexer(mh       = Message_Handler(),
                       filename = sys.argv[1])
    while True:
        token = lexer.token()
        if token is None:
            return
        print(token)


if __name__ == "__main__":
    sanity_test()
