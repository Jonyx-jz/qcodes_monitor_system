import random
import time
from qcodes.instrument import Instrument
from qcodes.parameters import Parameter
from qcodes.validators import Numbers

class SyntheticInstrument(Instrument):
#- Gaussian measurement noise
#    - Slow random drift
#    - Connection state
#    - Occasional simulated read failures
    def __init__(
        self,
        name,
        noise_std=0.0,
        drift_rate=0.0,
        failure_probability=0.0,
    ):
        super().__init__(name)

        self.noise_std = noise_std
        self.drift_rate = drift_rate
        self.failure_probability = failure_probability

        self.connected = True

        self._drift = 0.0
        self._last_update_time = time.monotonic()


    def connect(self):
        self.connected = True


    def disconnect(self):
        self.connected = False


    def _check_read_failure(self):

        if not self.connected:
            raise ConnectionError(
                f"{self.name} is disconnected."
            )

        if random.random() < self.failure_probability:
            raise TimeoutError(
                f"{self.name} failed to respond."
            )


    def _add_noise(self, value):

        noise = random.gauss(
            0.0,
            self.noise_std
        )

        return value + noise


    def _update_drift(self):

        current_time = time.monotonic()

        dt = current_time - self._last_update_time

        drift_change = random.gauss(
            0.0,
            self.drift_rate * dt
        )

        self._drift += drift_change

        self._last_update_time = current_time


    def _get_drift(self):

        self._update_drift()

        return self._drift


    def _simulate_read(self, true_value):

        self._check_read_failure()

        drift = self._get_drift()

        measured_value = true_value + drift

        measured_value = self._add_noise(
            measured_value
        )

        return measured_value
class SyntheticMicrowaveGenerator(SyntheticInstrument):

    def __init__(
        self,
        name,
        initial_frequency=5.0e9,
        initial_power=-20.0,
        frequency_noise_std=1.0e3,
        power_noise_std=0.05,
        frequency_drift_rate=10.0,
        power_drift_rate=0.001,
        failure_probability=0.01,
    ):
        super().__init__(
            name=name,
            noise_std=0.0,
            drift_rate=0.0,
            failure_probability=failure_probability,
        )

        # Internal ideal setpoints
        self._frequency = initial_frequency
        self._power = initial_power

        # Separate noise levels for different physical quantities
        self.frequency_noise_std = frequency_noise_std
        self.power_noise_std = power_noise_std

        # Separate drift rates for different physical quantities
        self.frequency_drift_rate = frequency_drift_rate
        self.power_drift_rate = power_drift_rate
        
        # Separate drift values for different physical quantities
        self._frequency_drift = 0.0
        self._power_drift = 0.0

        # Last update times for different physical quantities
        self._last_frequency_drift_update = time.monotonic()
        self._last_power_drift_update = time.monotonic()

        # Add parameters for frequency and power
        self.add_parameter(
            "frequency",
            parameter_class=Parameter,
            unit="Hz",
            get_cmd=self._get_frequency,
            set_cmd=self._set_frequency,
        )

        self.add_parameter(
            "power",
            parameter_class=Parameter,
            unit="dBm",
            get_cmd=self._get_power,
            set_cmd=self._set_power,
        )

        self.add_parameter(
            "measured_frequency",
            parameter_class=Parameter,
            unit="Hz",
            get_cmd=self._get_measured_frequency,
            set_cmd=False,
        )

        self.add_parameter(
            "measured_power",
            parameter_class=Parameter,
            unit="dBm",
            get_cmd=self._get_measured_power,
            set_cmd=False,
        )

    #setters and getters for the internal ideal setpoints
    def _set_frequency(self, value):
        self._frequency = value

    def _get_frequency(self):
        return self._frequency

    def _set_power(self, value):
        self._power = value

    def _get_power(self):
        return self._power


    # drift simulation for the measured values
    def _update_frequency_drift(self):
        now = time.monotonic()

        dt = now - self._last_frequency_drift_update

        drift_change = random.gauss(
            0.0,
            self.frequency_drift_rate * dt
        )

        self._frequency_drift += drift_change

        self._last_frequency_drift_update = now
    def _update_power_drift(self):
        now = time.monotonic()

        dt = now - self._last_power_drift_update

        drift_change = random.gauss(
            0.0,
            self.power_drift_rate * dt
        )

        self._power_drift += drift_change

        self._last_power_drift_update = now

    # getters for the measured values with noise and drift
    def _get_measured_frequency(self):
        self._check_read_failure()

        self._update_frequency_drift()

        noise = random.gauss(
            0.0,
            self.frequency_noise_std
        )

        return (
            self._frequency
            + self._frequency_drift
            + noise
        )


    def _get_measured_power(self):
        self._check_read_failure()

        self._update_power_drift()

        noise = random.gauss(
        0.0,
        self.power_noise_std
        )

        return (
        self._power
        + self._power_drift
        + noise
        )
class SyntheticCryostatController(SyntheticInstrument):

    def __init__(
        self,
        name,
        initial_temperature=0.050,
        target_temperature=0.020,
        temperature_noise_std=0.0005,
        temperature_drift_rate=0.00001,
        time_constant=20.0,
        failure_probability=0.01,
    ):
        super().__init__(
            name=name,
            noise_std=0.0,
            drift_rate=0.0,
            failure_probability=failure_probability,
        )

        self._temperature = initial_temperature
        self._target_temperature = target_temperature

        self.temperature_noise_std = temperature_noise_std
        self.temperature_drift_rate = temperature_drift_rate
        self.time_constant = time_constant

        self._temperature_drift = 0.0

        self._last_update_time = time.monotonic()

        self._cooling_power = 1.0

        self.add_parameter(
            "cooling_power",
            parameter_class=Parameter,
            unit="",
            get_cmd=self._get_cooling_power,
            set_cmd=self._set_cooling_power,
            vals=Numbers(0.0, 1.0),
        )

        self.add_parameter(
            "target_temperature",
            parameter_class=Parameter,
            unit="K",
            get_cmd=self._get_target_temperature,
            set_cmd=self._set_target_temperature,
        )

        self.add_parameter(
            "measured_temperature",
            parameter_class=Parameter,
            unit="K",
            get_cmd=self._get_measured_temperature,
            set_cmd=False,
        )


    def _set_cooling_power(self, value):
        self._cooling_power = value

    def _get_cooling_power(self):
        return self._cooling_power

    def _set_target_temperature(self, value):
        self._update_temperature()
        self._target_temperature = value

    def _get_target_temperature(self):
        return self._target_temperature

    def _update_temperature(self):
        now = time.monotonic()

        dt = now - self._last_update_time

        if dt > 0:
            change = (
            (self._target_temperature - self._temperature)/ self.time_constant)* self._cooling_power * dt

            self._temperature += change

        drift_change = random.gauss(
            0.0,
            self.temperature_drift_rate * dt
        )

        self._temperature_drift += drift_change

        self._last_update_time = now

    def _get_measured_temperature(self):
        self._check_read_failure()

        self._update_temperature()

        noise = random.gauss(
            0.0,
            self.temperature_noise_std
        )

        return (
            self._temperature
            + self._temperature_drift
            + noise
        )
