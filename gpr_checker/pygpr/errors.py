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


class Location:
    def __init__(self, filename, line=None, col=None):
        assert isinstance(filename, str)
        assert isinstance(line, int) or line is None
        assert isinstance(col, int) or col is None
        assert col is None or line is not None

        self.filename = filename
        self.line     = line
        self.col      = col

    def __str__(self):
        rv = os.path.relpath(self.filename)
        if self.line is not None:
            rv += ":%u" % self.line
            if self.col is not None:
                rv += ":%u" % self.col
            else:  # pragma: no cover
                pass
        return rv


class Error(Exception):
    def __init__(self, location, message):
        assert isinstance(location, Location)
        assert isinstance(message, str)
        super().__init__(message)
        self.location = location
        self.message  = message


class ICE(Error):
    pass


class Message_Handler:
    def __init__(self,
                 write_stdout = True,
                 write_file   = None):
        assert isinstance(write_stdout, bool)
        assert isinstance(write_file, str) or write_file is None
        assert write_stdout or isinstance(write_file, str)
        self.warnings     = 0
        self.errors       = 0
        self.issues       = {}
        self.write_stdout = write_stdout
        try:
            # pylint: disable=consider-using-with
            self.write_file = (open(write_file, "w", encoding="UTF-8")
                               if write_file
                               else None)
        except OSError:  # pragma: no cover
            # Not really a realistic test case, but also ruled out in
            # the safety manual
            print("error: cannot open output file %s for writing" % write_file)
            sys.exit(1)

    def __del__(self):
        if self.write_file is not None:  # pragma: no cover
            self.write_file.close()

    def write(self, line):
        assert isinstance(line, str) and len(line) >= 1
        if self.write_stdout:
            print(line)
        if self.write_file is not None:
            self.write_file.write(line + "\n")

    def write_blank_line(self):
        if self.write_stdout:
            print()
        if self.write_file is not None:
            self.write_file.write("\n")

    def emit(self, location, kind, message, check_id, fatal):
        assert isinstance(location, Location)
        assert kind in ("info", "warning", "error", "issue", "ice")
        assert isinstance(message, str) and "\n" not in message
        assert isinstance(check_id, str) or check_id is None
        assert isinstance(fatal, bool)

        msg = "%s: %s: %s" % (location, kind, message)
        if check_id is not None:
            msg += " [%s]" % check_id

        self.write(msg)

        if fatal:
            raise Error(location, msg)

    def info(self, location, message):
        self.emit(location = location,
                  kind     = "info",
                  message  = message,
                  check_id = None,
                  fatal    = False)

    def warning(self, location, message):
        self.warnings += 1
        self.emit(location = location,
                  kind     = "warning",
                  message  = message,
                  check_id = None,
                  fatal    = False)

    def error(self, location, message, fatal=True):
        self.errors += 1
        self.emit(location = location,
                  kind     = "error",
                  message  = message,
                  check_id = None,
                  fatal    = fatal)

    def issue(self, location, message, check_id):
        self.issues[check_id] = self.issues.get(check_id, 0) + 1
        self.emit(location = location,
                  kind     = "issue",
                  message  = message,
                  check_id = check_id,
                  fatal    = False)

    def ice_loc(self, location, message):
        self.errors += 1
        self.emit(location = location,
                  kind     = "ice",
                  message  = message,
                  check_id = None,
                  fatal    = False)
        raise ICE(location, message)
