<!--
SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION &
                        AFFILIATES. All rights reserved.
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Copyright notice
Most tests are taken from
[gnatcheck testsuite](https://github.com/AdaCore/langkit-query-language/tree/25.2/testsuite/tests/gnatcheck/lkql_rules_config).

These can be recognised by their name, all of which are 32-character
hex strings (when importing them we flattened the directory structure,
and since many files have the same name we just renamed them to their
`md5sum`).

All other files with human readable names are hand-written by NVIDIA
to close coverage gaps in the parser or example files for the rules
the SPARK process requires.
