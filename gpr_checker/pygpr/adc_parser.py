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
from pygpr.lexer import ADC_Token, ADC_Lexer
from pygpr.parser import Parser_Base


class ADC_Parser(Parser_Base):
    def __init__(self, mh, filename):
        assert isinstance(mh, Message_Handler)
        assert isinstance(filename, str)
        super().__init__(mh          = mh,
                         lexer       = ADC_Lexer(mh, filename),
                         token_kinds = ADC_Token.KINDS,
                         keywords    = ADC_Token.KEYWORDS)

        self.entries = []

    def parse(self):
        while self.nt:
            self.parse_pragma()

        return self.entries

    def parse_pragma(self):
        self.match_kw("pragma")
        self.match("IDENTIFIER")
        t_pragma = self.ct

        params = []
        while not self.peek("SEMICOLON"):
            if not self.nt:
                # Force termination
                break
            self.advance()
            params.append(self.ct)
        self.match("SEMICOLON")

        self.entries.append((t_pragma.location,
                             t_pragma.value,
                             [t.to_string() for t in params]))
