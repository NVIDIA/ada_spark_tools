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

VERSION_TUPLE = (1, 2, 0)
VERSION_SUFFIX = ""

PYGPR_VERSION = ("%u.%u.%u" % VERSION_TUPLE) + \
    ("-%s" % VERSION_SUFFIX if VERSION_SUFFIX else "")

FULL_NAME = "GPR Checker %s" % PYGPR_VERSION

PROJECT_URL = "https://github.com/NVIDIA/ada_spark_tools"
BUGS_URL = "%s/issues" % PROJECT_URL
DOCS_URL = "%s/blob/main/gpr_checker/README.md" % PROJECT_URL
CODE_URL = PROJECT_URL
