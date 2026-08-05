<!--
SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION &
                        AFFILIATES. All rights reserved.
SPDX-License-Identifier: GPL-3.0-or-later
-->

# GPR Checker User Manual

## Installation

There are two ways to use the GPR Checker.

1. Direct use from this repository. Just clone the repo and use the
   top-level `validator.py` script.

2. (In the future: from PyPI)

## Use

To invoke the GPR Checker simply provide a GPR file:

```
validator.py foo.gpr
```

Several command-line options exist:

* `--validate` is the most important option. This checks the GPR file
  against the SPARK Process and AdaCore safety manuals for compliance.

* `-X name=value` defines an external variable, similar to GPR Build.

* `--additional-gprbuild-flag FLAG`, `--additional-gnatprove-flag
  FLAG`, and `--additional-gnatcheck-flag FLAG`. These options can be
  specified multiple times and should mirror the flags for these
  tools. The primary use-case is the `-U` flag for e.g. SPARK, which
  is required by the process, but cannot be specified in a GPR file
  itself. If your build system adds switches on the command-line
  beyond the ones specified in the `.gpr` files, you must invlude them
  here with these options.

* `--verbose` creates a more detailed output, which is only
  interesting if you also use `--validate`. By default you just get a
  list of violations, for example:

  ```
  massive.adc: warning: could not find correct definition for user aspect Forward_Progress [2.3.1]
  test.gpr:1:8: issue: project requires a Compiler package [2.2.3]
  test.gpr:1:8: issue: project requires a Prove package [4.2.4]
  test.gpr:1:8: issue: project requires a Check package [4.3.3]
  test.gpr:1:8: issue: zero gnatcheck rules are enabled [4.3.4]
  test.gpr:1:8: issue: Test does not define a Runtime [2.2.2]
  test.gpr:1:8: issue: Test does not define a Target [2.2.2]
  ```

  In verbose mode we also create a summary for each category and a
  positive statement if something complies:

  ```
  =============================================
  = GPR Validator (VERSION) Report for test.gpr =
  =============================================
  1 file(s) checked:
  * test.gpr

  Checklist items fully checked:
  * 2.2.2 (gpr project correctly configured              ): 2 findings
  * 2.2.3 (gpr compiler package correctly configured     ): 1 findings
  * 2.2.4 (gpr prove package does not use banned switches): VERIFIED
  * 2.2.5 (gpr check package does not use banned switches): VERIFIED
  * 2.2.6 (no non-safety qualified switches used         ): VERIFIED
  * 2.3.1 (forward_progress is correctly configured      ): VERIFIED

  Checklist items partially checked:
  * 4.2.4 (all required gnatprove switches used          ): 1 findings
  * 4.3.3 (all required gnatcheck switches are used      ): 1 findings
  * 4.3.4 (all required gnatcheck rules are enabled      ): 1 findings

  Overall verdict: NON COMPLIANT
  ```

* `--write-json FILE` can be used to dump the information in the GPR
  file as a JSON file. You could use this to implement additional
  tools that consume GPR files.

* `--save-log FILE` also writes findings to the specified file (as
  well as standard output).

* `--no-std-output` disables messages on stdout.

* `--version` show the tool version and exit.

## Checks

The tool can enforce these checks when using the `--validate` option.

### Checklist items for GPR Checker

#### 2.2.2 (implemented)
Does each unit GPR file (combined with any other GPR files recursively
included via with keywords) do all the following?

