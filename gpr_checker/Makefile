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

.PHONY: style lint test

all: lint test

lint: style
	@python3 -m pylint --rcfile=pylint3.cfg \
		--reports=no \
		--score=no \
		pygpr validator.py

style:
	@python3 -m pycodestyle pygpr validator.py --exclude=pygpr/switches.py --max-line-length=82

test:
	find test-system -name "output*" -delete
	find test-gpr-lexer -name "*.out" -delete
	find test-lkql-parser -name "*.out" -delete
	make -B -C test-system
	make -B -C test-gpr-lexer -j20
	make -B -C test-lkql-parser -j20
	coverage combine -q
	coverage html --rcfile=coverage.cfg
	coverage report --rcfile=coverage.cfg --fail-under=100 -m

gnatcheck-behaviour:
	find gnatcheck-behaviour-analysis -name "output*" -delete
	make -B -C gnatcheck-behaviour-analysis
