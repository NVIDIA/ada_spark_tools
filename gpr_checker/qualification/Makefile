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

HEAD=$(shell git rev-parse HEAD)
REMOTE=https://github.com/NVIDIA/ada_spark_tools

.PHONY: system-tests.lobster

all: lobster_report.html lobster_online_report.html
	lobster-ci-report report.lobster

lobster_report.html: report.lobster
	lobster-html-report

lobster_online_report.html: online.report.lobster
	lobster-html-report --out=$@ online.report.lobster

report.lobster: lobster.conf requirements.lobster system-tests.lobster
	lobster-report --lobster-config=lobster.conf

online.report.lobster: report.lobster
	lobster-online-report-nogit \
		--repo-root=../.. \
		--remote-url=$(REMOTE) \
		--commit=$(HEAD) \
		--out=$@ \
		report.lobster

requirements.lobster: lobster-trlc.yaml requirements.rsl requirements.trlc
	lobster-trlc --out=$@ --config=lobster-trlc.yaml .

system-tests.lobster:
	../util/lobster_system_test.py ../test-system
