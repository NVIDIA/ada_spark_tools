<!--
SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION &
                        AFFILIATES. All rights reserved.
SPDX-License-Identifier: GPL-3.0-or-later
-->

# LKQL

GNAT Check 25.2 and later uses a new configuration mechnanism for
rules. A key advantage is that we can now specify rules that only
apply to e.g. Ada code. The language used to specify the configuration
files is full LKQL, including an `include` mechanism.

GPR Checker supports only a subset of this language, sufficient to
express the way we write our rule file.

# Language

## Tokens

```bnf
COMMENT ::= #.*

IDENTIFIER ::= [a-zA-Z][a-zA-Z0-9_]*

STRING ::= "(\\.|[^\"])*"

INTEGER ::= [0-9]+
```

There are also several punctuation tokens:

* `.` (dot)
* `...` (ellipsis)
* `?.` (question dot)
* `?[` (qestion bracket)
* `,` (comma)
* `;` (semicolon)
* `:` (colon)
* `_` (underscore)
* `!!` (double exclamation)
* `=` (assignment)
* `==` (equality)
* `!=` (inequality)
* `<`, `<=`, `>`, `>=` (comparison)
* `+`, `-`, `*`, `/`, `&` (operators)
* `@` (at)
* `|` (bar)
* `<-` (left arrow)
* `=>` (right arrow)
* `<>` (box)
* `(`, `)`, `[`, `]`, `{`, `}` (brackets)

## Grammar

This grammar is a simplified version of the [official grammar](https://github.com/AdaCore/langkit-query-language/blob/master/lkql/lkql.lkt).

The key restrictions we impose are "no includes" and "nothing other
than object declarations".

```
compilation_unit ::= {statement}

statement ::= value_declaration

value_declaration ::= 'val' IDENTIFIER '=' expression

expression ::= object_literal
             | list_literal
             | tuple_literal
             | STRING
             | INTEGER
             | 'true' | 'false'

object_literal ::= [ '@' ] '{' object_member {',' object_member} '}'

object_member ::= IDENTIFIER [ ':' expr ]

list_literal ::= '[' [ expr {',' expr} ] ']'

tuple_literal ::= '(' expr {',' expr} ')'
```
