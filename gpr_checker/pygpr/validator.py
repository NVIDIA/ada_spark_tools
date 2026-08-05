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

import os
import argparse
import json
import re
from copy import copy
import traceback

from pygpr.errors import Location, Error, ICE, Message_Handler
from pygpr.parser import GPR_Parser
from pygpr.adc_parser import ADC_Parser
from pygpr.version import PYGPR_VERSION, FULL_NAME, BUGS_URL
from pygpr.lkql_parser import LKQL_Parser
from pygpr import ast, lkql_ast
from pygpr import switches, rules


def validate_global_pragmas(mh, n_attr):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_attr, ast.Simple_Attribute)
    assert n_attr.name == "Global_Configuration_Pragmas"
    # TODO: 2.3.1

    config_pragma_filename = n_attr.concrete_value
    if not os.path.isabs(config_pragma_filename):
        config_pragma_filename = os.path.relpath(
            os.path.join(os.path.dirname(n_attr.location.filename),
                         config_pragma_filename))

    if not os.path.isfile(config_pragma_filename):
        mh.error(n_attr.location,
                 "cannot read configuration pragmas file %s" %
                 config_pragma_filename,
                 fatal = False)
        return

    parser = ADC_Parser(mh, config_pragma_filename)
    has_forward_progress = False
    for _, pragma, parameters in parser.parse():
        if pragma == "User_Aspect_Definition" and \
           parameters == ["(", "Forward_Progress", ",",
                          "Local_Restrictions",
                          "(", "No_Secondary_Stack", ",",
                          "No_Heap_Allocations", ")",
                          ",", "Always_Terminates",
                          ")"]:
            has_forward_progress = True

    if not has_forward_progress:
        # This cannot be specified correctly until CS0038331 is
        # fixed. So instead of raising an issue we just print a
        # warning.
        mh.warning(Location(config_pragma_filename),
                   "could not find correct definition for user "
                   "aspect Forward_Progress [2.3.1]")


def validate_switches(mh,
                      location,
                      actual_switches,
                      cmdline_switches,
                      category,
                      check_id_normal,
                      check_id_fallthrough,
                      simple_required_switches,
                      simple_banned_switches,
                      simple_discouraged_switches,
                      simple_qualified_switches,
                      predicate_qualified_switch = None):
    assert isinstance(mh, Message_Handler)
    assert isinstance(location, Location)
    assert isinstance(actual_switches, set)
    assert isinstance(cmdline_switches, set)
    assert isinstance(category, str)
    assert isinstance(check_id_normal, str)
    assert isinstance(check_id_fallthrough, str)
    assert isinstance(simple_required_switches, dict)
    assert isinstance(simple_banned_switches, dict)
    assert isinstance(simple_discouraged_switches, dict)
    assert isinstance(simple_qualified_switches, set)
    assert callable(predicate_qualified_switch) or \
        predicate_qualified_switch is None

    unchecked_switches = copy(actual_switches) | copy(cmdline_switches)
    cmdline_loc = Location("%s commadline" % category.lower())
    switches_with_locations = dict(zip(list(actual_switches) +
                                       list(cmdline_switches),
                                       [location] * len(actual_switches) +
                                       [cmdline_loc] * len(cmdline_switches)))

    # Enforcing required switches
    for required_switches, message in simple_required_switches.items():
        if isinstance(required_switches, str):
            required_switches = (required_switches, )

        for required_switch in required_switches:
            if required_switch in switches_with_locations:
                unchecked_switches.remove(required_switch)
            else:
                mh.issue(location,
                         "required %s switch %s not present (%s)" %
                         (category, required_switch, message),
                         check_id_normal)

    # Enforcing banned switches
    for banned_switches, message in simple_banned_switches.items():
        if isinstance(banned_switches, str):
            banned_switches = (banned_switches, )
        for banned_switch in banned_switches:
            if banned_switch in switches_with_locations:
                unchecked_switches.remove(banned_switch)
                mh.issue(switches_with_locations[banned_switch],
                         "banned %s switch %s must not be present (%s)" %
                         (category, banned_switch, message),
                         check_id_normal)

    # Commenting on discouraged switches
    for bad_switches, message in simple_discouraged_switches.items():
        if isinstance(bad_switches, str):
            bad_switches = (bad_switches, )
        for bad_switch in bad_switches:
            if bad_switch in switches_with_locations:
                unchecked_switches.remove(bad_switch)
                mh.warning(switches_with_locations[bad_switch],
                           "%s switch %s is not advised (%s)" %
                           (category, bad_switch, message))

    # Remove the switches that are optional but qualified
    unchecked_switches -= simple_qualified_switches

    # Anything leftover is banned
    for switch in sorted(unchecked_switches):
        if predicate_qualified_switch is None:  # pragma: no cover
            pass
        elif predicate_qualified_switch(switch):
            continue
        mh.issue(switches_with_locations[switch],
                 "Non-qualified %s switch %s must not be present" %
                 (category, switch),
                 check_id_fallthrough)


