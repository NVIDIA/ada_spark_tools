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
import sys
import multiprocessing
import subprocess
import shutil

REPO_ROOT_DIR = os.path.abspath("..")
TEST_ROOT_DIR = os.getcwd()

def execute_test(test):
    os.chdir(os.path.join(TEST_ROOT_DIR, test))

    coverage_cmd = [
        "coverage",
        "run",
        "-p",
        "--rcfile=%s" % os.path.join(REPO_ROOT_DIR, "coverage.cfg"),
        "--branch",
        "--data-file", os.path.join(REPO_ROOT_DIR, ".coverage")
    ]
    validator_cmd = [
        os.path.join(REPO_ROOT_DIR, "validator.py"),
        "test.gpr",
        "--no-version-in-report",
        "--validate",
    ]

    if os.path.isfile("options"):
        with open("options", "r", encoding="UTF-8") as fd:
            validator_cmd += [option.strip()
                              for option in fd.read().split()
                              if option.strip()]

    output_files = ("output",
                    "output.verbose",
                    "output.verbose.check",
                    "output.json")
    temp_files = ("output.verbose.check",)

    for file_name in output_files:
        if os.path.exists(file_name):
            os.unlink(file_name)

    test_status = True
    reason      = None

    return_codes = {}
    for file_name in output_files:
        cmd = coverage_cmd + validator_cmd
        match file_name:
            case "output":
                pass
            case "output.verbose":
                cmd.append("--verbose")
            case "output.verbose.check":
                cmd.append("--verbose")
                cmd.append("--no-std-output")
                cmd.append("--save-log=%s" % file_name)
            case "output.json":
                cmd.append("--write-json=%s" % file_name)

        r = subprocess.run(cmd,
                           stdout   = subprocess.PIPE,
                           stderr   = subprocess.STDOUT,
                           check    = False,
                           encoding = "UTF-8")

        return_codes[file_name] = r.returncode
        match r.returncode:
            case 0:
                status = "COMPLIANT"
            case 1:
                status = "NON COMPLIANT"
            case 2:
                status = "ICE"
            case _:
                status = "UNEXPECTED RETURN %i" % r.returncode

        match file_name:
            case "output" | "output.verbose":
                with open(file_name, "w", encoding="UTF-8") as fd:
                    fd.write("Exit code: %s\n\n" % status)
                    fd.write(r.stdout)
            case "output.verbose.check":
                with open("output.verbose", "r", encoding="UTF-8") as fd:
                    lines_a = fd.read().splitlines()[2:]
                with open("output.verbose.check", "r", encoding="UTF-8") as fd:
                    lines_b = fd.read().splitlines()
                if lines_a != lines_b:
                    test_status = False
                    reason      = "differing saved/stdout output"
                    break
            case "output.json":
                pass

    all_status = set(return_codes.values())
    if len(all_status) != 1:
        test_status = False
        reason      = "differing return codes"

    if test_status:
        for file_name in temp_files:
            if os.path.exists(file_name):
                os.unlink(file_name)

    if test_status:
        print("%-*s: PASS" % (40, test))
    else:
        print("%-*s: FAIL [%s]" % (40, test, reason))

    return test_status, reason


def main():
    tests = [item.name
             for item in os.scandir()
             if item.is_dir()]

    pool = multiprocessing.Pool()
    success = True
    for status, reason in pool.imap_unordered(execute_test, tests):
        success &= status

    if success:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
