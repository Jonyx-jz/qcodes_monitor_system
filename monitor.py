import time
import threading
from pathlib import Path

from qcodes.dataset import (
    Measurement,
    initialise_or_create_database_at,
    load_or_create_experiment,
)
from qcodes.parameters import Parameter


class Monitor:

    def __init__(
    self,
    database_path="data/monitoring.db",
    experiment_name="Quantum Lab Monitoring",
    sample_name="Synthetic Quantum Setup",
    ):
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

        self.experiment_name = experiment_name
        self.sample_name = sample_name

        self.monitored_parameters = []

        self._running = False

        self.history = {}

        self._history_lock = threading.Lock()

        self.dataset = None


    def add_parameter(
        self,
        parameter,
        interval=1.0,
        lower_threshold=None,
        upper_threshold=None,
    ):
        """
        Add a QCoDeS parameter to the monitor.

        interval:
            Time between reads in seconds.

        lower_threshold / upper_threshold:
            Optional warning limits.
        """

        parameter_info = {
            "parameter": parameter,
            "interval": interval,
            "lower_threshold": lower_threshold,
            "upper_threshold": upper_threshold,
            "next_read_time": 0.0,
        }

        self.monitored_parameters.append(
            parameter_info
        )

        # Create an empty live-history buffer
        name = parameter.full_name

        with self._history_lock:
            self.history[name] = {
                "time": [],
                "value": [],
            }


    def get_history(self, parameter_name):
        """
        Return copies of the live data for one parameter.

        Copies are returned so the plotter cannot accidentally
        modify the monitor's internal history.
        """

        with self._history_lock:

            data = self.history[
                parameter_name
            ]

            times = data["time"].copy()
            values = data["value"].copy()

        return times, values


    def _store_in_history(
        self,
        parameter,
        elapsed,
        value,
    ):
        """
        Store a successful measurement in memory
        for live plotting.
        """

        with self._history_lock:

            self.history[
                parameter.full_name
            ]["time"].append(elapsed)

            self.history[
                parameter.full_name
            ]["value"].append(value)


    def _check_thresholds(
        self,
        parameter,
        value,
        lower_threshold,
        upper_threshold,
    ):
        """
        Print a warning if a measurement crosses
        one of its configured thresholds.
        """

        if (
            lower_threshold is not None
            and value < lower_threshold
        ):
            print(
                f"WARNING: {parameter.full_name} = {value} "
                f"is below lower threshold "
                f"{lower_threshold}"
            )

        if (
            upper_threshold is not None
            and value > upper_threshold
        ):
            print(
                f"WARNING: {parameter.full_name} = {value} "
                f"is above upper threshold "
                f"{upper_threshold}"
            )


    def stop(self):
        """
        Request the monitoring loop to stop.
        """

        self._running = False


    @property
    def running(self):
        """
        Public way for LivePlotter to check
        whether monitoring is active.
        """

        return self._running


    def run(self, duration=None):
        """
        Start monitoring.

        duration:
            Number of seconds to monitor.

            If None, run until stop() is called
            or the user presses Ctrl+C.
        """
        initialise_or_create_database_at(self.database_path)

        experiment = load_or_create_experiment(
            experiment_name=self.experiment_name,
            sample_name=self.sample_name,
        )

        measurement = Measurement(
            exp=experiment,
            name="monitoring_run",
        )

        # QCoDeS parameter representing elapsed time
        elapsed_time = Parameter(
            "elapsed_time",
            label="Elapsed Time",
            unit="s",
            get_cmd=None,
            set_cmd=None,
        )

        measurement.register_parameter(
            elapsed_time
        )

        # Register every monitored parameter
        # with elapsed time as its setpoint
        for info in self.monitored_parameters:

            measurement.register_parameter(
                info["parameter"],
                setpoints=(elapsed_time,),
            )

        start_time = time.monotonic()

        # All parameters are ready to be read immediately
        for info in self.monitored_parameters:
            info["next_read_time"] = start_time

        self._running = True

        try:

            with measurement.run() as datasaver:

                # Make current DataSet accessible
                self.dataset = datasaver.dataset

                while self._running:

                    now = time.monotonic()

                    elapsed = (
                        now - start_time
                    )

                    # Stop after requested duration
                    if (
                        duration is not None
                        and elapsed >= duration
                    ):
                        break

                    for info in self.monitored_parameters:

                        if (
                            now
                            >= info["next_read_time"]
                        ):

                            parameter = info[
                                "parameter"
                            ]

                            try:

                                # Read QCoDeS parameter
                                value = parameter()

                                # Save permanently to SQLite
                                datasaver.add_result(
                                    (
                                        elapsed_time,
                                        elapsed,
                                    ),
                                    (
                                        parameter,
                                        value,
                                    ),
                                )

                                # Save temporarily in memory
                                # for LivePlotter
                                self._store_in_history(
                                    parameter,
                                    elapsed,
                                    value,
                                )

                                print(
                                    f"{elapsed:8.3f} s | "
                                    f"{parameter.full_name}: "
                                    f"{value}"
                                )

                                # Check alert thresholds
                                self._check_thresholds(
                                    parameter,
                                    value,
                                    info[
                                        "lower_threshold"
                                    ],
                                    info[
                                        "upper_threshold"
                                    ],
                                )

                            except (
                                TimeoutError,
                                ConnectionError,
                            ) as error:

                                print(
                                    f"{elapsed:8.3f} s | "
                                    f"ERROR reading "
                                    f"{parameter.full_name}: "
                                    f"{error}"
                                )

                            # Advance according to the
                            # requested sampling interval
                            info[
                                "next_read_time"
                            ] += info["interval"]

                    # Avoid busy-waiting at 100% CPU
                    time.sleep(0.01)

                return datasaver.dataset


        except KeyboardInterrupt:

            print(
                "\nMonitoring stopped by user."
            )


        finally:

            self._running = False