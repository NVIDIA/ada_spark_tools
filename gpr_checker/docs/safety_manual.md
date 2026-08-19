<!--
SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION &
                        AFFILIATES. All rights reserved.
SPDX-License-Identifier: GPL-3.0-or-later
-->

# GPR Checker Safety Manual

## Purpose

The GPR Checker reads a `.gpr` file and can check it against the
[SPARK Process](https://github.com/NVIDIA/spark-process) (and AdaCore
safety manuals).

The tool is a stand-alone Python program with no run-time
dependencies.

## Scope

This document is the Safety Manual (SM) of the qualification material
being developed for automotive ISO-26262 standard certification
[R1]. It provides usage and constraints information concerning the use
of GPR Checker in accordance of the TCL3/ASIL-D level of the ISO-26262
standard.

## Terms, Definitions and Abbreviations

For the purpose of this qualification, the terms, definitions and
abbreviated terms from the ISO 26262 standard apply. Additional terms
specific to the current qualification are listed in [I1] and
below. Further terms and abbreviations are described in Glossary Of
Terms for ISO 26262 Projects (ref. SE.DOC-473) [R1].

## Input Documents

| ID | Document Title | Revision | Location               |
|:---|:---------------|:---------|:-----------------------|
| I1 | GPR Checker UG | 1.2.0    | [Link](user_manual.md) |

## Reference Documents

| ID | Document Title                              | Revision | Location                                               |
|:---|:--------------------------------------------|:---------|:-------------------------------------------------------|
| R1 | ISO-26262: Road Vehicle - Functional Safety | 2018     | [Link](https://www.iso.org/publication/PUB200262.html) |

## Environment

The GPR Checker is qualified in GNU/Linux environments.

The tool must be installed as described in [I1].

## Responsibility
According to the clause 11.4.2 of [R1] part 8, the user shall verify
the validity of the predetermined TCL prior to the use of this
software tool in a safety-related development.  Furthermore, according
to the clause 11.4.3 of [R1] part 8, the user shall ensure the usage,
the environment and the functional constraints of this software tool
comply with its evaluation criteria or its qualification.

## Tools Identification
This safety manual is only applicable to GPR Checker 1.2.0 tool.

## Tool Options

### Mandatory switches

There are two mandatory switches:

| Switch       | Description                          |
|:-------------|:-------------------------------------|
| `--validate` | Enables checking of GPR files.       |
| `--verbose`  | Emits detailed report of compliance. |

### Optional switches

The following switches are also qualified:

| Switch                        | Description                                        |
|:------------------------------|:---------------------------------------------------|
| `--additional-gprbuild-flag`  | Used to indicate additional build flags.           |
| `--additional-gnatprove-flag` | Used to indicate additional SPARK flags.           |
| `--additional-gnatcheck-flag` | Used to indicate additional GNAT Check flags.      |
| `--save-log`                  | Can be used to also write a report.                |
| `-X`                          | Can be used to specify the value of a GPR variable |

### Prohibited switches

All other switches are prohibited.

## Assumptions of use

### AOU 1 (legal input)
It is assumed that the checked GPR file is syntactically and
semantically legal as far as `gprbuild`, `gnatcheck`, and `gnatprove`
are concerned.

Running these tools in CI, before or after GPR Checker is invoked, and
checking its exit status is sufficient to meet this obligation.

### AOU 2 (full context available)
Since not all mandatory switches can be placed in the GPR file (for
example the `-U` switch for SPARK), the actual SPARK invocation will
look something like this:

```
gnatprove -P project.gpr -U
```

To make sure GPR Checker knows about the actual switches used, the
build system (or user) must provide these additional switches to GPR
Checker using the following switches:

* `--additional-gprbuild-flag` (for command-line flags provided to
  `gprbuild`)
* `--additional-gnatprove-flag` (for command-line flags provided to
  `gnatprove`)
* `--additional-gnatcheck-flag` (for command-line flags provided to
  `gnatcheck`)

For example, a full invocation might look like this:

```
validator.py project.gpr \
  --validate \
  --additional-gnatcheck-flag=-U \
  --additional-gnatprove-flag=-U \
  --additional-gprbuild-flag=-nostdlib
```

### AOU 3 (pragma skip)

The [pragma skip file](user_manual.md#pragma-skip-file) feature must
not be used on the main file to be checked, since it just disables
analysis.

It may be used if you want perform modular analysis in a large tree of
GPR files; but it is your responsibility to make sure everything is
analysed at the end of the day.

## Tool Results Interpretation

Refer to section [Return Codes](user_manual.md#return-codes) in [I1].

## Limitations

The tool does not support the full feature set of the GPR
language. The user manual documents these
[limitations](user_manual.md#gpr-features). In any case the tool will
abort with a non-zero return code if such a feature is encountered.

## Known Problems

None.
