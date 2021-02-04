#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

"""reST directive for syntax-highlighting spock interactive sessions.
"""

#-----------------------------------------------------------------------------
# Needed modules

# Standard library
import re
import copy

# Third party
from pygments.lexer import Lexer, do_insertions
from pygments.lexers.agile import (PythonConsoleLexer, PythonLexer,
                                   PythonTracebackLexer)
from pygments.token import Token, Comment, Generic
from pygments.style import Style
import pygments.styles
from sphinx import highlighting

#-----------------------------------------------------------------------------
# Global constants
line_re = re.compile('.*?\n')

DftStyle = pygments.styles.get_style_by_name("default")


class SpockStyle(DftStyle):

    styles = copy.copy(DftStyle.styles)
    styles[Generic.Prompt] = 'bold #00AA00'


class SpockConsoleLexer(Lexer):
    """
    For spock console output or doctests, such as:

    .. sourcecode:: spock

      LAB-01 [1]: a = 'foo'

      LAB-01 [2]: a
      Result [2]: 'foo'

      LAB-01 [3]: print(a)
      foo

      LAB-01 [4]: 1 / 0

    Notes:

      - Tracebacks are not currently supported.

      - It assumes the default spock prompts, not customized ones.
    """

    name = 'Spock console session'
    aliases = ['spock']
    mimetypes = ['text/x-spock-console']
    input_prompt = re.compile(
        "([a-zA-Z0-9_\-]+ \[(?P<N>[0-9]+)\]: )|(   \.\.\.+:)")
    output_prompt = re.compile("(\s*Result \[(?P<N>[0-9]+)\]: )|(   \.\.\.+:)")
    continue_prompt = re.compile("   \.\.\.+:")
    tb_start = re.compile("\-+")

    def get_tokens_unprocessed(self, text):
        pylexer = PythonLexer(**self.options)
        tblexer = PythonTracebackLexer(**self.options)

        curcode = ''
        insertions = []
        for match in line_re.finditer(text):
            line = match.group()
            input_prompt = self.input_prompt.match(line)
            continue_prompt = self.continue_prompt.match(line.rstrip())
            output_prompt = self.output_prompt.match(line)
            if line.startswith("#"):
                insertions.append((len(curcode),
                                   [(0, Comment, line)]))
            elif line.startswith("<warning>"):
                insertions.append((len(curcode),
                                   [(0, Generic.Error, line[9:])]))
            elif input_prompt is not None:
                insertions.append((len(curcode),
                                   [(0, Generic.Prompt, input_prompt.group())]))
                curcode += line[input_prompt.end():]
            elif continue_prompt is not None:
                insertions.append((len(curcode),
                                   [(0, Generic.Prompt, continue_prompt.group())]))
                curcode += line[continue_prompt.end():]
            elif output_prompt is not None:
                # Use the 'error' token for output.  We should probably make
                # our own token, but error is typicaly in a bright color like
                # red, so it works fine for our output prompts.
                insertions.append((len(curcode),
                                   [(0, Generic.Error, output_prompt.group())]))
                curcode += line[output_prompt.end():]
            else:
                if curcode:
                    for item in do_insertions(insertions,
                                              pylexer.get_tokens_unprocessed(curcode)):
                        yield item
                        curcode = ''
                        insertions = []
                yield match.start(), Generic.Output, line
        if curcode:
            for item in do_insertions(insertions,
                                      pylexer.get_tokens_unprocessed(curcode)):
                yield item


def setup(app):
    """Setup as a sphinx extension."""

    # This is only a lexer, so adding it below to pygments appears sufficient.
    # But if somebody knows that the right API usage should be to do that via
    # sphinx, by all means fix it here.  At least having this setup.py
    # suppresses the sphinx warning we'd get without it.
    pass

#-----------------------------------------------------------------------------
# Register the extension as a valid pygments lexer
highlighting.lexers['spock'] = SpockConsoleLexer()