def validate_builder_package(mh, n_project, n_package, cmdline_flags):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_project, ast.Project)
    assert isinstance(n_package, ast.Package)
    assert n_package.name == "Builder"
    assert isinstance(cmdline_flags, list)
    assert all(isinstance(item, str) for item in cmdline_flags)
    assert len(cmdline_flags) == 0

    # 2.2.2 Required attributes are set, and no Naming package
    if n_package.has_attribute("Global_Configuration_Pragmas"):
        n_attr = n_package.get_attribute("Global_Configuration_Pragmas")
        validate_global_pragmas(mh, n_attr)
    else:
        mh.issue(n_package.location,
                 "%s.%s must set Global_Configuration_Pragmas" %
                 (n_project.name, n_package.name),
                 "2.2.2")

    return {}


def fetch_switch_lists(mh, n_project, n_package, check_id):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_project, ast.Project)
    assert isinstance(n_package, ast.Package)
    assert isinstance(check_id, str)

    has_default_switches = n_package.has_attribute("Default_Switches")
    if has_default_switches:
        n_attr = n_package.get_attribute("Default_Switches")
        n_default_ada_switches, c_default_ada_switches = \
            n_attr.get_value("Ada")
        if n_default_ada_switches is None:
            # In this case we do have the attribute, but it doesn't
            # have an others clause, nor an explicit Ada value
            has_default_switches = None

    has_override_switches = n_package.has_attribute("Switches")
    if has_override_switches:
        n_attr = n_package.get_attribute("Switches")
        if "Ada" in n_attr.n_value:
            # Warn on global override
            mh.warning(n_attr.n_value["Ada"].location,
                       'This should be Default_Switches("Ada") instead')
        elif n_attr.n_default is not None:
            mh.warning(n_attr.n_default.location,
                       'This should be Default_Switches(others) instead')
        else:
            has_override_switches = False

    if not (has_default_switches or has_override_switches):
        mh.issue(n_package.location,
                 'Cannot find Default_Switches("Ada")',
                 check_id)
        return []

    # Assemble a list of switch options to check. The above makes sure
    # we have at least one cover-all to check here to make sure we're
    # not missing any files.
    switch_lists = []
    if has_default_switches:
        switch_lists.append((n_default_ada_switches.location,
                             set(c_default_ada_switches)))
    if has_override_switches:
        n_attr = n_package.get_attribute("Switches")
        for name, n_value in n_attr.n_value.items():
            switch_lists.append((n_value.location,
                                 set(n_attr.concrete_value[name])))
        if n_attr.n_default is not None:
            switch_lists.append((n_attr.n_default.location,
                                 set(n_attr.concrete_default)))

    return switch_lists


