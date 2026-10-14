import time
import pytest

from instruments import SyntheticCryostatController


def test_target_temperature_change():
    """
    Check that the temperature target can be changed.
    """

    cryostat = SyntheticCryostatController(
        "cryo_target_test",
        failure_probability=0.0
    )

    cryostat.target_temperature(0.020)

    assert cryostat.target_temperature() == pytest.approx(0.020)

    cryostat.close()

def test_temperature_moves_toward_target():
    """
    Check that the measured temperature moves toward
    the target temperature over time.
    """

    cryostat = SyntheticCryostatController(
        "cryo_response_test",
        initial_temperature=0.100,
        target_temperature=0.020,
        temperature_noise_std=0.0,
        temperature_drift_rate=0.0,
        time_constant=0.2,
        failure_probability=0.0
    )

    initial = cryostat.measured_temperature()

    time.sleep(0.1)

    later = cryostat.measured_temperature()

    assert later < initial
    assert later > 0.020

    cryostat.close()

def test_disconnect():
    """
    A disconnected cryostat should not allow measurements.
    """

    cryostat = SyntheticCryostatController(
        "cryo_disconnect_test",
        failure_probability=0.0
    )

    cryostat.disconnect()

    with pytest.raises(ConnectionError):
        cryostat.measured_temperature()

    cryostat.close()

def test_reconnect():
    """
    The cryostat should work again after reconnecting.
    """

    cryostat = SyntheticCryostatController(
        "cryo_reconnect_test",
        failure_probability=0.0
    )

    cryostat.disconnect()

    with pytest.raises(ConnectionError):
        cryostat.measured_temperature()

    cryostat.connect()

    value = cryostat.measured_temperature()

    assert isinstance(value, (int, float))

    cryostat.close()

def test_read_failure():
    """
    failure_probability=1.0 should cause every read to fail.
    """

    cryostat = SyntheticCryostatController(
        "cryo_failure_test",
        failure_probability=1.0
    )

    with pytest.raises(TimeoutError):
        cryostat.measured_temperature()

    cryostat.close()