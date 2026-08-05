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

import re

# pylint: disable=line-too-long

ALLOWED_ADA_RUNTIMES = set([
    # 24.1
    "aarch64_qnx_runtime",
    "hv_aarch64_elf_runtime",
])

ALLOWED_TARGETS = set([
    # 24.1
    "aarch64-elf",
    "aarch64-nto-qnx",

    # Since 25.1
    "riscv32-elf",
    "riscv64-elf",
])

REQUIRED_ADA_COMPILER_SWITCHES = {
    #
    # Warnings
    #
    ("-gnatwa",
     "-Wall"): "Enables warnings that are not controversial.",
    "-gnatw.d" : "Expected to provide greater clarity to warnings. (Also, other compilers do this by default.)",
    ("-gnatwe",
     "-Werror"): "Treating warnings as errors results in warnings being taken seriously and results in cleaner build output",
    "-gnatwh": "Implicitly-hidden declarations are a potential source of confusion when reading code.",
    "-gnatw.h": "Record representation clauses should be complete and fully specify the layout, and that a hole might be an indication of an error.",
    "-gnatw.j": 'Per AdaCore (see [V413-003]), the chief designer of Ada 95 believes that Ada "should have disallowed ... adding visible operations to a tagged type after deriving a private extension from it" due to the confusion created. The capability also does not appear to add value to the language.',
    "-gnatw.k": "As warned by AdaCore, redefining names in package Standard could lead to confusion.",
    "-gnatwl": "This warning appears to prevent elaboration problems that could lead to exceptions",
    "-gnatw.o": "This switch enables warnings that are a straightforward extension of warnings enabled by -gnatwu/-gnatwa. For consistency, enable these warnings.",
    "-gnatw_r": "Record representation clauses should be structurally consistent with the associated record type definitions to ensure a complete consideration of the constraints on representation.",
    "-gnatw.s": "Record representation clauses should not contradict the associated record type definitions.",
    "-gnatwt": "It is expected that every code path within a compilation unit will be reachable without modification of the compilation unit so that every code path can be tested using the same object code as what ships to customers",
    "-gnatw.w": "Enables useful warnings about misuse of Warnings Off pragmas.",
    "-gnatw.X": "Necessary when using pragma Restrictions (No_Exception_Propagation) to avoid spurious warnings compiling SPARK code (see V223-002)",

    #
    # Non-warnings
    #
    "-fcallgraph-info=su,da": "Necessary to ensure that GNATstack produces correct output in the Check_Stack_Usage step.",
    "-gnatyr": "Unique IDs (see section Traceability Model) are case sensitive and built from local IDs sometimes derived from identifiers. To remove ambiguity concerning the correct local ID (and thus the correct unique ID) for a comment or syntactic construct, all references to the same entity must agree about the case of the associated identifiers.",

}

BANNED_ADA_COMPILER_SWITCHES = {
    #
    # Warnings
    #
    ("-gnatwA",
     "-gnatw.A",
     "-gnatw_A",
     "-gnatwB",
     "-gnatw.B",
     "-gnatwC",
     "-gnatw.C",
     "-gnatw_C",
     "-gnatwF",
     "-gnatwG",
     "-gnatwI",
     "-gnatw.I",
     "-gnatwJ",
     "-gnatwK",
     "-gnatwM",
     "-gnatw.M",
     "-gnatwP",
     "-gnatw.P",
     "-gnatw_P",
     "-gnatwQ",
     "-gnatwR",
     "-gnatw.R",
     "-gnatw.T",
     "-gnatwU",
     "-gnatwV",
     "-gnatw.V",
     "-gnatwW",
     "-gnatwX",
     "-gnatwY",
     "-gnatwZ",
     "-gnatw.Z"): "Would suppress warnings enabled by -gnatwa",
    "-gnatw.D": "Would suppress effects of -gnatw.d",
    "-gnatwH": "Would suppress effects of -gnatwh",
    "-gnatw.H": "Would suppress effects of -gnatw.h",
    "-gnatw.J": "Would suppress effects of -gnatw.j",
    "-gnatw.K": "Would suppress effects of -gnatw.k",
    "-gnatwL": "Would suppress effects of -gnatwl",
    "-gnatwn": "Would suppress effects of -gnatwe",
    "-gnatwO": "Would disable some warnings that are enabled by default",
    "-gnatw.O": "Would suppress effects of -gnatw.o",
    "-gnatw_R": "Would suppress effects of -gnatw_r",
    "-gnatws": "Would disable all warnings",
    "-gnatw.S": "Would suppress effects of -gnatw.s",
    "-gnatwT": "Would suppress effects of -gnatwt",
    "-gnatw.W": "Would suppress effects of -gnatw.w",
    "-gnatw.x": "Would undo effects of -gnatw.X",
    "-w": "Would undo effects of -Wall",

    #
    # Non-warnings
    #
    "-gnata": "This switch causes contracts to be executed at runtime, and contracts and ghost code are permitted to use Ada 2022, but Ada 2022 is not safety qualified for production use.",
    "--RTS": "The runtime should be set at project level.",
    ("-c",
     "-o",
     "-I",
     "-x",
     "-S"): "Will be added by gprbuild.",

    # Plus any others not explicitly mentioned in the safety manual
}

