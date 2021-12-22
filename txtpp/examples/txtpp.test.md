Hello
@define HELLO

world

@if HELLO
>>> Hello
@else
>>> Not hello
@end


@if ARG
ARG is set
@end


@@ @@ Comment
@@ @define WORLD
@@
@@ @if NOTDEF
@@ Hello
@@ @end
@@
@@ @if HELLO
@@ @   if WORLD
@@ Hello world
@@ @   else
@@ Hello !
@@ @   end
@@ @else
@@ Hey
@@ @end
@@
@@ lol
