import time
import threading

from instruments import (
    SyntheticMicrowaveGenerator,
    SyntheticCryostatController,
)

from monitor import Monitor

from plotting import (
    LivePlotter,
    DatabasePlotter,
)


def main():

    # --------------------------------------------------
    # 1. Create synthetic instruments
    # --------------------------------------------------

    generator = SyntheticMicrowaveGenerator(
        "mw_gen",
        failure_probability=0.01,
    )

    cryostat = SyntheticCryostatController(
        "cryostat",
        failure_probability=0.01,
    )


    # --------------------------------------------------
    # 2. Create monitor
    # --------------------------------------------------

    monitor = Monitor(
        database_path="data/monitoring.db"
    )


    # --------------------------------------------------
    # 3. Register monitored parameters
    # --------------------------------------------------

    monitor.add_parameter(
        generator.measured_frequency,
        interval=1.0,
    )

    monitor.add_parameter(
        generator.measured_power,
        interval=2.0,
    )

    monitor.add_parameter(
        cryostat.measured_temperature,
        interval=0.5,
    )


    # --------------------------------------------------
    # 4. Create live plotter
    # --------------------------------------------------

    live_plotter = LivePlotter(
        monitor,
        parameters=[
            generator.measured_frequency,
            generator.measured_power,
            cryostat.measured_temperature,
        ],
        refresh_interval=0.2,
    )


    # --------------------------------------------------
    # 5. Start monitor in background thread
    # --------------------------------------------------

    monitor_thread = threading.Thread(
        target=monitor.run,
        kwargs={
            "duration": 30
        },
    )

    monitor_thread.start()


    # Give monitor time to enter its running state
    time.sleep(0.1)


    # --------------------------------------------------
    # 6. Run live plotting on main thread
    # --------------------------------------------------

    live_plotter.run()


    # --------------------------------------------------
    # 7. Wait for monitoring to finish
    # --------------------------------------------------

    monitor_thread.join()


    # --------------------------------------------------
    # 8. Close instruments
    # --------------------------------------------------

    generator.close()
    cryostat.close()


    # --------------------------------------------------
    # 9. Plot stored database data
    # --------------------------------------------------

    database_plotter = DatabasePlotter(
        database_path="data/monitoring.db"
    )

    dataset = database_plotter.load_latest_run()

    if dataset is not None:

        print(
            f"\nPlotting stored run "
            f"{dataset.run_id}"
        )

        database_plotter.plot_all(
            dataset
        )


if __name__ == "__main__":
    main()