def validate_compiler_package(mh, n_project, n_package, cmdline_flags):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_project, ast.Project)
    assert isinstance(n_package, ast.Package)
    assert n_package.name == "Compiler"
    assert isinstance(cmdline_flags, list)
    assert all(isinstance(item, str) for item in cmdline_flags)

    # https://docs.adacore.com/gprbuild-docs/html/gprbuild_ug/attributes.html#package-compiler-attributes
    #
    # In short there are two relevant attributes:
    #
    # * Default_Switches [string -> list] that defines the general
    #   switches. The index is the language (we care only about Ada)
    #
    # * Switches [string -> list]. The index here can be either a
    #   languagre or glob for files. This will _override_ the default
    #   switches.
    #
    # TODO: We should apply the glob based on the project defined
    # souce lists, and then only consider ads/adb files. But for now
    # we just check everything in Switches.

    # Check id 2.2.3 concerns warnings and style switches
    #
    # * The Requirements Concerning Compiler Warning Switches section
    #
    # * The Requirements Concerning Non-Warning-Related Compiler
    #   Switches section
    #
    # * Any restrictions in the Ada/SPARK Guidelines concerning style
    #   checking switches

    # Check id 2.2.6 is the same but for real switches

    # First we need to check that we have one of these:
    # * Default_Switches (Ada)
    # * Switches (others)
    #
    # Since we have required switches, if we don't find a reasonable
    # catch-all default for Ada we should error out.

    switch_lists = fetch_switch_lists(mh, n_project, n_package, "2.2.3")

    def also_qualified(switch):
        assert isinstance(switch, str)
        for allowed_prefix in ("-gnatw", "-gnaty", "-gnateD",
                               "-gnatep", "-gnatec", "-gnatR",
                               "--RTS="):
            if switch.startswith(allowed_prefix):
                return True
        return False

    # Validate switches
    cmdline_switches = set(cmdline_flags)
    rv = {
        "uses_standard_library" : "-nostdlib" not in cmdline_switches
    }
    for location, actual_switches in switch_lists:
        validate_switches(
            mh                   = mh,
            location             = location,
            actual_switches      = actual_switches,
            cmdline_switches     = cmdline_switches,
            category             = "Compiler",
            check_id_normal      = "2.2.3",
            check_id_fallthrough = "2.2.6",

            simple_required_switches =
            switches.REQUIRED_ADA_COMPILER_SWITCHES,

            simple_banned_switches =
            switches.BANNED_ADA_COMPILER_SWITCHES,

            simple_discouraged_switches =
            switches.DISCOURAGED_ADA_COMPILER_SWITCHES,

            simple_qualified_switches =
            switches.QUALIFIED_ADA_SWITCHES,

            predicate_qualified_switch = also_qualified)
        if "-nostdlib" in actual_switches:
            rv["uses_standard_library"] = False

    return rv


def validate_prove_package(mh, n_project, n_package, cmdline_flags):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_project, ast.Project)
    assert isinstance(n_package, ast.Package)
    assert n_package.name == "Prove"
    assert isinstance(cmdline_flags, list)
    assert all(isinstance(item, str) for item in cmdline_flags)

    # 2.2.4 Does each unit GPR file (combined with any other GPR files
    # recursively included via with keywords) with a Prove package
    # refrain from specifying any GNATprove switches prohibited by the
    # Requirements Concerning GNATprove Switches section?
    #
    # And the fall-though check in 2.2.6 that we didn't use anything
    # else.

    # For the Prove package switches are assembled differently. The
    # Proof_Switches indexed attribute can provide a default (via
    # "Ada", others is not permitted) and then an _addition_ of
    # switches in file specific extra rules. This contrasts with the
    # compiler switches which seem to overwrite.
    #
    # The Switches attribute is deprecated.
    #
    # https://docs.adacore.com/spark2014-docs/html/ug/en/appendix/project_attributes.html

    if n_package.has_attribute("Switches"):
        location = n_package.get_attribute("Switches").location
        mh.issue(location,
                 "this is deprecated, rewrite to use Proof_Switches",
                 "SPARK UG")
        mh.error(location,
                 "aborting gpr analysis since we don't understand the impact"
                 " of attribute Prove.Switches")

    if not n_package.has_attribute("Proof_Switches"):
        mh.issue(n_package.location,
                 "The Proof_Switches attribute is required",
                 "4.2.4")
        return

    n_attr = n_package.get_attribute("Proof_Switches")
    if "Ada" not in n_attr.n_value:
        mh.issue(n_package.location,
                 'The Proof_Switches("Ada") attribute is required',
                 "4.2.4")
        return
    base_switches = n_attr.concrete_value["Ada"]

    switch_lists = [(n_attr.n_value["Ada"].location,
                     set(base_switches))]
    for name, n_value in n_attr.n_value.items():
        if name == "Ada":
            continue
        switch_lists.append((n_value.location,
                             set(base_switches + n_attr.concrete_value[name])))

    for location, actual_switches in switch_lists:
        validate_switches(
            mh                   = mh,
            location             = location,
            actual_switches      = actual_switches,
            cmdline_switches     = set(cmdline_flags),
            category             = "GNATProve",
            check_id_normal      = "2.2.4",
            check_id_fallthrough = "2.2.6",

            simple_required_switches =
            switches.REQUIRED_GNATPROVE_SWITCHES,

            simple_banned_switches =
            switches.BANNED_GNATPROVE_SWITCHES,

            simple_discouraged_switches = {},

            simple_qualified_switches =
            switches.QUALIFIED_SPARK_SWITCHES,

            predicate_qualified_switch = switches.also_qualified_gnatprove)

    return {}


