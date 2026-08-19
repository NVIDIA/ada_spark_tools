<!--
SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION &
                        AFFILIATES. All rights reserved.
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Requirements and Traceability

We use [TRLC](https://github.com/bmw-software-engineering/trlc) to
record requirements and
[LOBSTER](https://github.com/bmw-software-engineering/lobster) to
create the traceability report.

High-level requirements are captured in the [Requirements TRLC
file](requirements.trlc).

The system test suite contains `tracing` files for some tests. This
file contains named requirements, e.g:

```
required_pragmas
```

This test would be linked to `Requirements.required_pragmas`. A test
without a `tracing` file is deemed to be not directly linked to
safety-related features of GPR Checker.

The script to extract the information from the test-suite is
[lobster-system-test.py](../util/lobster-system-test.py). We directly
emit the [LOBSTER Interchange
format](https://github.com/bmw-software-engineering/lobster/blob/main/documentation/schemas.md)
for activities (i.e. tests).

## Missing tests/tracing

- [ ] exit_code (requires test infra changes to record exit code)
- [ ] banned_compiler_switches
- [ ] banned_gnatprove_switches
- [ ] banned_gnatcheck_switches
