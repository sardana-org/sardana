#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""This package contains macro parameters parsing utilities."""

__all__ = ["ParamParser"]

import re
import collections

# Token specification
PARAM = r"(?P<PARAM>[^\[\]\s]+)"
QUOTEDPARAM = r'"(?P<QUOTEDPARAM>.*?)(?<!\\)"'
SINGQUOTEDPARAM = r"'(?P<SINGQUOTEDPARAM>.*?)'"
LPAREN = r"(?P<LPAREN>\[)"
RPAREN = r"(?P<RPAREN>\])"
WS = r"(?P<WS>\s+)"

master_pat = re.compile("|".join([QUOTEDPARAM, SINGQUOTEDPARAM, PARAM, LPAREN,
                                  RPAREN, WS]))

# Tokenizer
Token = collections.namedtuple("Token", ["type", "value"])


def generate_tokens(text):
    scanner = master_pat.scanner(text)
    for m in iter(scanner.match, None):
        # quoted parameters must be returned without the quotes that's why we
        # extract a given group, otherwise we would extract the whole match
        group = (m.group("QUOTEDPARAM") or
                 m.group("SINGQUOTEDPARAM") or
                 m.group())
        tok = Token(m.lastgroup, group)
        if tok.type != "WS":
            yield tok


class ParamParser:
    """Implementation of a recursive descent parser. Use the ._accept() method
    to test and accept the current lookahead token. Use the ._expect()
    method to exactly match and discard the next token on the input
    (or raise a SyntaxError if it doesn't match).

    Inspired on Python Cookbook 3 (chapter 2.19)
    """

    def parse(self, text):
        self.tokens = generate_tokens(text)
        self.tok = None             # Last symbol consumed
        self.nexttok = None         # Next symbol tokenized
        self._advance()             # Load first lookahead token
        return self.param()

    def _advance(self):
        """Advance one token ahead"""
        self.tok, self.nexttok = self.nexttok, next(self.tokens, None)

    def _accept(self, toktype):
        """Test and consume the next token if it matches toktype"""
        if self.nexttok and self.nexttok.type == toktype:
            self._advance()
            return True
        else:
            return False

    def _expect(self, toktype):
        """Consume next token if it matches toktype or raise SyntaxError"""
        if not self._accept(toktype):
            raise SyntaxError("Expected " + toktype)

    # Grammar rules follow

    def param(self):
        """Interpret parameters by iterating over generated tokens. Respect
        quotes for string parameters and parenthesis for repeat parameters.
        """
        params = []
        while True:
            if self._accept("QUOTEDPARAM"):
                # quoted parameters allows using quotes escaped by \\
                string = self.tok.value
                string = string.replace('\\"', '"')
                params.append(string)
            elif self._accept("SINGQUOTEDPARAM"):
                params.append(self.tok.value)
            elif self._accept("PARAM"):
                params.append(self.tok.value)
            elif self._accept("LPAREN"):
                params.append(self.param())
                self._expect("RPAREN")
            else:
                break
        return params