def validate_check_package(mh, n_project, n_package, cmdline_flags):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_project, ast.Project)
    assert isinstance(n_package, ast.Package)
    assert n_package.name == "Check"
    assert isinstance(cmdline_flags, list)
    assert all(isinstance(item, str) for item in cmdline_flags)

    # I could not find any documentation. However I assume this works
    # just like the Compiler package.

    switch_lists = fetch_switch_lists(mh, n_project, n_package, "2.2.5")

    def also_qualified(switch):
        assert isinstance(switch, str)

        for prefix in ("+R", "-from=", "--rule-file="):
            if switch.startswith(prefix):
                return True

        return False

    for location, actual_switches in switch_lists:
        assert isinstance(location, Location)
        assert isinstance(actual_switches, set)
        assert all(isinstance(s, str) for s in actual_switches)

        # Basic checking
        validate_switches(
            mh                   = mh,
            location             = location,
            actual_switches      = actual_switches,
            cmdline_switches     = set(cmdline_flags),
            category             = "GNATCheck",
            check_id_normal      = "2.2.5",
            check_id_fallthrough = "2.2.6",

            simple_required_switches =
            switches.REQUIRED_GNATCHECK_SWITCHES,

            simple_banned_switches =
            switches.BANNED_GNATCHECK_SWITCHES,

            simple_discouraged_switches = {},

            simple_qualified_switches = switches.QUALIFIED_GNATCHECK_SWITCHES,

            predicate_qualified_switch = also_qualified)

        # Ruleset checking
        rule_file_name = None
        rule_file_loc  = None
        if n_package.has_attribute("Rule_File"):
            n_rule_file = n_package.get_attribute("Rule_File")
            assert isinstance(n_rule_file, ast.Simple_Attribute)
            if isinstance(n_rule_file.n_value, ast.String_Literal):
                rule_file_name = n_rule_file.n_value.string_value
                rule_file_loc  = n_rule_file.n_value.location
            else:  # pragma: no cover
                mh.error(n_rule_file.n_value.location,
                         "must be a simple string",
                         fatal = False)

        for switch in sorted(actual_switches):
            if switch.startswith("+R"):
                mh.error(location,
                         "old +R rule configuration is deprecated in"
                         " favour of --rule-file=",
                         fatal = False)
                continue
            elif switch.startswith("-from="):
                mh.error(location,
                         "old -from= rule configuration is deprecated in"
                         " favour of --rule-file=",
                         fatal = False)
                continue
            elif switch.startswith("--rule-file="):
                if rule_file_name is None:
                    rule_file_name = switch.split("=", 1)[1]
                    rule_file_loc  = location
                else:
                    mh.error(location,
                             "only a single lkql rule config may be supplied",
                             fatal = False)

        if rule_file_name is not None and not os.path.isfile(rule_file_name):
            mh.issue(location,
                     "cannot open rule config file '%s'" %
                     rule_file_name,
                     "4.3.4")
            rule_file_name = None

        decl_list = []
        if rule_file_name is not None:
            try:
                lkql_parser = LKQL_Parser(mh, rule_file_name)
                decl_list   = lkql_parser.parse_compilation_unit()
            except Error:
                mh.issue(location, "rule file contains parse errors", "4.3.4")
        validate_rule_file(mh,
                           rule_file_loc
                           if rule_file_loc is not None
                           else location,
                           decl_list)

    return {}


