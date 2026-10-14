import time

import pytest

from instruments import (
    SyntheticMicrowaveGenerator,
    SyntheticCryostatController,
)


# ============================================================
# Microwave Generator Tests
# ============================================================

def test_microwave_initial_setpoints():
    generator = SyntheticMicrowaveGenerator(
        "test_mw_initial",
        initial_frequency=5.0e9,
        initial_power=-20.0,
        failure_probability=0.0,
    )

    assert generator.frequency() == pytest.approx(5.0e9)
    assert generator.power() == pytest.approx(-20.0)

    generator.close()


def test_microwave_change_setpoints():
    generator = SyntheticMicrowaveGenerator(
        "test_mw_change",
        failure_probability=0.0,
    )

    generator.frequency(5.2e9)
    generator.power(-15.0)

    assert generator.frequency() == pytest.approx(5.2e9)
    assert generator.power() == pytest.approx(-15.0)

    generator.close()


def test_microwave_measurements():
    generator = SyntheticMicrowaveGenerator(
        "test_mw_measurements",
        failure_probability=0.0,
    )

    measured_frequency = generator.measured_frequency()
    measured_power = generator.measured_power()

    assert isinstance(measured_frequency, float)
    assert isinstance(measured_power, float)

    generator.close()


def test_microwave_disconnect():
    generator = SyntheticMicrowaveGenerator(
        "test_mw_disconnect",
        failure_probability=0.0,
    )

    generator.disconnect()

    with pytest.raises(ConnectionError):
        generator.measured_frequency()

    generator.close()


def test_microwave_reconnect():
    generator = SyntheticMicrowaveGenerator(
        "test_mw_reconnect",
        failure_probability=0.0,
    )

    generator.disconnect()

    with pytest.raises(ConnectionError):
        generator.measured_frequency()

    generator.connect()

    value = generator.measured_frequency()

    assert isinstance(value, float)

    generator.close()


def test_microwave_read_failure():
    generator = SyntheticMicrowaveGenerator(
        "test_mw_failure",
        failure_probability=1.0,
    )

    with pytest.raises(TimeoutError):
        generator.measured_frequency()

    generator.close()


def test_microwave_drift():
    generator = SyntheticMicrowaveGenerator(
        "test_mw_drift",
        frequency_noise_std=0.0,
        power_noise_std=0.0,
        frequency_drift_rate=100.0,
        power_drift_rate=0.01,
        failure_probability=0.0,
    )

    first_frequency = generator.measured_frequency()
    first_power = generator.measured_power()

    time.sleep(0.1)

    second_frequency = generator.measured_frequency()
    second_power = generator.measured_power()

    # Drift should update the values over time
    assert isinstance(second_frequency, float)
    assert isinstance(second_power, float)

    generator.close()


# ============================================================
# Cryostat Tests
# ============================================================

def test_cryostat_initial_target():
    cryostat = SyntheticCryostatController(
        "test_cryo_initial",
        initial_target=0.020,
        failure_probability=0.0,
    )

    assert cryostat.target_temperature() == pytest.approx(0.020)

    cryostat.close()


def test_cryostat_target_change():
    cryostat = SyntheticCryostatController(
        "test_cryo_target",
        initial_target=0.020,
        failure_probability=0.0,
    )

    cryostat.target_temperature(0.030)

    assert cryostat.target_temperature() == pytest.approx(0.030)

    cryostat.close()


def test_cryostat_cooling_power():
    cryostat = SyntheticCryostatController(
        "test_cryo_cooling",
        failure_probability=0.0,
    )

    cryostat.cooling_power(0.5)

    assert cryostat.cooling_power() == pytest.approx(0.5)

    cryostat.close()


def test_cryostat_cooling_power_limits():
    cryostat = SyntheticCryostatController(
        "test_cryo_limits",
        failure_probability=0.0,
    )

    # Valid lower limit
    cryostat.cooling_power(0.0)
    assert cryostat.cooling_power() == pytest.approx(0.0)

    # Valid middle value
    cryostat.cooling_power(0.5)
    assert cryostat.cooling_power() == pytest.approx(0.5)

    # Valid upper limit
    cryostat.cooling_power(1.0)
    assert cryostat.cooling_power() == pytest.approx(1.0)

    # Invalid: below minimum
    with pytest.raises(ValueError):
        cryostat.cooling_power(-0.1)

    # Invalid: above maximum
    with pytest.raises(ValueError):
        cryostat.cooling_power(1.1)

    cryostat.close()


def test_cryostat_temperature_response():
    cryostat = SyntheticCryostatController(
        "test_cryo_response",
        initial_temperature=0.050,
        initial_target=0.020,
        temperature_noise_std=0.0,
        temperature_drift_rate=0.0,
        time_constant=0.2,
        failure_probability=0.0,
    )

    cryostat.cooling_power(1.0)

    first_temperature = cryostat.measured_temperature()

    time.sleep(0.1)

    second_temperature = cryostat.measured_temperature()

    # The cryostat starts at 0.050 K and is trying
    # to move toward the target of 0.020 K.
    assert second_temperature < first_temperature

    # It should not instantly jump below the target.
    assert second_temperature > 0.020

    cryostat.close()


def test_cryostat_lower_cooling_power_is_slower():
    fast = SyntheticCryostatController(
        "test_cryo_fast",
        initial_temperature=0.050,
        initial_target=0.020,
        temperature_noise_std=0.0,
        temperature_drift_rate=0.0,
        time_constant=0.2,
        failure_probability=0.0,
    )

    slow = SyntheticCryostatController(
        "test_cryo_slow",
        initial_temperature=0.050,
        initial_target=0.020,
        temperature_noise_std=0.0,
        temperature_drift_rate=0.0,
        time_constant=0.2,
        failure_probability=0.0,
    )

    fast.cooling_power(1.0)
    slow.cooling_power(0.2)

    # Update both once before waiting
    fast.measured_temperature()
    slow.measured_temperature()

    time.sleep(0.1)

    fast_temperature = fast.measured_temperature()
    slow_temperature = slow.measured_temperature()

    # Full cooling power should make more progress
    # toward the lower target temperature.
    assert fast_temperature < slow_temperature

    fast.close()
    slow.close()


def test_cryostat_disconnect():
    cryostat = SyntheticCryostatController(
        "test_cryo_disconnect",
        failure_probability=0.0,
    )

    cryostat.disconnect()

    with pytest.raises(ConnectionError):
        cryostat.measured_temperature()

    cryostat.close()


def test_cryostat_reconnect():
    cryostat = SyntheticCryostatController(
        "test_cryo_reconnect",
        failure_probability=0.0,
    )

    cryostat.disconnect()

    with pytest.raises(ConnectionError):
        cryostat.measured_temperature()

    cryostat.connect()

    value = cryostat.measured_temperature()

    assert isinstance(value, float)

    cryostat.close()


def test_cryostat_read_failure():
    cryostat = SyntheticCryostatController(
        "test_cryo_failure",
        failure_probability=1.0,
    )

    with pytest.raises(TimeoutError):
        cryostat.measured_temperature()

    cryostat.close()