from sardana.macroserver.macro import Hookable


def test_Hookable():
    hookable = Hookable()
    assert len(hookable.hooks) == 0
    hooks = hookable.getHooks("unexisting-hook-place")
    assert len(hooks) == 0
    hookable.hooks = []
    assert len(hookable.hooks) == 0
    hooks = hookable.getHooks("unexisting-hook-place")
