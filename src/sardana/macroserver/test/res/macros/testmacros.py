from sardana.macroserver.macro import Type, Macro

MSG_TEMP = "Parsing failed (result: %r; expected: %r)"


class runMacro(Macro):
    """
    Macro to test the parameters parsing/decoding using the macro API,
    'runMacro'
    """
    def run(self, *args):

        expect_params = (99, [1., 2.])
        macro, _ = self.prepareMacro("pt6_base", *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (99, 1., 2.)
        macro, _ = self.prepareMacro("pt6_base", *params)
        expect_params = (99, [1., 2.])
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([92], True)
        macro, _ = self.prepareMacro("pt10_base", *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (91, True)
        expect_params = ([91], True)
        macro, _ = self.prepareMacro("pt10_base", *params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg


class createMacro(Macro):
    """
    Macro to test the parameters parsing/decoding using the macro API,
    'createMacro'
    """
    def run(self, *args):

        expect_params = (99, [1., 2.])
        macro, pars = self.createMacro('pt6_base', *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (99, 1., 2.)
        expect_params = (99, [1., 2.])
        self.runMacro(macro)
        macro, pars = self.createMacro('pt6_base', *params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([92], True)
        macro, _ = self.createMacro("pt10_base", *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (91, True)
        expect_params = ([91.], True)
        macro, _ = self.createMacro("pt10_base", *params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg


class execMacro(Macro):
    """
    Macro to test the parameters parsing/decoding using the macro API,
    'execMacro'
    """
    def run(self, *args):

        expect_params = (99, [1., 2.])
        macro = self.execMacro('pt6_base', *expect_params)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (99, 1., 2.)
        macro = self.execMacro('pt6_base', *params)
        result = macro.data
        expect_params = (99, [1., 2.])
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([92], True)
        macro = self.execMacro('pt10_base', *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([99.], True)
        macro = self.execMacro("pt10_base [99] True")
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([999.], True)
        macro = self.execMacro("pt10_base", 999, True)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg


class pt6_base(Macro):
    """Macro with a number parameter followed by a list of numbers.
    Usages from Spock, ex.:
    pt6_base 99 [1 3]
    pt6_base 99 1 3
    """

    param_def = [
        ['val1', Type.Float, None, 'value 1'],
        ['numb_list', [['pos', Type.Float, None, 'value']], None,
         'List of values'],
    ]

    def run(self, *args, **kwargs):
        self.data = args


class pt10_base(Macro):
    """Macro with a list of numbers followed by a boolean parameter.
    Usages from Spock, ex.:
    pt10_base [1] True
    pt10_base 1 True
    """

    param_def = [

        ['numb_list', [['pos', Type.Float, None, 'value']], None,
         'List of values'],
        ['val1', Type.Boolean, None, 'value 1'],
    ]

    def run(self, *args, **kwargs):
        self.data = args