def validate_rule_file(mh, base_loc, decl_list):
    assert isinstance(mh, Message_Handler)
    assert isinstance(base_loc, Location)
    assert isinstance(decl_list, list)
    assert all(isinstance(decl, lkql_ast.Value_Declaration)
               for decl in decl_list)

    rule_set = {"rules"       : None,
                "ada_rules"   : None,
                "spark_rules" : None}
    loc = base_loc
    for decl in decl_list:
        # These three checks are more like sanity checks - they
        # indicate a truly broken rule file that would not be accepted
        # by gnatcheck. It's not meaningful to test these.

        if decl.name not in rule_set:  # pragma: no cover
            mh.error(decl.location,
                     "invalid rule set %s" % decl.name)
        elif rule_set[decl.name] is not None:  # pragma: no cover
            mh.error(decl.location,
                     "duplicate value declaration for %s" % decl.name)

        if not isinstance(decl.n_value,
                          lkql_ast.Object_Literal):  # pragma: no cover
            mh.error(decl.n_value.location,
                     "must be a object literal")

        rule_set[decl.name] = decl.n_value.values
        if decl.name == "rules":
            loc = decl.location

    for check in rules.REQUIRED_GNATCHECK_RULES:
        check.perform(mh           = mh,
                      loc          = loc,
                      common_rules = rule_set["rules"],
                      ada_rules    = rule_set["ada_rules"],
                      spark_rules  = rule_set["spark_rules"])


