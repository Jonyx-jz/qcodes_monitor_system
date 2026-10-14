import threading

from instruments import (
    SyntheticMicrowaveGenerator,
    SyntheticCryostatController,
)

from monitor import Monitor
from plotting import LivePlotter


generator = SyntheticMicrowaveGenerator(
    "mw_gen_plot_test",
    failure_probability=0.0,
)

cryostat = SyntheticCryostatController(
    "cryostat_plot_test",
    failure_probability=0.0,
)


monitor = Monitor(
    database_path="data/plot_test.db"
)

monitor.add_parameter(
    generator.measured_frequency,
    interval=0.5,
)

monitor.add_parameter(
    generator.measured_power,
    interval=1.0,
)

monitor.add_parameter(
    cryostat.measured_temperature,
    interval=0.25,
)


plotter = LivePlotter(
    monitor,
    parameters=[
        generator.measured_frequency,
        generator.measured_power,
        cryostat.measured_temperature,
    ],
    refresh_interval=0.1,
)


monitor_thread = threading.Thread(
    target=monitor.run,
    kwargs={"duration": 10},
)

monitor_thread.start()

plotter.run()

monitor_thread.join()

generator.close()
cryostat.close()