DISCOURAGED_ADA_COMPILER_SWITCHES = {
    #
    # Warnings
    #
    ("-gnatw.a",
     "-gnatw_a",
     "-gnatwb",
     "-gnatw.b",
     "-gnatwc",
     "-gnatw.c",
     "-gnatw_c",
     "-gnatwf",
     "-gnatwg",
     "-gnatwi",
     "-gnatw.i",
     "-gnatwj",
     "-gnatwk",
     "-gnatwm",
     "-gnatw.m",
     "-gnatwp",
     "-gnatw.p",
     "-gnatw_p",
     "-gnatwq",
     "-gnatwr",
     "-gnatw.r",
     "-gnatw.t",
     "-gnatwu",
     "-gnatwv",
     "-gnatw.v",
     "-gnatww",
     "-gnatwx",
     "-gnatwy",
     "-gnatwz",
     "-gnatw.z"): "Would have no effect (already enabled by required switch -gnatwa)",
    ("-gnatwd",
     "-gnatwD"): "Enabling the warnings would disallow a common idiom in Ada that is prevalent even among Ada examples",
    "-gnatwE": "All warnings enabled by this switch are already enabled by -gnatwe",
    "-gnatw.e": 'AdaCore documentation warns that this switch is "almost certain" to cause "large numbers of useless warnings"',
    "-gnatw.g": "Entirely redundant with other warning options, and AdaCore warns that its effect may change in the future without advanced notice",
    ("-gnatw.l",
     "-gnatw.L"): "This switch merely causes the compiler to emit a list of aspects that are inherited, which is purely informational, rather than a list of things that are wrong.",
    ("-gnatw.n",
     "-gnatw.N"): "Enabling the warning would interfere with the use of Atomic variables, which some lower-level software needs to use",
    "-gnatwo": "Warnings enabled by this switch are enabled by default",
    ("-gnatw.q",
     "-gnatw.Q"): "Warnings enabled by this switch concern performance and space efficiency but not code correctness.",
    ("-gnatw.u",
     "-gnatw.U"): "Using comparisons of enumerated values is a common idiom for determining whether a given enumerated value is within a certain range of enumerated values. It should not be required that this be explicitly allowed in the definition of the enumerated type.",
    ("-gnatw.y",
     "-gnatw.Y"): "This switch controls verbose informational messages that typically do not indicate errors",
    ("-Wunused",
     "-Wuninitialized"): "Entities that are declared but not referenced, or uninitialized, from a back end perspective but not from a front end perspective are more likely to be indicative of the effects of optimizations than real errors",
}

# Taken from v2 of the GNATPro 25.2 SafetyManual
QUALIFIED_ADA_SWITCHES = set([
    "-c",
    "-fdata-sections",
    "-ffunction-sections",
    "-flto",
    "-fno-builtin",
    "-fno-jump-tables",
    "-fno-strict-aliasing",
    "-fno-tree-switch-conversion",
    "-fno-zero-initialized-in-bss",
    "-fPIC", "-fpic",
    "-fPIE", "-fpie", "-pie",
    "-ffreestanding",
    "-fstack-usage",
    "-g",
    "-mcmodel=medany",
    "-mstrict-align",
    "-param l1-cache-line-size=64",
    "-param l1-cache-size=0"
    "-param l1-cache-size=2"
    "-param l1-cache-size=4"
    "-param l1-cache-size=8"
    "-param l1-cache-size=16"
    "-param l1-cache-size=32",
    "-param l1-cache-size=64"
    "-param l1-cache-size=128"
    "-param l2-cache-size=0",
    "-param ssp-buffer-size=4"
    "-param ssp-buffer-size=8"
    "-save-temps",
    "-std=c90",
    "-std=c99",
    "-std=c11",
    "-std=gnu99",
    "-std=gnu11",
    "-MF",
    "-MMD",
    "-MP",
    "-Os",
    "-O0",
    "-O1",
    "-O2",
    "-Og",
    "-S",
    "-x",
    "-fsanitize-coverage=trace-pc",
    "-fstack-protector",
    "-fstack-protector-strong",
    "-fstack-protector-all",
    "-march=armv8-a+nofp+nosimd+pauth",
    "-march=armv8-a+crypto+pauth",
    "-mbranch-protection=pac-ret+leaf",
    "-mbranch-protection=standard",
    "-mharden-sls=all",
    "-mlittle-endian",
    "-fcallgraph-info",
    "-fcallgraph-info=su,da",
    "-gnat2022",
    "-gnata",
    "-gnatceg",
    "-gnatf",
    "-gnatn2",
    "-gnato",
    "-gnatp",
    "-gnatA",
    "-gnatVa",
    "-nostdlib",
])

