<!--
SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION &
                        AFFILIATES. All rights reserved.
SPDX-License-Identifier: GPL-3.0-or-later
-->

# GPR Validator Release Notes

## Language support

Intended to be up-to-date with release 25.2 of the AdaCore tools.

## Limitations

Several language features of the gpr language are not
supported. Please see the [user manual](docs/user_manual.md) for more
information.

## Changelog

### 1.2.0 (2026-06-05)

* Note: This release is backwards-incompatible to the previous
  version, mainly due to the GNAT SAS changes.

* Proper support for 25.2, including updates of all required/allowed
  switches for the new safety manuals.

* Fix pluralisation of "1 findings" -> "1 finding".

* Fix possible tool crash when the name of the supplied runtime is
  really wrong.

* [GCC] Add a few new qualified switches (`-fstack-protector`,
  `-fstack-protector-all`, `-mbranch-protection=standard`).

* [GCC] Fixed too broad acceptance of `-std`, it is now limited to
  `c90`, `c99`, `c11`, `gnu99`, and `gnu11`.

* [SAS] Support new-style LKQL configuration files for GNAT Check. You must
  now use `--rule-file=foo.lkql` or the `Rule_File` project attribute.

* [SAS] Remove support for the old `+R`, `-rules`, and `-from` options
  to control rules. Only the new-style LKQL rules are supported, in
  line with the new safety manual.

* [SAS] Switch `--check-redefinition` is no longer qualified.

* [SAS] Trimmed required rule set. Now we basically only require three
  forbidden pragmas and goto statements (in Ada code).

* [SPARK] Removed `--output=` from the list of qualified switches.

* [SPARK] Added `--no-inlining`, and `--no-loop-unrolling` VCG
  switches to the qualified set.

* [SPARK] Added `--proof-warnings=on` VCG switch to the qualified set.

* [SPARK] Added `--output-header`, and `--report=` to the qualified
  set.

### 1.1.7 (2025-09-08)

* Also add new target `riscv32-elf` for GNAT 25.x.

### 1.1.6 (2025-08-27)

* Add new target `riscv64-elf` for GNAT 25.x.
* Add `-nostdlib` to the set of certified options.
* Permit any runtime if `-nostdlib` is set.

### 1.1.5 (2025-03-24)

* Support `+R` options with instance names, e.g. `+R:foo:my_rule`.

* Ban `+R`from the command-line, but allow it in rules files.

* Remove two switches (`-eL` and `--check-semantics`) as they were
  never qualified.

### 1.1.4 (2025-03-14)

* Support `+R` options with lists, e.g. `+R
  Forbidden_Pragmas:Validity_Checks,Assertion_Policy,Ignore_Pragma`. The
  new GNAT Check 25.1 requires this format now (instead of allowing
  you to specify each option separately).

* Fix bug (spurious parse errors) when processing files without
  trailing new-line.

### 1.1.3 (2025-02-14)

* No changes (except for copyright dates)

### 1.1.2 (2025-02-14)

* Change spelling of allowed rule `--show-rules` to `--show-rule`.

### 1.1.1 (2024-08-05)

* Add `-gnatep`, `-gnatec`, `-gnatR`, and the `--RTS` switch to the
  qualified list.

### 1.1.0 (2024-07-31)

This version contains backwards-incompatible changes in tool
behaviour.

* We now just print error messages instead of a full report. Add a
  new switch `--verbose` that restores the previous behaviour.

* Downgrade warning message about default values for environment
  variables to an info message.

### 1.0.10 (2024-07-19)

* Add compiler switch `-gnateD<definition>` to the set of qualified
  switches.

### 1.0.9 (2024-06-12)

* New switches `--additional-permitted-target` and
  `--additional-permitted-runtime` which allow you to allow additional
  targets or runtimes, beyond what the safety manuals permit.

### 1.0.8 (2024-05-19)

* Fix parsing of `pragma Interrupt_State` which can be found in global
  pragma files.

### 1.0.7 (2024-05-19)

* Fix parsing of empty parameter lists.

### 1.0.6 (2024-05-06)

* Add new options to control output: `--no-std-output` and
  `--save-log`.

### 1.0.5 (2024-03-05)

* Add method to skip validation of projects using a special pragma
  comment.

### 1.0.4 (2024-02-02)

* Fix correct form of `--checks-as-errors` (should be
  `--checks-as-errors=on`).

### 1.0.3 (2024-02-01)

* Downgrade missing forward_progress into warning due to a bug in
  GNAT. (Retroactive note: this is fixed since 2024-02-26)

### 1.0.2 (2024-02-01)

* Remove 5 rules from the required GNATcheck rules due to process
  changes.

* Add `aarch64-nto-qnx` as an allowed target.

### 1.0.1 (2024-02-01)

* Fixed a typo in the expected definition for `Forward_Progress`.

* Add three new options intended to also allow checking of
  command-line parameters: `--additional-gprbuild-flag`,
  `--additional-gnatprove-flag"`, and `--additional-gnatcheck-flag`.

* Fix treatment of `-j` (it now also allows e.g. `-j0` or `-j8`, etc.)

* Add several GNATcheck switches to the allowed set.

### 1.0.0 (2024-01-24)

* Initial release.
