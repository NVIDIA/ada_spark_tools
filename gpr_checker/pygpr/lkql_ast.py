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

from abc import ABCMeta

from pygpr.lkql_lexer import Token
from pygpr.ast import Node, Entity, Symbol_Table


class Statement(Node, metaclass=ABCMeta):
    pass


class Value_Declaration(Statement):
    def __init__(self, t_name, n_value):
        assert isinstance(t_name, Token)
        assert t_name.kind == "IDENTIFIER"
        assert isinstance(n_value, Expression)

        super().__init__(t_name.location)

        self.name    = t_name.value
        self.n_value = n_value

    def dump(self, indent=0):
        self.write_header(indent, extra=self.name)
        self.n_value.dump(indent + 1)


class Expression(Node):
    def dump(self, indent=0):
        self.write_header(indent)


class Literal(Expression, metaclass=ABCMeta):
    pass


class Simple_Literal(Literal, metaclass=ABCMeta):
    pass


class Composite_Literal(Literal, metaclass=ABCMeta):
    pass


class Object_Key(Entity):
    pass


class Object_Member(Entity):
    def __init__(self, n_key, n_value):
        assert isinstance(n_key, Object_Key)
        assert isinstance(n_value, Expression) or n_value is None
        super().__init__(n_key.location, n_key.name.lower())
        self.n_key   = n_key
        self.n_value = n_value

    def dump(self, indent=0):
        super().dump(indent)
        if self.n_value is not None:
            self.n_value.dump(indent + 1)


class Object_Literal(Composite_Literal):
    def __init__(self, location, default_allowed):
        assert isinstance(default_allowed, bool)
        super().__init__(location)
        self.default_allowed = default_allowed
        self.values          = Symbol_Table(case_sensitive=False)

    def dump(self, indent=0):
        super().dump(indent)
        self.write_indent(indent + 1,
                          "Default_Allowed: %s" % self.default_allowed)
        self.values.dump(indent + 1)


class Sequence_Literal(Composite_Literal):
    def __init__(self, location):
        super().__init__(location)

        self.values = []

    def dump(self, indent=0):
        super().dump(indent)
        for item in self.values:
            item.dump(indent + 1)


class List_Literal(Sequence_Literal):
    pass


class Tuple_Literal(Sequence_Literal):
    pass


class String_Literal(Simple_Literal):
    def __init__(self, t_string):
        assert isinstance(t_string, Token)
        assert t_string.kind == "STRING"
        super().__init__(t_string.location)
        self.value = t_string.value

    def dump(self, indent=0):
        self.write_header(indent, extra=self.value)


class Integer_Literal(Simple_Literal):
    def __init__(self, t_int):
        assert isinstance(t_int, Token)
        assert t_int.kind == "INTEGER"
        super().__init__(t_int.location)
        self.value = t_int.value

    def dump(self, indent=0):
        self.write_header(indent, extra=str(self.value))


class Boolean_Literal(Simple_Literal):
    def __init__(self, t_bool):
        assert isinstance(t_bool, Token)
        assert t_bool.kind == "KEYWORD"
        assert t_bool.value in ("true", "false")
        super().__init__(t_bool.location)
        self.value = t_bool.value == "true"

    def dump(self, indent=0):
        self.write_header(indent, extra=str(self.value))
