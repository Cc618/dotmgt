# Text preprocessor
This tool is a simple text preprocessor inspired by the C preprocessor.
However, it targets every text files.

## Usage
### Command line
```
txtpp [-D DEFINITION] input_file
```

### Syntax
See an [example here](examples/txtpp.simple.md).

### Directives
- comment : `@@ My comment`
- error : `@error <message>`
- warning : `@warning <message>`
- define : `@define <variable>`
- undef : `@undef <variable>`
- if : `@if <variable>`
- elif : `@elif <variable>`
- ifnot : `@ifnot <variable>`
- elifnot : `@elifnot <variable>`
- else : `@else`
- end : `@end` to end control structures
