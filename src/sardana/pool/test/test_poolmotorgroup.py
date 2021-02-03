import pytest
from sardana.pool.test.test_poolcontroller import controller
from sardana.pool.test.test_poolmotor import _motor


@pytest.fixture
def motor_group(motors=None, full_name="motgrp01", name="motgrp01"):
    if motors is None:
        from sardana.pool.test.test_pool import pool
        pool = pool()
        ctrl = controller(pool)
        motors = [_motor(ctrl), _motor(ctrl)]
    pool = motors[0].pool
    kwargs = {'full_name': full_name,
              'name': name,
              'user_elements': [m.id for m in motors]
              }
    return pool.create_motor_group(**kwargs)
