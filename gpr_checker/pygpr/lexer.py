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

import sys

from pygpr.errors import Error, Location, Message_Handler
from pygpr.parsing import Token_Base, Lexer_Base


class Token(Token_Base):
    KINDS = frozenset([
        "COMMENT",
        "IDENTIFIER",
        "KEYWORD",
        "STRING",
        "ASSIGN",
        "ARROW",
        "CONCATENATION",
        "BAR",
        "BRA",
        "KET",
        "SEMICOLON",
        "COMMA",
        "COLON",
        "DOT",
        "PRAGMA_SKIP_FILE",
    ])

    KEYWORDS = frozenset([
        "abstract",
        "all",
        "at",
        "case",
        "end",
        "extends",
        "external",
        "external_as_list",
        "for",
        "is",
        "limited",
        "null",
        "others",
        "package",
        "project",
        "renames",
        "type",
        "use",
        "when",
        "with",
    ])


class GPR_Lexer(Lexer_Base):
    PUNCTUATION = {
        ";" : "SEMICOLON",
        "(" : "BRA",
        ")" : "KET",
        "," : "COMMA",
        "." : "DOT",
        "&" : "CONCATENATION",
        ":" : "COLON",
        "|" : "BAR",
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

        if self.cc == "-" and self.nc == "-":
            kind = "COMMENT"
            while self.nc and self.nc != "\n":
                self.advance()

        elif self.cc.isalpha() and self.cc.isascii():
            kind = "IDENTIFIER"
            while self.nc and self.nc.isascii() and (self.nc.isalpha() or
                                                     self.nc.isdigit() or
                                                     self.nc == "_"):
                self.advance()

        elif self.cc == '"':
            kind = "STRING"
            while self.nc:
                self.advance()
                if self.cc == '"' and self.nc == '"':
                    self.advance()
                elif self.cc == '"':
                    break
            if self.cc != '"':
                self.mh.error(loc, "broken string")

        elif self.cc == ":" and self.nc == "=":
            kind = "ASSIGN"
            self.advance()

        elif self.cc == "=" and self.nc == ">":
            kind = "ARROW"
            self.advance()

        elif self.cc in GPR_Lexer.PUNCTUATION:
            kind = GPR_Lexer.PUNCTUATION[self.cc]

        else:
            self.mh.error(loc, "unexpected character: %s" % repr(self.cc))

        text = self.content[start_pos:self.lexpos + 1]

        if kind == "COMMENT":
            value = text[2:].strip()

            # Comments could also be pragmas, so we need to find them
            # here
            if value.startswith("gpr_checker:"):
                value = value.split(":", 1)[1].strip()
                if value.startswith("skip file"):
                    if ":" not in value:
                        self.mh.error(loc,
                                      "malformed skip file pragma:"
                                      " missing explanation")
                    _, value = (item.strip()
                                for item in value.split(":", 1))
                    kind = "PRAGMA_SKIP_FILE"

                else:
                    self.mh.error(loc,
                                  "unknown pragma: %s" % value)

        elif kind == "STRING":
            value = text[1:-1].replace('""', '"')

        elif kind == "IDENTIFIER":
            value = text
            if value.lower() in Token.KEYWORDS:
                kind = "KEYWORD"
                value = value.lower()

        return Token(loc, kind, value)


class ADC_Token(Token_Base):
    KINDS = frozenset([
        "COMMENT",
        "IDENTIFIER", "KEYWORD",
        "NUMBER",
        "STRING",
        "ARROW",
        "DOT",
        "BRA",
        "KET",
        "SEMICOLON",
        "COMMA",
    ])

    KEYWORDS = frozenset([
        "pragma",
    ])

    def to_string(self):
        if self.kind in ("IDENTIFIER", "KEYWORD"):
            return self.value
        elif self.kind == "STRING":
            return '"' + self.value.replace('"', '""') + '"'
        elif self.kind == "NUMBER":
            return self.value
        elif self.kind == "BRA":
            return "("
        elif self.kind == "KET":
            return ")"
        elif self.kind == "DOT":
            return "."
        elif self.kind == "SEMICOLON":  # pragma: no cover We
            # currently use this to check if parameters of two pragmas
            # are the same (and they can't contain semicolons)
            return ";"
        elif self.kind == "COMMA":
            return ","
        elif self.kind == "ARROW":
            return "=>"
        else:
            assert False, "unexpected token kind %s" % self.kind


class ADC_Lexer(Lexer_Base):
    PUNCTUATION = {
        "(" : "BRA",
        ")" : "KET",
        ";" : "SEMICOLON",
        "," : "COMMA",
        "." : "DOT",
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

        if self.cc == "-" and self.nc == "-":
            kind = "COMMENT"
            while self.nc and self.nc != "\n":
                self.advance()

        elif self.cc.isalpha() and self.cc.isascii():
            kind = "IDENTIFIER"
            while self.nc and self.nc.isascii() and (self.nc.isalpha() or
                                                     self.nc.isdigit() or
                                                     self.nc == "_"):
                self.advance()

        elif self.cc.isnumeric() and self.cc.isascii():
            kind = "NUMBER"
            period_count = 0
            while self.nc:
                if self.nc.isnumeric() and self.nc.isascii():
                    pass
                elif self.nc == "_":
                    if self.cc == "_":
                        self.mh.error(Location(self.filename,
                                               self.line_no,
                                               self.col_no + 1),
                                      "two consecutive underscores are"
                                      " not permitted")
                elif self.nc == ".":
                    period_count += 1
                    if period_count > 1:
                        self.mh.error(Location(self.filename,
                                               self.line_no,
                                               self.col_no + 1),
                                      "only a single decimal separator"
                                      " is permitted")
                else:
                    break
                self.advance()

        elif self.cc == '"':
            kind = "STRING"
            while self.nc:
                self.advance()
                if self.cc == '"' and self.nc == '"':
                    self.advance()
                elif self.cc == '"':
                    break
            if self.cc != '"':
                self.mh.error(loc, "broken string")

        elif self.cc == "=" and self.nc == ">":
            kind = "ARROW"
            self.advance()

        elif self.cc in ADC_Lexer.PUNCTUATION:
            kind = ADC_Lexer.PUNCTUATION[self.cc]

        else:
            self.mh.error(loc, "unexpected character: %s" % repr(self.cc))

        text = self.content[start_pos:self.lexpos + 1]

        if kind == "COMMENT":
            value = text[2:].strip()
        elif kind == "NUMBER":
            value = text
        elif kind == "STRING":
            value = text[1:-1].replace('""', '"')
        elif kind == "IDENTIFIER":
            value = text
            if value.lower() in ADC_Token.KEYWORDS:
                kind = "KEYWORD"
                value = value.lower()

        return ADC_Token(loc, kind, value)


def sanity_test():
    mh = Message_Handler()
    if sys.argv[1].endswith(".gpr"):
        lexer = GPR_Lexer(mh, sys.argv[1])
    else:
        lexer = ADC_Lexer(mh, sys.argv[1])
    try:
        while t := lexer.token():
            print(t)
    except Error:
        pass


if __name__ == "__main__":
    sanity_test()
