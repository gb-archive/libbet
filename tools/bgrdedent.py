#!/usr/bin/env python3
"""
Indentation translator for RGBASM
Copyright 2018 Damian Yerrick

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
"""
"""
bgrdedent.py is a preprocessor for SM83 (Game Boy CPU) assembly
language source code files intended to be assembled using older
versions of RGBDS assembler ([RGBASM]).  It translates the "followed
by colon" convention for denoting labels that [ca65] and other modern
assemblers use to the "begins in first column" convention that
punch-card-era assemblers used and RGBASM used prior to 0.4.0.

First all leading and trailing whitespace is removed.  Then decide
whether or not to re-add a leading space based on the first of the
following rules that applies for each line, where a "word" is a run
of non-whitespace.

* If the previous line ended with a backslash, it is a line
  continuation. Start this line at column 2.
* If the line is empty, is blank, output a blank line.
* If the first word is `SECTION`, `EXPORT`, `GLOBAL`, `UNION`,
  `NEXTU`, or `ENDU` (case insensitive), start this line at column 1.
* If the first word does not contain a quotation mark or semicolon,
  and the second word is `EQU`, `SET`, `RB`, `RW`, `RL`, or `EQUS`
  (case insensitive), start this line at column 1.
* If the first word contains a colon or equal sign,
  start this line at column 1.
* If the second word begins with a colon or equal sign,
  start this line at column 1.
* Start everything else at column 2.


[RGBASM]: https://rednex.github.io/rgbds/rgbasm.5.html
[ca65]: https://cc65.github.io/doc/ca65.html

"""
import sys
import argparse

def fixcolumns(lines):
    last_was_continue = False
    word0s = {'section', 'export', 'global', 'union', 'nextu', 'endu'}
    word1s = {'equ', 'set', 'rb', 'rw', 'rl', 'equs'}
    for line in lines:
        line = line.strip()
        lwords = line.lower().split()
        start = ' '
        if last_was_continue:
            pass
        elif len(lwords) == 0:
            start = ''
        elif lwords[0] in word0s:
            start = ''
        elif (len(lwords) > 1 and lwords[1] in word1s
              and ";" not in lwords[0] and ":" not in lwords[0]):
            start = ''
        elif ':' in lwords[0] or '=' in lwords[0]:
            start = ''
        elif len(lwords) > 1 and lwords[1].startswith((':', '=')):
            start = ''
        yield "".join((start, line, "\n"))
        last_was_continue = line.endswith("\\")

def parse_argv(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("input", default="-", nargs='?',
                        help="file to dedent (standard input if omitted)")
    parser.add_argument("-o", "--output", default="-",
                        help="file to write (standard output if omitted)")
    return parser.parse_args(argv[1:])

def main(argv=None):
    args = parse_argv(argv or sys.argv)

    infp, outfp = sys.stdin, sys.stdout
    try:
        if args.input != '-':
            infp = open(args.input, "r")
        if args.output != '-':
            outfp = open(args.output, "w")
        outfp.writelines(fixcolumns(infp))
    finally:
        if outfp is not sys.stdout:
            outfp.close()
        if infp is not sys.stdin:
            infp.close()

if __name__=='__main__':
    main()
