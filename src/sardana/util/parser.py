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
        group = (m.group("QUOTEDPARAM")
                 or m.group("SINGQUOTEDPARAM")
                 or m.group())
        tok = Token(m.lastgroup, group)
        if tok.type != "WS":
            yield tok


def is_repeat_param(param_def):
    return isinstance(param_def["type"], list)


def is_repeat_param_single(param_def):
    return len(param_def) == 1


class ParseError(Exception):
    pass


class UnrecognizedParamValue(ParseError):
    pass


class ExcessParamValue(ParseError):
    pass


class ParamParser:
    """Implementation of a recursive descent parser. Use the ._accept() method
    to test and accept the current lookahead token. Use the ._expect()
    method to exactly match and discard the next token on the input
    (or raise a SyntaxError if it doesn't match).

    Inspired on Python Cookbook 3 (chapter 2.19)
    """

    def __init__(self, params_def=None):
        self._params_def = params_def

    def parse(self, text):
        self.tokens = generate_tokens(text)
        self.tok = None             # Last symbol consumed
        self.nexttok = None         # Next symbol tokenized
        self._advance()             # Load first lookahead token
        params = self._params()
        self._end_check()
        return params

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
            raise ParseError("Expected " + toktype)

    # Grammar rules follow

    def _params(self, params_def=None, is_repeat=False):
        """Interpret parameter values by iterating over generated tokens
        according to parameters definition.

        It is used either at the macro level or a the repeat parameter
        repetition level.

        :param params_def: parameters definition as used by the
            :meth:`sardana.macroserver.msmetamacro.Parametrizable.get_parameter`
            or by the
            `attr:`sardana.taurus.core.tango.sardana.macro.MacroInfo.parameters`
        :type params_def: list<dict>
        :param end_check: whether to check if there are parameter values
            exceeding parameters definition
        :type end_check: bool
        :return: parameter values
        :rtype: list
        """
        params_def = params_def or self._params_def
        len_params_def = len(params_def)
        params = []
        for param_idx, param_def in enumerate(params_def):
            # no next tokens means that the string being parsed had finished
            if self.nexttok is None:
                break
            if is_repeat_param(param_def):
                is_last_param = False
                if param_idx == len_params_def - 1:
                    is_last_param = True
                repeat_param_def = param_def["type"]
                param_value = self._repeat_param(repeat_param_def,
                                                 is_last_param)
            else:
                try:
                    param_value = self._param()
                except UnrecognizedParamValue:
                    # this exception may occur if repeat is not complete -
                    # uses default values
                    if is_repeat:
                        return params
                    raise
            params.append(param_value)
        return params

    def _param(self):
        """Interpret normal parameter value. Respect quotes for string
        parameters.

        :return: parameter value
        :rtype: str
        """
        if self._accept("LPAREN"):
            # empty brackets will be interpreted as a default value
            self._expect("RPAREN")
            param = []
        elif self._accept("QUOTEDPARAM"):
            # quoted parameters allows using quotes escaped by \\
            string = self.tok.value
            string = string.replace('\\"', '"')
            param = string
        elif self._accept("SINGQUOTEDPARAM"):
            param = self.tok.value
        elif self._accept("PARAM"):
            tok_value = self.tok.value
            param = tok_value
        else:
            msg = "%s is not a valid param value" % self.tok.value
            raise UnrecognizedParamValue(msg)
        return param

    def _repeat_param(self, repeat_param_def, is_last_param):
        """Interpret repeat parameter.

        Accepts repeat parameters using the following rules:
        * enclosed in parenthesis
        * non-enclosed in parenthesis multiple repetitions of the last repeat
          parameter (can be single or multiple)
        * non-enclosed in parenthesis one repetition of single repeat
        parameter at arbitrary position

        :param repeat_param_def: repeat parameter definition
        :type repeat_param_def: list<dict>
        :param is_last_param: whether this repeat parameter is the last in the
            definition
        :type is_last_param: bool
        :return: repeat parameter value
        :rtype: list
        """
        repeats = []

        if self._accept("LPAREN"):
            while True:
                repeat = self._repeat(repeat_param_def)
                if repeat is None:
                    break
                repeats.append(repeat)
            self._expect("RPAREN")
        else:
            single = is_repeat_param_single(repeat_param_def)
            if is_last_param:
                while True:
                    repeat = []
                    for _ in repeat_param_def:
                        try:
                            param = self._param()
                        except UnrecognizedParamValue:
                            return repeats
                        if single:
                            repeat = param
                        else:
                            repeat.append(param)
                    repeats.append(repeat)
            elif single:
                param = self._param()
                repeats = [param]
        return repeats

    def _repeat(self, repeat_param_def):
        """Interpret one repetition of the repeat parameter.

        :param repeat_param_def: repeat parameter definition
        :type repeat_param_def: list<dict>
        :return: repeat value
        :rtype: list or None
        """
        repeat = None
        if self._accept("LPAREN"):
            # empty brackets will be interpreted as a default value
            if self._accept("RPAREN"):
                repeat = []
            else:
                repeat = self._params(repeat_param_def, is_repeat=True)
                # repetitions of single repeat parameters are not enclosed
                # in parenthesis so remove it
                if is_repeat_param_single(repeat_param_def):
                    repeat = repeat[0]
                self._expect("RPAREN")
        else:
            try:
                repeat = self._param()
            except UnrecognizedParamValue:
                # no repeat found - return None
                pass
        return repeat

    def _end_check(self):
        """Check if there are excessive tokens."""
        excess_tokens = ""
        if len(self._params_def) == 0 and self.nexttok is not None:
            excess_tokens += self.nexttok.value
        while True:
            self._advance()
            if self.nexttok is None:
                break
            excess_tokens += self.nexttok.value
        if len(excess_tokens) > 0:
            raise ExcessParamValue("excess tokens are %s" % excess_tokens)
