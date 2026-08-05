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

TARGETS=$(addsuffix .out, $(basename $(wildcard *.gpr) $(wildcard *.adc)))
export PYTHONPATH=..

all: $(TARGETS)

%.out: %.gpr
	-coverage run -p --rcfile=../coverage.cfg --branch \
		--data-file ../.coverage \
		-m pygpr.lexer $< > $@ 2>&1

%.out: %.adc
	-coverage run -p --rcfile=../coverage.cfg --branch \
		--data-file ../.coverage \
		-m pygpr.lexer $< > $@ 2>&1
