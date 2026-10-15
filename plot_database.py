from plotting import DatabasePlotter


def main():

    database_plotter = DatabasePlotter(
        database_path="data/monitoring.db"
    )

    # Show recent runs
    database_plotter.list_recent_runs()

    # Load one run
    dataset = database_plotter.load_run(4)

    if dataset is None:
        print("No dataset available.")
        return

    # Show stored parameter names
    database_plotter.show_parameters(
        dataset
    )
    print(
        f"\nFinished plotting run "
        f"{dataset.run_id}"
    )
    # Plot all parameters
    database_plotter.plot_all(
        dataset
    )
    


if __name__ == "__main__":
    main()