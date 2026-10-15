import math
import matplotlib.pyplot as plt
from pathlib import Path

from qcodes.dataset import (
    initialise_or_create_database_at,
    load_by_id,
    load_experiment_by_name,
)

class LivePlotter:

    def __init__(
        self,
        monitor,
        parameters,
        refresh_interval=0.2,
    ):
        self.monitor = monitor
        self.parameters = parameters
        self.refresh_interval = refresh_interval


    def _clean_data(self, times, values):

        clean_times = []
        clean_values = []

        for t, value in zip(times, values):

            if t is None or value is None:
                continue

            if not isinstance(t, (int, float)):
                continue

            if not isinstance(value, (int, float)):
                continue

            if not math.isfinite(t):
                continue

            if not math.isfinite(value):
                continue

            clean_times.append(t)
            clean_values.append(value)

        return clean_times, clean_values


    def run(self):

        plt.ion()

        fig, axes = plt.subplots(
            len(self.parameters),
            1,
            figsize=(8, 8)
        )

        if len(self.parameters) == 1:
            axes = [axes]

        lines = []

        for axis, parameter in zip(
            axes,
            self.parameters
        ):

            line, = axis.plot([], [])

            axis.set_xlabel("Elapsed Time (s)")
            axis.set_ylabel(parameter.unit)
            axis.set_title(parameter.full_name)

            lines.append(line)

        plt.tight_layout()

        while self.monitor.running:

            for axis, line, parameter in zip(
                axes,
                lines,
                self.parameters
            ):

                try:
                    times, values = self.monitor.get_history(
                        parameter.full_name
                    )

                except KeyError:
                    continue

                times, values = self._clean_data(
                    times,
                    values
                )

                if len(times) == 0:
                    continue

                line.set_data(
                    times,
                    values
                )

                axis.relim()
                axis.autoscale_view()
                axis.margins(x=0.05,y=0.10,)
            fig.canvas.draw_idle()

            plt.pause(
                self.refresh_interval
            )

        plt.ioff()
        plt.close(fig)


class DatabasePlotter:

    def __init__(
        self,
        database_path="data/monitoring.db",
        experiment_name="Quantum Lab Monitoring",
        sample_name="Synthetic Quantum Setup",
    ):
        self.database_path = Path(database_path)
        self.experiment_name = experiment_name
        self.sample_name = sample_name

        initialise_or_create_database_at(
            self.database_path
        )


    def load_run(self, run_id):

        return load_by_id(run_id)

    def _load_experiment(self):

        return load_experiment_by_name(
        self.experiment_name,
        sample=self.sample_name,
        load_last_duplicate=True,
    )

    def list_recent_runs(self, limit=5):

        experiment = self._load_experiment()

        datasets = experiment.data_sets()

        if len(datasets) == 0:
            print("No runs found.")
            return []

    # Sort newest first
        datasets = sorted(
            datasets,
            key=lambda dataset: (
                dataset.run_timestamp_raw
                if dataset.run_timestamp_raw is not None
                else 0
            ),
            reverse=True,
        )

        recent = datasets[:limit]

        print("Recent runs:")

        for dataset in recent:

            started = dataset.run_timestamp()
            completed = dataset.completed_timestamp()

            print(
            f"Run ID: {dataset.run_id} | "
            f"Started: {started} | "
            f"Completed: {completed}"
            )

        return recent

    def show_parameters(self, dataset):

        data = dataset.get_parameter_data()

        print("Available parameters:")

        for name in data.keys():
            print(name)


    def get_parameter_data(
        self,
        dataset,
        parameter_name,
    ):

        data = dataset.get_parameter_data(
            parameter_name
        )

        parameter_data = data[
            parameter_name
        ]

        times = parameter_data[
            "elapsed_time"
        ]

        values = parameter_data[
            parameter_name
        ]

        return times, values


    def plot_parameter(
        self,
        dataset,
        parameter_name,
        ylabel=None,
        title=None,
    ):

        times, values = self.get_parameter_data(
            dataset,
            parameter_name
        )

        plt.figure(figsize=(8, 5))

        plt.plot(
            times,
            values
        )

        plt.xlabel("Elapsed Time (s)")

        if ylabel is not None:
            plt.ylabel(ylabel)

        if title is None:
            title = parameter_name

        plt.title(title)

        plt.tight_layout()
        plt.show()


    def plot_all(self, dataset):

        data = dataset.get_parameter_data()

        parameter_names = list(
            data.keys()
        )

        number_of_plots = len(
            parameter_names
        )

        if number_of_plots == 0:
            print("No data to plot.")
            return

        fig, axes = plt.subplots(
            number_of_plots,
            1,
            figsize=(8, 3 * number_of_plots)
        )

        if number_of_plots == 1:
            axes = [axes]

        for axis, parameter_name in zip(
            axes,
            parameter_names
        ):

            parameter_data = data[
                parameter_name
            ]

            times = parameter_data[
                "elapsed_time"
            ]

            values = parameter_data[
                parameter_name
            ]

            axis.plot(
                times,
                values
            )

            axis.set_xlabel(
                "Elapsed Time (s)"
            )

            axis.set_title(
                parameter_name
            )

        plt.tight_layout()
        plt.show()
    def load_latest_run(self):

        experiment = self._load_experiment()

        try:
            dataset = experiment.last_data_set()

            print(
            f"Loaded latest run: {dataset.run_id}"
        )

            return dataset

        except ValueError:

            print("No direct latest run found.")
            print("Trying recent-run fallback...")

        recent_runs = self.list_recent_runs(
            limit=1
        )

        if len(recent_runs) == 0:
            print("No runs available.")
            return None

        dataset = recent_runs[0]

        print(
            f"Loaded fallback run: {dataset.run_id}"
        )

        return dataset