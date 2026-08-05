<!--
SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION &
                        AFFILIATES. All rights reserved.
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Contributing to GPR Checker

If you are interested in contributing to the __Ada/SPARK Tools__, your
contributions will fall into three categories:

1. You want to report a bug, feature request, or documentation issue

    - File an [issue](https://github.com/NVIDIA/ada_spark_tools/issues/new)
      describing what you encountered or what you want to see changed.

    - Please note the version and origin of the Ada/SPARK tools you
      are using, your operating system, and the version of your
      Python.

    - The GPR Checker team will evaluate the issues and triage them,
      scheduling them for a release. If you believe the issue needs
      priority attention comment on the issue to notify the team.

1. You want to propose a new feature and implement it

    - Post about your intended feature, and we shall discuss the
      design and implementation.

    - Once we agree that the plan looks good, go ahead and implement
      it, using the [code contributions](#code-contributions) guide
      below.

1. You want to implement a feature or bug-fix for an outstanding issue

    - Follow the [code contributions](#code-contributions) guide below.

    - If you need more context on a particular issue, please ask and
      we shall provide.

## Code contributions

### Your first issue

1. Read the project's README.md to learn how to setup the development
   environment.

1. Find an issue to work on. The best way is to look for the
   [good first issue](https://github.com/NVIDIA/ada_spark_tools/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22good%20first%20issue%22) label.

1. Comment on the issue saying you are going to work on it.

1. Code! Make sure to update unit tests and complete code coverage.

1. When done, create your pull request.

1. Verify that CI passes and fix if needed.

1. Wait for other developers to review your code and update code as
   needed.

1. Once reviewed and approved, a GPR Checker developer will merge your
   pull request.

Remember, if you are unsure about anything, don't hesitate to comment
on issues and ask for clarifications!

### Signing Off Your Work

We require that all contributors "sign-off" on their commits. This
certifies that the contribution is your original work, or you have
rights to submit it under the same license, or a compatible license.

* Any contribution which contains commits that are not Signed-Off will
  not be accepted.

* To sign off on a commit you simply use the `--signoff` (or `-s`)
  option when committing your changes:

  ```bash
  $ git commit -s -m "Add cool feature."
  ```

  This will append the following to your commit message:

  ```
  Signed-off-by: Your Name <your@email.com>
  ```

* Full text of the DCO (https://developercertificate.org/):

  ```
    Developer Certificate of Origin
    Version 1.1

    Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

    Everyone is permitted to copy and distribute verbatim copies of this
    license document, but changing it is not allowed.


    Developer's Certificate of Origin 1.1

    By making a contribution to this project, I certify that:

    (a) The contribution was created in whole or in part by me and I
        have the right to submit it under the open source license
        indicated in the file; or

    (b) The contribution is based upon previous work that, to the best
        of my knowledge, is covered under an appropriate open source
        license and I have the right under that license to submit that
        work with modifications, whether created in whole or in part
        by me, under the same open source license (unless I am
        permitted to submit under a different license), as indicated
        in the file; or

    (c) The contribution was provided directly to me by some other
        person who certified (a), (b) or (c) and I have not modified
        it.

    (d) I understand and agree that this project and the contribution
        are public and that a record of the contribution (including all
        personal information I submit with it, including my sign-off) is
        maintained indefinitely and may be redistributed consistent with
        this project or the open source license(s) involved.
  ```

### Managing PR labels

Each PR must be labeled if it is a "backwards-incompatible" change
(using Github labels). This is used to highlight changes that users
should know about when upgrading.

For GPR Checker, a "backwards-incompatible" change is any that would
flag previously correctly accepted GPR files as violating rules. Note
that a previously incorrecttly accepted GPR files (e.g. a missing or
broken check fails to flag it) is not a backwards-incompatible
change. It's a bug fix.

## Attribution

Portions adopted from
https://github.com/NVIDIA-GitHub-Management/PLC-OSS-Template/blob/main/CONTRIBUTING.md
