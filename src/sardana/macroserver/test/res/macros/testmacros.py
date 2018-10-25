from sardana.macroserver.macro import Type, Macro


class runMacro(Macro):

    def run(self, *args):
        macro, _ = self.prepareMacro("testParamMacros1", 99, [1, 2])
        self.runMacro(macro)
        macro, _ = self.prepareMacro("testParamMacros1", 99, 1, 2)
        self.runMacro(macro)


class createMacro(Macro):

    def run(self, *args):
        macro, pars = self.createMacro('testParamMacros1', 99, 1, 3)
        self.runMacro(macro)
        macro, pars = self.createMacro('testParamMacros1', 99, [1, 3])
        self.runMacro(macro)


class execMacro(Macro):

    def run(self, *args):
        self.execMacro('testParamMacros1 99 [1 3]')
        self.execMacro('testParamMacros1', '99', '1', '3')


class testParamMacros1(Macro):
    """Macro with a motor parameter followed by a list of numbers.
    Usages from Spock, ex.:
    pt5 99 [1 3]
    pt5 99 1 3
    """

    param_def = [
        ['val1', Type.Float, None, 'value 1'],
        ['numb_list', [['pos', Type.Float, None, 'value']], None, 'List of '
                                                                  'values'],
    ]

    def run(self, *args, **kwargs):
        print args
