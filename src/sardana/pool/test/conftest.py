from random import randrange

import pytest
from sardana import ElementType
from sardana.pool.pool import Pool


@pytest.fixture(scope="module")
def pool(full_name=None, name=None, pool_path=None):
    if full_name is None:
        full_name = "pool"
    if name is None:
        name = "pool"
    pool = Pool(full_name, name)
    if pool_path is None:
        pool_path = []
    pool.set_path(pool_path)
    return pool


@pytest.fixture(scope="module")
def controller(pool, conf=None):
    if conf is None:
        conf = {
            "full_name": "dmotctrl01",
            "name": "dmotctrl01",
            "klass": "DummyMotorController",
            "library": "DummyMotorController.py",
            "type": "Motor",
            "properties": {},
        }
    return pool.create_controller(**conf)


@pytest.fixture()
def motor(pool, controller):
    def _motor():
        pool_motors = pool.get_elements_by_type(ElementType.Motor)
        axes = []
        for motor in pool_motors:
            if motor.controller == controller:
                axes.append(motor.axis)
        max_axis = max(axes) if len(axes) > 0 else 0
        axis = max_axis + 1
        kwargs = {
            "type": "Motor",
            "ctrl_id": controller.id,
            "axis": axis,
            "full_name": "mot{}".format(axis),
            "name": "mot{}".format(axis),
        }
        motor = pool.create_element(**kwargs)
        return motor

    return _motor


@pytest.fixture()
def motor_group(motor):
    m1 = motor()
    m2 = motor()
    motors = [m1, m2]
    pool = motors[0].pool
    full_name = name = "motgrp0{}".format(randrange(10))
    kwargs = {
        "full_name": full_name,
        "name": name,
        "user_elements": [m.id for m in motors],
    }
    return pool.create_motor_group(**kwargs)


@pytest.fixture(params=["motor", "motor_group"])
def moveable(request, motor, motor_group):
    if request.param == "motor":
        return motor()
    if request.param == "motor_group":
        return motor_group