def validate_project(mh, n_project, extra_flags):
    assert isinstance(mh, Message_Handler)
    assert isinstance(n_project, ast.Project)
    assert isinstance(extra_flags, dict)

    # Skip projects that contain a skip_file pragma
    if n_project.skip_reason is not None:
        mh.info(n_project.location,
                "skipping validation of %s: %s" % (n_project.name,
                                                   n_project.skip_reason))
        return

    # Skip projects that are marked as externally built. In the spirit
    # of modular verification you have to check the original project.
    if n_project.has_attribute("Externally_Built"):
        n_attr = n_project.get_attribute("Externally_Built")
        assert isinstance(n_attr, ast.Simple_Attribute)
        if n_attr.concrete_value.lower() == "true":
            mh.info(n_project.location,
                    "skipping externally build project")
            return

    #######################################################################
    # Check project attributes
    #######################################################################

    # Check presence of certain required packages
    checked_packages = {
        # 2.2.2, 2.3.1
        "Builder" : (validate_builder_package, "2.2.2", []),

        # 2.2.3, 2.2.6
        "Compiler" : (validate_compiler_package,
                      "2.2.3",
                      extra_flags.get("gprbuild", [])),

        # 2.2.4, 2.2.6, 4.2.4, 4.13.4
        "Prove" : (validate_prove_package,
                   "4.2.4",
                   extra_flags.get("gnatprove", [])),

        # 2.2.5, 2.2.6, 4.3.3, 4.3.4,
        "Check" : (validate_check_package,
                   "4.3.3",
                   extra_flags.get("gnatcheck", [])),
    }

    info = {"uses_standard_library" : True}
    for package_name, (analysis_procedure,
                       check_id,
                       cmdline_flags) in checked_packages.items():
        if n_project.symbols.contains_raw(package_name):
            new_info = analysis_procedure(
                mh,
                n_project,
                n_project.symbols.lookup_raw_assuming(package_name),
                cmdline_flags)
            if new_info:
                info.update(new_info)
        else:
            mh.issue(n_project.location,
                     "project requires a %s package" % package_name,
                     check_id)
            if package_name == "Check":
                mh.issue(n_project.location,
                         "zero gnatcheck rules are enabled",
                         "4.3.4")

    # Ban the presence of certain packages
    banned_packages = {
        "Naming" : "2.2.2",
    }

    for package_name, check_id in banned_packages.items():
        if n_project.symbols.contains_raw(package_name):
            n_pkg = n_project.symbols.lookup_raw_assuming(package_name)
            mh.issue(n_pkg.location,
                     "project must not declare the %s package" % package_name,
                     check_id)

    #######################################################################
    # Check project attributes
    #######################################################################

    # 2.2.2 Required attributes are set, and no Naming package
    if n_project.has_attribute("Runtime"):
        n_attr = n_project.get_attribute("Runtime")
        assert isinstance(n_attr, ast.Map_Attribute)

        n_ada_runtime, conc_ada_runtime = n_attr.get_value("Ada")
        if n_ada_runtime is None:
            mh.issue(n_attr.location,
                     "%s'Runtime does not have a value for Ada" %
                     n_project.name,
                     "2.2.2")
        else:
            runtime_name = None
            if conc_ada_runtime is None:
                mh.ice_loc(n_ada_runtime.location,
                           "expected actual value")
            elif not isinstance(conc_ada_runtime, str):
                pass
            elif m := re.match(r".*[/\\](.*_runtime)[/\\].*",
                               conc_ada_runtime):
                runtime_name = m.group(1)

            if runtime_name is None:
                mh.issue(n_attr.location,
                         "cannot understand %s'Runtime,"
                         " expected path ending in _runtime" % n_project.name,
                         "2.2.2")
            elif runtime_name not in switches.ALLOWED_ADA_RUNTIMES and \
               info["uses_standard_library"]:
                mh.issue(n_ada_runtime.location,
                         "%s runtime '%s' is not one of the allowed ones"
                         % (n_project.name, runtime_name),
                         "2.2.2")

    else:
        mh.issue(n_project.location,
                 "%s does not define a Runtime" % n_project.name,
                 "2.2.2")

    if n_project.has_attribute("Target"):
        n_attr = n_project.get_attribute("Target")
        if n_attr.concrete_value not in switches.ALLOWED_TARGETS:
            mh.issue(n_attr.location,
                     "%s is not one of the allowed targets" %
                     n_attr.concrete_value,
                     "2.2.2")
    else:
        mh.issue(n_project.location,
                 "%s does not define a Target" % n_project.name,
                 "2.2.2")


def validate_closure(mh, stab, extra_flags):
    assert isinstance(mh, Message_Handler)
    assert isinstance(stab, ast.Symbol_Table)
    assert isinstance(extra_flags, dict)

    for n_project in stab.symbols.values():
        validate_project(mh, n_project, extra_flags)


def top_down(mh, stab, parsers, in_progress, done, file_name):
    assert isinstance(mh, Message_Handler)
    assert isinstance(stab, ast.Symbol_Table)
    assert isinstance(parsers, dict)
    assert isinstance(in_progress, set)
    assert isinstance(done, set)
    assert isinstance(file_name, str)

    if file_name in done:
        return

    if file_name in in_progress:
        mh.error(Location(os.path.relpath(file_name)),
                 "cyclic dependency in %s" %
                 ", ".join(os.path.relpath(name)
                           for name in sorted(in_progress)))

    in_progress.add(file_name)

    for t_dep in parsers[file_name].dependencies:
        top_down(mh, stab, parsers, in_progress, done,
                 os.path.abspath(os.path.join(os.path.dirname(file_name),
                                              t_dep.value)))

    parsers[file_name].parse_gpr()

    in_progress.remove(file_name)
    done.add(file_name)

    for t_dep in parsers[file_name].limited_dependencies:
        top_down(mh, stab, parsers, in_progress, done,
                 os.path.abspath(os.path.join(os.path.dirname(file_name),
                                              t_dep.value)))


