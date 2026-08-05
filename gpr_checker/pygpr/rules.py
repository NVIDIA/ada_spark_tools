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

from abc import abstractmethod, ABCMeta

from pygpr.errors import Message_Handler, Location
from pygpr.ast import Symbol_Table
from pygpr import lkql_ast


class Simple_Rule_Enforcement(metaclass=ABCMeta):
    def __init__(self, rule_name, scope, message):
        assert isinstance(rule_name, str)
        assert scope in ("spark+ada", "ada")
        assert isinstance(message, str)
        self.rule_name = rule_name
        self.scope     = scope
        self.message   = message
        self.issue_id  = "4.3.4"

    def dispatch(self, mh, rules):
        assert isinstance(mh, Message_Handler)
        assert isinstance(rules, Symbol_Table)

        if not rules.contains_raw(self.rule_name):
            return False
        member = rules.lookup_raw_assuming(self.rule_name)
        assert isinstance(member, lkql_ast.Object_Member)

        if member.n_value is None:  # pragma: no cover
            # Not covered as we currently don't have any rules without
            # parameters we wish to enforce.

            # Simple rule, e.g. "same_logic" without parameters
            return self.perform_simple_check(mh, member)

        elif isinstance(member.n_value, lkql_ast.List_Literal):
            # Potentially multiple instances of one rule
            # rule: [{...}, {...}]
            for item in member.n_value.values:
                if self.perform_complex_check(mh, item):
                    return True
            return False

        else:
            # Single instance of a rule with parameters
            return self.perform_complex_check(mh, member.n_value)

    @abstractmethod
    def perform_simple_check(self, mh, member):
        assert isinstance(mh, Message_Handler)
        assert isinstance(member, lkql_ast.Object_Member)

    @abstractmethod
    def perform_complex_check(self, mh, obj):
        assert isinstance(mh, Message_Handler)
        assert isinstance(obj, lkql_ast.Object_Literal)

    @abstractmethod
    def flag_issue(self, mh, loc):
        assert isinstance(mh, Message_Handler)
        assert isinstance(loc, Location)

    def perform(self, mh, loc, common_rules, ada_rules, spark_rules):
        assert isinstance(mh, Message_Handler)
        assert isinstance(common_rules, Symbol_Table) or common_rules is None
        assert isinstance(ada_rules, Symbol_Table) or ada_rules is None
        assert isinstance(spark_rules, Symbol_Table) or spark_rules is None
        if common_rules is not None:
            if self.dispatch(mh, common_rules):
                return
        if ada_rules is not None and self.scope == "ada":
            if self.dispatch(mh, ada_rules):
                return
        if spark_rules is not None and \
           self.scope == "spark":  # pragma: no cover
            # Currently this is not possible to use (dead code)
            # but if we add spark-specific rules to enforce we'll need it
            if self.dispatch(mh, spark_rules):
                return
        self.flag_issue(mh, loc)


class Rule_Enforcement(Simple_Rule_Enforcement, metaclass=ABCMeta):
    def __init__(self, rule_name, scope, attribute, message):
        super().__init__(rule_name, scope, message)
        assert isinstance(attribute, str)
        self.attribute = attribute

    def perform_simple_check(self, mh, member):
        assert isinstance(mh, Message_Handler)
        assert isinstance(member, lkql_ast.Object_Member)
        return False


class Contains_Enforcement(Rule_Enforcement):
    def __init__(self, rule, scope, attribute, expect, message):
        super().__init__(rule, scope, attribute, message)
        assert isinstance(expect, str)
        self.required_member = expect

    def perform_complex_check(self, mh, obj):
        assert isinstance(mh, Message_Handler)
        assert isinstance(obj, lkql_ast.Object_Literal)
        if not obj.values.contains_raw(self.attribute):
            return False
        value = obj.values.lookup_raw_assuming(self.attribute).n_value
        if not isinstance(value, lkql_ast.List_Literal):
            mh.error(value.location,
                     "value for %s is not a List" % self.attribute,
                     fatal=False)
            return False
        for item in value.values:
            if isinstance(item, lkql_ast.String_Literal):
                if item.value == self.required_member:
                    return True
        return False

    def flag_issue(self, mh, loc):
        assert isinstance(mh, Message_Handler)
        assert isinstance(loc, Location)
        mh.issue(loc,
                 "rule %s does not contain %s in attribute %s in %s (%s)" %
                 (self.rule_name,
                  self.required_member,
                  self.attribute,
                  self.scope,
                  self.message),
                 self.issue_id)


class Boolean_Enforcement(Rule_Enforcement):
    def __init__(self, rule, scope, attribute, expect, message):
        super().__init__(rule, scope, attribute, message)
        assert isinstance(expect, bool)
        self.required_value = expect

    def perform_complex_check(self, mh, obj):
        assert isinstance(mh, Message_Handler)
        assert isinstance(obj, lkql_ast.Object_Literal)
        if not obj.values.contains_raw(self.attribute):
            return False
        value = obj.values.lookup_raw_assuming(self.attribute).n_value
        if not isinstance(value, lkql_ast.Boolean_Literal):
            mh.error(value.location,
                     "value for %s is not a Boolean" % self.attribute,
                     fatal = False)
            return False
        return value.value == self.required_value

    def flag_issue(self, mh, loc):
        assert isinstance(mh, Message_Handler)
        assert isinstance(loc, Location)
        mh.issue(loc,
                 "rule %s does not configure %s = %s in %s (%s)" %
                 (self.rule_name,
                  self.attribute,
                  self.required_value,
                  self.scope,
                  self.message),
                 self.issue_id)


REQUIRED_GNATCHECK_RULES = [
    # Rules for the new SPARK process

    Contains_Enforcement(
        rule      = "Forbidden_Pragmas",
        scope     = "spark+ada",
        attribute = "forbidden",
        expect    = "Extensions_Allowed",
        message   = ("GNAT language extensions are outside"
                     " certification scope")),

    Contains_Enforcement(
        rule      = "Forbidden_Pragmas",
        scope     = "spark+ada",
        attribute = "forbidden",
        expect    = "Validity_Checks",
        message   = ("Required because pragma Validity_Checks is"
                     " not safety-certified")),

    Contains_Enforcement(
        rule      = "Forbidden_Pragmas",
        scope     = "spark+ada",
        attribute = "forbidden",
        expect    = "Ignore_Pragma",
        message   = ("Required because pragma Ignore_Pragma can "
                     " cause SPARK to be silently disabled")),

    Boolean_Enforcement(
        rule      = "Goto_Statements",
        scope     = "ada",
        attribute = "only_unconditional",
        expect    = True,
        message   = ("Required for compliance with ISO 26262-6:2018,"
                     " Table 6, row 1i 'No unconditional jumps'")),
]