* Set attributes `Runtime("Ada")`, `Target`, and
  `Builder'Global_Configuration_Pragmas`, with values that satisfy the
  restrictions specified by the
  [Create_Project_File](https://nvidia.github.io/spark-process/process/process/unit-design.html#create-project-file)
  step

  Note: The permitted runtimes and targets can be set in
  [switches.py](../pygpr/switches.py).

* Refrain from including a `Naming` package

#### 2.2.3 (implemented)
Does each unit GPR file (combined with any other GPR files recursively
included via with keywords) include a Compiler package that specifies
switches that comply with all the following?

* The Requirements Concerning Compiler Warning Switches section

* The Requirements Concerning Non-Warning-Related Compiler Switches
  section

* Any restrictions in the Ada/SPARK Guidelines concerning style
  checking switches

#### 2.2.4 (implemented)
Does each unit GPR file (combined with any other GPR files recursively
included via with keywords) with a Prove package refrain from
specifying any GNATprove switches prohibited by the Requirements
Concerning GNATprove Switches section?

> Note: the tool is stricter here than the wording implies. It will
> require you to have a Prove package. Otherwise how could you make
> sure you specify the required switches?

#### 2.2.5 (implemented)
Does each unit GPR file (combined with any other GPR files recursively
included via with keywords) with a Check package refrain from
specifying any GNATcheck switches prohibited by the Requirements
Concerning GNATcheck Switches and Rules section?

> Note: the tool is stricter here than the wording implies. It will
> require you to have a Check package. Otherwise how could you make
> sure you specify the required switches?

#### 2.2.6 (implemented)
Does each unit GPR file (combined with any other GPR files recursively
included via with keywords) avoid all non-safety-qualified tool
switches in the Compiler, Prove, and Check packages?

#### 2.3.1 (implemented)
For each unit GPR file (combined with any other GPR files recursively
included via with keywords), does the ADC file specified by the
`Builder'Global_Configuration_Pragmas` attribute contain the exact
definition of the `Forward_Progress` user aspect specified in the
Create_Configuration_Pragmas step?

```ada
pragma User_Aspect_Definition (Forward_Progress,
    Local_Restrictions (No_Secondary_Stack, No_Heap_Allocations),
    Always_Terminates);
```

#### 2.5.1 (not implemented yet)
For each internal package identified in the Software Unit Verification
Plan, is the corresponding internal ADS file included in at least one
of the unit GPR files (whether it is included directly or via the
containing directory?)

#### 3.1.2 (not implemented yet)
For each non-nested package implemented by the unit which requires a
package body, is the corresponding ADB file included in at least one
of the unit GPR files (whether it is included directly or via the
containing directory)?

### Checks requiring cooperation from your build system

Only you and your build system can ensure these, since `gprbuild` /
`gnatprove` can be supplied with additional switches on the
command-line. GPR Checker can check the set of switches in the GPR
file is OK, but if you add additional switches on the command-line you
need to check at that point as well.

#### 4.2.4 (implemented)
Does the combination of switches in the Prove package in the unit GPR
file and the switches on the gnatprove command line collectively
include all the switches required by the Requirements Concerning
GNATprove Switches section?

#### 4.3.3 (implemented)
Does the combination of switches in the Check package in the unit GPR
file and the switches on the gnatcheck command line collectively
include all the switches and enable all the rules required by the
Requirements Concerning GNATcheck Switches and Rules section?

#### 4.3.4 (implemented)
Does the combination of switches in the Check package in the unit GPR
file and the switches on the gnatcheck command line collectively
enable all the rules required by the Ada/SPARK Guidelines?

#### 4.13.4 (implemented)
Does the combination of switches in the Prove package in the test GPR
file and the switches on the gnatprove command line collectively
include all the switches required by the Requirements Concerning
GNATprove Switches section?

## Return codes

The GPR Checker has two return codes:

* `0` - no errors or findings (but there might be warnings). When used
  with `--validate` then this implies that your GPR file conforms to
  the SPARK Process and AdaCore safety manuals.

* `1` - at least one error or finding was emitted, i.e. your GPR file
  does not conform (or it contains syntax errors).

* `2` - internal tool error, please bug report it

## Conditional evaluation

GPR can include conditional paths using the case statement. The way
this is done in the GPR Checker is simple:

* We constant fold everything.
* If we get an external reference you need to provide it on the
  command-line (using `-X`, just like with `gprbuild`).
* If we get an external reference with a default and you didn't
  specify it on the command-line we use the default but emit a warning.

In the future we could extend this to do symbolic execution and reason
about all possible evaluations. But for now this is overkill.

## GPR Features

Not all features from GPR files are supported.

- [x] with clause, including limited with
- [ ] specifying additional includes on the command-line
- [ ] project extensions
- [x] enumerations (typed string declarations)
- [x] packages
  - [x] direct packages
  - [ ] renamed packages
  - [ ] extended packages
- [x] variables
- [x] attributes
- [x] case statements
- [x] null statements
- [x] expressions
  - [x] variable references (without qualifiers)
  - [ ] variable references (with qualifiers)
  - [ ] attribute references
- [ ] builtin functions
  - [ ] `alternative` function
  - [ ] `default` function
  - [x] `external` references (with and without default)
  - [ ] `external_as_list` references
  - [ ] `filter_out` function
  - [ ] `item_at` function
  - [ ] `lower` function
  - [ ] `match` function
  - [ ] `remove_prefix` function
  - [ ] `remove_suffix` function
  - [ ] `split` function
  - [ ] `upper` function

## Specification

The official spec is here:
https://docs.adacore.com/gprbuild-docs/html/gprbuild_ug/project_file_reference.html

I am using a [simplified / fixed grammar](grammar_gpr.md) because the
original one is a bit odd and contains a few errors. Also note that
the grammar contains a few extensions which are described below.

## Pragmas

The GPR checker assigns special meaning to some comments starting with
`gpr_checker:`. These pragmas are described below.

### Pragma: Skip File

Sometimes projects should not generate any error messages (which we
already automatically do for externally built projects). To skip
analysis of a project you can place a `skip file` pragma somewhere in
the preamble comments, for example:

```gpr
--  This is an example
--  gpr_checker: skip file: potato reason
--  More comments

project Test is
end Test;
```

The given reason will be quited by the tool later, for example:

```
test.gpr:5:9: info: skipping validation of Test: potato reason
```

Please note that this pragma only disables *validation*, the file
itself is still parsed and so syntax error may still be prodiced.
