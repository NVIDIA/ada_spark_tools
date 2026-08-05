<!--
SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION &
                        AFFILIATES. All rights reserved.
SPDX-License-Identifier: GPL-3.0-or-later
-->

# GPR Grammar
This is based on
https://docs.adacore.com/gprbuild-docs/html/gprbuild_ug/project_file_reference.html
but the grammar is cleaned up and fixed.

## Tokens

```bnf
COMMENT ::= --.*

IDENTIFIER ::= [a-zA-Z][a-zA-Z0-9_]*

STRING ::= "(.|"")*"
```

There are also some punctuation tokens:
* `:=` (assignment)
* `->` (arrow)
* `&` (concatenation)
* `(` and `)`
* `;` (end of statement)
* `,` (comma separator)
* `:` (colon)
* `.` (dot)

Pragmas are comments that also match these expressions:
```bnf
PRAGMA_SKIP_FILE ::= -- *gpr_checker: skip_file:.*
```

Keywords are identifiers contained in the set of reserved words.

## Top level

```bnf
gpr_file ::= { file_pragma }
             project

file_pragma ::= PRAGMA_SKIP_FILE
```

## Common
```bnf
name ::= IDENTIFIER { . IDENTIFIER }
```

## Projects
```bnf
project ::= context_clause project_declaration

context_clause ::= {with_clause}
with_clause    ::= [ 'limited' ] 'with' path_name { , path_name } ;
path_name      ::= string_literal

project_declaration ::= simple_project_declaration | project_extension

simple_project_declaration ::=
   [ qualifier ] 'project' <project_>name 'is'
     {declarative_item}
   'end' <project_>name ;

project_extension ::=
  [ qualifier ] 'project' <project_>name 'extends' [ 'all' ] <base_project_>name 'is'
    {declarative_item}
 'end' <project_>name ;

qualifier ::= 'abstract' | IDENTIFIER [ IDENTIFIER ]
```

Meaning of `limited with` is defined here:
https://docs.adacore.com/gprbuild-docs/html/gprbuild_ug/gnat_project_manager.html#cyclic-project-dependencies,
but basically it means you cannot refer to variables, projects or
packages in the withing unit.

## Declarations
```bnf
declarative_item ::= typed_string_declaration
                   | package_declaration
				   | simple_declarative_item

simple_declarative_item ::= variable_declaration
                          | typed_variable_declaration
                          | attribute_declaration
                          | case_construction
                          | 'null' ;
```

## Typed strings
```bnf
typed_string_declaration ::=
  'type' <typed_string_>IDENTIFIER 'is' ( string_literal {, string_literal} );
```

## Packages
```bnf
package_declaration ::= package_spec | package_renaming | package_extension

package_spec ::=
  'package' <package_>IDENTIFIER 'is'
     { simple_declarative_item }
  'end' <package_>IDENTIFIER ;

package_renaming ::=
  'package' <package_>IDENTIFIER 'renames'
        <project_>IDENTIFIER.<package_>IDENTIFIER ;

package_extension ::=
  'package' <package_>IDENTIFIER 'extends'
        <project_>IDENTIFIER.<package_>IDENTIFIER 'is'
     { simple_declarative_item }
  'end' <package_>IDENTIFIER ;
```

## Variables
```bnf
typed_variable_declaration ::=
  <typed_variable_>IDENTIFIER : <typed_string_>name := <string_>expression;

variable_declaration ::= <variable_>IDENTIFIER := expression;
```

Note: You can assign to the same variable more than once
(e.g. declaring with a default and then overwriting in a case
expression). The type is implicitly set on the first declaration.

Note: A variable declaration with the same name in a project and
package is possible, the package variable shadows the project variable
for the duration the package is in scope. The types could be
different.

## Attributes
```bnf
attribute_declaration ::=
   'for' IDENTIFIER [ ( string_literal ) ] 'use' expression ;
```

## Case
```bnf
case_construction ::=
  'case' <variable_>name 'is' {case_item} 'end' 'case' ;

case_item ::= 'when' discrete_choice_list '=>' {case_action}

case_action ::= case_construction
              | attribute_declaration
              | variable_declaration
              | empty_declaration

discrete_choice_list ::= string_literal {| string_literal}
                       | 'others'
```

You cannot declare a variable for the first time in a case statement,
nor can you declare types.

## Expressions
```bnf
expression ::= term { & term }

term ::= STRING_LITERAL
	   | external_reference
       | name_reference
	   | ( term { & term } )
	   | ( term { , term } )

external_reference ::=
   'external' ( <env_>STRING_LITERAL [, <default_>STRING_LITERAL] )

name_reference ::= <variable_>name
                 | <attribute_>name ' IDENTIFIER [ (STRING_LITERAL) ]
                 | 'project' ' IDENTIFIER [ (STRING_LITERAL) ]
```
