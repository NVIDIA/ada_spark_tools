with Ada.Text_IO; use Ada.Text_IO;

procedure Foo
with SPARK_Mode
is
begin
   Put_Line ("Hello World!");
end Foo;
