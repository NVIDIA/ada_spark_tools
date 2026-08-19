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

import argparse
import json
import os

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("test_dir")

    options = ap.parse_args()

    tests = [entry.name
             for entry in os.scandir(options.test_dir)
             if entry.is_dir()]
    tests.sort()

    data = []

    for test in tests:
        trace_file = os.path.join(options.test_dir, test, "tracing")
        refs = []
        just_up = []
        if os.path.isfile(trace_file):
            with open(trace_file, "r", encoding="UTF-8") as fd:
                refs = ["req Requirements." + line.strip()
                        for line in fd
                        if line.strip]
        else:
            just_up.append("test is not related to certified features")
        info = {
            "location" : {
                "kind"   : "file",
                "file"   : os.path.abspath(os.path.join(options.test_dir,
                                                        test,
                                                        "test.gpr")),
                "line"   : None,
                "column" : None,
            },
            "tag"         : "test %s" % test,
            "name"        : "System test %s" % test.replace("-", " "),
            "refs"        : refs,
            "just_up"     : just_up,
            "just_down"   : [],
            "just_global" : [],
            "framework"   : "GPR Parser System Test",
            "kind"        : "test",
            "status"      : "ok",
        }
        data.append(info)


    data = {
        "generator" : "lobster-gpr-checker-system-tests",
        "schema"    : "lobster-act-trace",
        "version"   : 3,
        "data"      : data,
    }

    with open("system-tests.lobster", "w", encoding="UTF-8") as fd:
        json.dump(data, fd)

if __name__ == "__main__":
    main()
