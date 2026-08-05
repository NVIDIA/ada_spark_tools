#!/usr/bin/env python3
#############################################################################
# GPR Checker
# SPDX-FileCopyrightText: Copyright (C) 2026 NVIDIA CORPORATION &
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

from pygpr.errors import Location, Message_Handler


class Token_Base(metaclass=ABCMeta):
    KINDS = frozenset()

    def __init__(self, location, kind, value=None):
        assert isinstance(location, Location)
        assert kind in self.KINDS, "%s is not a valid %s kind" % \
            (kind, self.__class__.__name__)

        self.location = location
        self.kind     = kind
        self.value    = value

    def __repr__(self):
        if self.value is None:
            return "%s(%s)" % (self.__class__.__name__,
                               self.kind)
        else:
            return "%s(%s, %s)" % (self.__class__.__name__,
                                   self.kind,
                                   repr(self.value))


class Lexer_Base(metaclass=ABCMeta):
    def __init__(self, mh, filename, content=None, encoding="UTF-8"):
        assert isinstance(mh, Message_Handler)
        assert isinstance(filename, str)
        assert isinstance(content, str) or content is None
        assert isinstance(encoding, str)

        self.mh       = mh
        self.filename = filename
        self.encoding = encoding

        if content is None:
            with open(filename, "r", encoding=encoding) as fd:
                self.content = fd.read()
        else:  # pragma: no cover
            self.content  = content

        self.length  = len(self.content)
        self.lexpos  = -3
        self.cc      = None
        self.nc      = None
        self.nnc     = None
        self.line_no = 1
        self.col_no  = -3

        self.advance()
        self.advance()

    def advance(self):
        if self.cc == "\n":
            self.line_no += 1
            self.col_no = 0
        else:
            self.col_no += 1
        self.cc = self.nc
        self.nc = self.nnc
        self.lexpos += 1
        if self.lexpos + 2 < self.length:
            self.nnc = self.content[self.lexpos + 2]
        else:
            self.nnc = None

    @abstractmethod
    def token(self):
        pass


class Parser_Base(metaclass=ABCMeta):
    def __init__(self, mh, lexer, token_kinds, keywords):
        assert isinstance(mh, Message_Handler)
        assert isinstance(lexer, Lexer_Base)
        assert isinstance(token_kinds, (set, frozenset))
        assert "COMMENT" in token_kinds
        assert "KEYWORD" in token_kinds
        assert isinstance(keywords, (set, frozenset))

        self.token_kinds = token_kinds
        self.keywords    = keywords

        self.mh    = mh
        self.lexer = lexer
        self.ct    = None
        self.nt    = None
        self.advance()

    def advance(self):
        self.ct = self.nt
        while True:
            self.nt = self.lexer.token()
            if self.nt is None or self.nt.kind != "COMMENT":
                break

    def peek(self, kind):
        assert kind in self.token_kinds
        return self.nt and self.nt.kind == kind

    def peek_kw(self, kind):
        assert kind in self.keywords
        return self.peek("KEYWORD") and self.nt.value == kind

    def match(self, kind):
        assert kind in self.token_kinds
        if self.nt is None:
            self.mh.error(Location(self.lexer.filename),
                          "expected %s, got EOF" % kind)
        if self.nt.kind != kind:
            self.mh.error(self.nt.location,
                          "expected %s, got %s" % (kind, self.nt.kind))
        self.advance()

    def match_kw(self, kind):
        assert kind in self.keywords
        if self.nt is None:
            self.mh.error(Location(self.lexer.filename),
                          "expected %s, got EOF" % kind)
        if self.nt.kind != "KEYWORD" or self.nt.value != kind:
            self.mh.error(self.nt.location,
                          "expected %s, got %s" % (kind, self.nt.kind))
        self.advance()

    def match_eof(self):
        if self.nt is not None:
            self.mh.error(self.nt.location,
                          "expected EOF, got %s" % self.nt.kind)
        self.advance()
