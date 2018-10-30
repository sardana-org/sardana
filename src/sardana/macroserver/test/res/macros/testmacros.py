from sardana.macroserver.macro import Type, Macro

MSG_TEMP = "Parsing failed (result: %r; expected: %r)"


class runMacro(Macro):

    def run(self, *args):

        expect_params = (99, [1., 2.])
        macro, _ = self.prepareMacro("testParamMacros1", *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (99, 1., 2.)
        macro, _ = self.prepareMacro("testParamMacros1", *params)
        expect_params = (99, [1., 2.])
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([92], True)
        macro, _ = self.prepareMacro("testParamsFirstRepeat", *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (91, True)
        expect_params = ([91], True)
        macro, _ = self.prepareMacro("testParamsFirstRepeat", *params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg


class createMacro(Macro):

    def run(self, *args):

        expect_params = (99, [1., 2.])
        macro, pars = self.createMacro('testParamMacros1', *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (99, 1., 2.)
        expect_params = (99, [1., 2.])
        self.runMacro(macro)
        macro, pars = self.createMacro('testParamMacros1', *params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([92], True)
        macro, _ = self.createMacro("testParamsFirstRepeat", *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (91, True)
        expect_params = ([91.], True)
        macro, _ = self.createMacro("testParamsFirstRepeat", *params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg


class execMacro(Macro):

    def run(self, *args):

        expect_params = (99, [1., 2.])
        macro = self.execMacro('testParamMacros1', *expect_params)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        params = (99, 1., 2.)
        macro = self.execMacro('testParamMacros1', *params)
        result = macro.data
        expect_params = (99, [1., 2.])
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([92], True)
        macro = self.execMacro('testParamsFirstRepeat', *expect_params)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([99.], True)
        macro = self.execMacro("testParamsFirstRepeat [99] True")
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg

        expect_params = ([999.], True)
        macro = self.execMacro("testParamsFirstRepeat", 999, True)
        self.runMacro(macro)
        result = macro.data
        msg = MSG_TEMP % (result, expect_params)
        assert expect_params == result, msg


class testParamMacros1(Macro):
    """Macro with a motor parameter followed by a list of numbers.
    Usages from Spock, ex.:
    pt5 99 [1 3]
    pt5 99 1 3
    """

    param_def = [
        ['val1', Type.Float, None, 'value 1'],
        ['numb_list', [['pos', Type.Float, None, 'value']], None,
         'List of values'],
    ]

    def run(self, *args, **kwargs):
        self.data = args


class testParamsFirstRepeat(Macro):
    """Macro with a motor parameter followed by a list of numbers.
    Usages from Spock, ex.:
    pt5 99 [1 3]
    pt5 99 1 3
    """

    param_def = [

        ['numb_list', [['pos', Type.Float, None, 'value']], None, 'List of '
                                                                  'values'],
        ['val1', Type.Boolean, None, 'value 1'],
    ]

    def run(self, *args, **kwargs):
        self.data = args