REQUIRED_GNATPROVE_SWITCHES = {
    "--checks-as-errors=on": "In this process, GNATprove check messages are reviewed via diagnostic justifications, not via gnatprove output. This switch ensures that any check message will result in gnatprove not exiting without an error code.",

    "--warnings=error": "Some GNATprove warnings are used to identify potential violations of GNATprove assumptions, each of which requires manual review to ensure the violations will not lead to GNATprove false negatives. This switch ensures that any such potential violation will result in gnatprove not exiting without an error code.",

    "-U": "Without -U, GNATprove will not necessarily analyze all the units that are part of the project.",
}

BANNED_GNATPROVE_SWITCHES = {
    "--assumptions": "This switch is not safety-qualified.",
    "--clean": "This switch directs GNATprove not to attempt to prove anything.",
    "--cwe": "This switch is not safety-qualified.",
    ("--help",
     "-h"): "This switch is not safety-qualified.",
    "--list-categories": "This switch prevents GNATprove from fulfilling its intended function. This switch is also not safety-qualified.",
    ("--mode=stone",
     "--mode=check",
     "--mode=check_all"): "Would disable flow analysis and proof",
    ("--mode=bronze",
     "--mode=flow"): "Would disable proof",
    "--mode=prove": "Would siable flow analysis",
    ("--mode=gold",
     "--mode=silver"): "Though these switches are equivalent to --mode=all, they are not safety-qualified (where --mode=all is safety-qualified).",
    "--no-subprojects": "GNATprove will not necessarily analyze all of the code within each analyzed unit.",
    "--output-msg-only": "This switch is not safety-qualified.",
    "--proof": "This switch is not safety-qualified.",
    "--replay": "This switch is not safety-qualified.",
    "--version": "This switch prevents GNATprove from fulfilling its intended function. This switch is also not safety-qualified.",
    ("--warnings=off",
     "--warnings=continue"): "This switch would interfere with the effect of –warnings=error. These switches are also not safety-qualified.",
    "-f": "This switch is not safety-qualified. Note that this switch is not needed to ensure correct results.",
    "-k": "This switch is not safety-qualified.",
    "-m": "This switch is not safety-qualified.",
    "-q": "This switch is not safety-qualified. (Note however that a synonym, --quiet, is safety-qualified.)",
    "-u": "Would conflict with -U. This switch is also not safety-qualified.",
    "-v": "This switch is not safety-qualified. (Note however that a synonym, --verbose, is safety-qualified.)",
}

QUALIFIED_SPARK_SWITCHES = set([
    "--no-inlining",
    "--output-header",
    "--no-loop-unrolling",
    "--proof-warnings=on",
    "--proof-warnings=off",
    "--counterexamples=on",
    "--counterexamples=off",
    "--info",
    "--quiet",
    "--mode=all",
    "--verbose",
])


def also_qualified_gnatprove(switch):
    assert isinstance(switch, str)

    for prefix in ("--level", "--report",
                   "--memlimit", "--steps", "--timeout"):
        if switch.startswith(prefix):
            return True

    if switch.startswith("--prover="):
        prover_set = set(switch.split("=", 1)[1].split(","))
        if prover_set <= set(["altergo", "cvc5", "z3"]):
            return True

    if re.match("-j[0-9]+", switch):
        return True

    return False


REQUIRED_GNATCHECK_SWITCHES = {
    "-U": "Without -U, GNATcheck will not necessarily analyze all the units that are part of the project."
}

QUALIFIED_GNATCHECK_SWITCHES = set([
    "--show-rule",
    "--no-objects-dir",
    "--no-subprojects",
])

# Also the set of rules needs to be checked, but this is done separately
# "-from=<rule_option_filename>

BANNED_GNATCHECK_SWITCHES = {
    "--brief": "Potentially suppresses reporting of rule violations on stdout / stderr.",
    # --charset=<charset>
    # Done via fallthrough
    "--help": "Causes GNATcheck to exit without checking for violations of any of the specified rules.",
    # --ignore=<filename>
    # Done via fallthrough
    "--ignore-project-switches": "Would cause GNATcheck to ignore mandatory switches specified via the Check project in the project file.",
    # --RTS
    # Done via fallthrough
    "--simple-project": "It is not clear from the GNATcheck documentation whether this switch might cause some files in the project to be ignored by GNATcheck.",
    "--version": "Causes GNATcheck to exit without checking for violations of any of the specified rules.",
    # -files=<filename>
    # Done via fallthrough
    "-q": "Potentially suppresses reporting of rule violations on stdout / stderr."
}
