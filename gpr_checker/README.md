<!--
SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION &
                        AFFILIATES. All rights reserved.
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Python GPR File Parser

Enforce [SPARK Process](https://github.com/NVIDIA/spark-process)
requirements on `.gpr` files.

## Overview

This is an independent framework to parse GNAT Project Files, as used
by SPARK and various other AdaCore tools. There are three goals:

* A (pure, zero dependency) Python API to build additional tools.
* A converter to spit out the concrete values of a GPR file in JSON
  (an alternative to the above, use the `--write-json` option).
* A static checker for the GPR files enabled with `--validate` so we
  can make sure we're following the safety manuals when it comes to
  switches.

## Getting Started

You can run the tool directly from a clone of this repository.

```bash
export PATH=${PATH}:/path/to/this/repo/gpr_checker
$ validator.py --validate my_spark_project.gpr
```

## Requirements

For running the tool you just need Python 3.11 or later.

For development (specifically running the test-suite) you need Linux
and several Python packages. You can install everything like so:

```bash
$ pip3 install -r requirements.txt
```
## Documentation

* [User Manual](docs/user_manual.md)
* [Roadmap](ROADMAP.md)
* [Changelog](CHANGELOG.md)

## Development quick-start

* Install development dependencies as described above
* Run linters: `make lint`
* Run the test-suite: `make test`, coverage report can be found in
  `htmlcov/index.html`; test status can be judged with `git diff`

# License

This project is licensed under the GPLv3 - see the
[LICENSE](../LICENSE) file for details.

While all code is (C) NVIDIA, a part of the [test-suite for the LKQL
parser](test-lkql-parser) is taken from the [gnatcheck
repository](https://github.com/AdaCore/langkit-query-language). The
[README.md](test-lkql-parser/README.md) explains which files from the
gnatcheck test-suite, and which files have been created by NVIDIA. See
[third party notices](THIRD-PARTY-NOTICES) for details.