def validate_gpr(mh,
                 main_file,
                 externals,
                 json_name,
                 validate,
                 show_version,
                 show_report,
                 extra_flags):
    assert isinstance(mh, Message_Handler)
    assert isinstance(main_file, str)
    assert isinstance(externals, dict)
    assert isinstance(json_name, str) or json_name is None
    assert isinstance(validate, bool)
    assert isinstance(show_version, bool)
    assert isinstance(show_report, bool)
    assert isinstance(extra_flags, dict)

    dep_list = set([main_file])
    lim_list = set()
    parsers  = {}
    stab     = ast.Symbol_Table()

    while dep_list or lim_list:
        if dep_list:
            filename = dep_list.pop()
        else:  # pragma: no cover
            # Doesn't really matter if this is not tested
            filename = lim_list.pop()

        filename = os.path.abspath(filename)

        if not os.path.isfile(filename):
            mh.error(Location(filename),
                     "cannot find file")

        parsers[filename] = GPR_Parser(mh, stab, filename, externals)
        parsers[filename].parse_context_clause()

        dep_list |= set(os.path.abspath(os.path.join(os.path.dirname(filename),
                                                     tok.value))
                        for tok in parsers[filename].dependencies)
        lim_list |= set(os.path.abspath(os.path.join(os.path.dirname(filename),
                                                     tok.value))
                        for tok in parsers[filename].limited_dependencies)

        dep_list -= set(parsers)
        lim_list -= set(parsers)

    done = set()
    in_progress = set()
    top_down(mh, stab, parsers, in_progress, done, os.path.abspath(main_file))

    if json_name:
        mh.write("Wrote %s" % json_name)
        with open(json_name, "w", encoding="UTF-8") as fd:
            json.dump(stab.serialise(), fd, indent=2)
            fd.write("\n")

    if not validate:  # pragma: no cover
        return

    validate_closure(mh, stab, extra_flags)

    if not show_report:  # pragma: no cover
        return

    if show_version:  # pragma: no cover
        banner_text = "= GPR Validator (%s) Report for %s =" % \
            (PYGPR_VERSION, main_file)
    else:
        banner_text = "= GPR Validator Report for %s =" % main_file

    mh.write("=" * len(banner_text))
    mh.write(banner_text)
    mh.write("=" * len(banner_text))

    mh.write("%u file(s) checked:" % len(parsers))
    for file_name in sorted(parsers):
        mh.write("* %s" % os.path.relpath(file_name))

    fully_checked = {
        "2.2.2": "gpr project correctly configured",
        "2.2.3": "gpr compiler package correctly configured",
        "2.2.4": "gpr prove package does not use banned switches",
        "2.2.5": "gpr check package does not use banned switches",
        "2.2.6": "no non-safety qualified switches used",
        "2.3.1": "forward_progress is correctly configured",
    }

    partially_checked = {
        "4.2.4": "all required gnatprove switches used",
        "4.3.3": "all required gnatcheck switches are used",
        "4.3.4": "all required gnatcheck rules are enabled",
        # "4.13.4": "all required gnatprove switches used (for tests)",
    }

    check_length = max(map(len,
                           list(fully_checked) +
                           list(partially_checked)))
    descr_length = max(map(len,
                           list(fully_checked.values()) +
                           list(partially_checked.values())))

    def fmt_findings(n):
        assert isinstance(n, int) and n >= 0
        match n:
            case 0:
                return "VERIFIED"
            case 1:
                return "1 finding"
            case _:
                return "%u findings" % n

    mh.write_blank_line()
    mh.write("Checklist items fully checked:")
    for check_id in sorted(fully_checked):
        mh.write("* %*s (%-*s): %s" %
                 (check_length, check_id,
                  descr_length, fully_checked[check_id],
                  fmt_findings(mh.issues.get(check_id, 0))))

    mh.write_blank_line()
    mh.write("Checklist items partially checked:")
    for check_id in sorted(partially_checked):
        mh.write("* %*s (%-*s): %s" %
                 (check_length, check_id,
                  descr_length, partially_checked[check_id],
                  fmt_findings(mh.issues.get(check_id, 0))))

    mh.write_blank_line()
    mh.write("Overall verdict: %s" %
             ("NON COMPLIANT" if mh.issues else "COMPLIANT"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filename")

    ag = ap.add_argument_group("environment")
    ag.add_argument("-X",
                    metavar="name=value",
                    help="define external variable",
                    action="append",
                    default=[])
    ag.add_argument("--additional-gprbuild-flag",
                    metavar="name=value",
                    help="specify gprbuild command-line flag",
                    action="append",
                    default=[])
    ag.add_argument("--additional-gnatprove-flag",
                    metavar="name=value",
                    help="specify gnatprove command-line flag",
                    action="append",
                    default=[])
    ag.add_argument("--additional-gnatcheck-flag",
                    metavar="name=value",
                    help="specify gnatcheck command-line flag",
                    action="append",
                    default=[])
    ag.add_argument("--additional-permitted-target",
                    help="also allow the specified target",
                    action="append",
                    default=[])
    ag.add_argument("--additional-permitted-runtime",
                    help="also allow the specified runtime",
                    action="append",
                    default=[])

    ag = ap.add_argument_group("checking")
    ag.add_argument("--validate",
                    help="enforce rules from the SPARK process",
                    default=False,
                    action="store_true")

    ag = ap.add_argument_group("output")
    ag.add_argument("--verbose",
                    help="also produce a summary of checklist items",
                    default=False,
                    action="store_true")
    ag.add_argument("--no-version-in-report",
                    help="do not include tool versions in the report",
                    default=False,
                    action="store_true")
    ag.add_argument("--write-json",
                    metavar="FILE",
                    help="dump concrete values to the named json file",
                    default=None)
    ag.add_argument("--save-log",
                    metavar="FILE",
                    help=("also dump error messages and summary to the"
                          " named file"),
                    default=None)
    ag.add_argument("--no-std-output",
                    action="store_true",
                    help=("do not write messages to standard output"),
                    default=False)

    ag = ap.add_argument_group("debug")
    ag.add_argument("--debug-tb",
                    help="show traceback even on normal errors",
                    default=False,
                    action="store_true")
    ag.add_argument("--version",
                    help="print PyGPR version and stop",
                    default=False,
                    action="store_true")

    options = ap.parse_args()

    if options.no_std_output and \
       options.save_log is None:  # pragma: no cover
        ap.error("--no-std-output cannot be specified without --save-log")

    if options.version:  # pragma: no cover
        print(PYGPR_VERSION)
        return 0

    externals = {}
    for assignment in options.X:
        try:
            variable, value = assignment.split("=", 1)
            externals[variable] = value
        except ValueError:  # pragma: no cover
            ap.error("-X%s does not match the name=value pattern" % assignment)

    for target in options.additional_permitted_target:
        switches.ALLOWED_TARGETS.add(target)
    for runtime in options.additional_permitted_runtime:
        switches.ALLOWED_ADA_RUNTIMES.add(runtime)

    mh = Message_Handler(write_stdout = not options.no_std_output,
                         write_file   = options.save_log)

    try:
        validate_gpr(mh           = mh,
                     main_file    = options.filename,
                     externals    = externals,
                     json_name    = options.write_json,
                     validate     = options.validate,
                     show_version = not options.no_version_in_report,
                     show_report  = options.verbose,
                     extra_flags  = {
                         "gprbuild"  : options.additional_gprbuild_flag,
                         "gnatprove" : options.additional_gnatprove_flag,
                         "gnatcheck" : options.additional_gnatcheck_flag,
                     })
        if mh.errors or mh.issues:
            return 1
        else:
            return 0

    except (AssertionError, ICE) as error:  # pragma: no cover
        traceback.print_exception(error)
        print("=" * 70)
        print("= I have encountered an internal compiler error, i.e. a bug")
        print("= in the tool. Please raise an issue on")
        print("= %s" % BUGS_URL)
        print("= to get it fixed!")
        print("=")
        print("= Please include the tool version (%s), the entire" % FULL_NAME)
        print("= traceback shown above, full command-line and all files")
        print("= specified on the command-linein your ticket.")
        print("=" * 70)
        return 2

    except Error:
        if options.debug_tb:  # pragma: no cover
            raise
        else:
            return 1


if __name__ == "__main__":
    main()
