# qcodes_monitor_system

# QCoDeS Synthetic Monitoring System

A small monitoring system built with QCoDeS.

The system simulates two quantum-lab instruments:

- Synthetic microwave generator
- Synthetic cryostat controller

The monitor supports:

- configurable polling intervals
- noisy and drifting measurements
- simulated read failures
- connection/disconnection behavior
- threshold alerts
- QCoDeS/SQLite data storage
- live plotting using in-memory history
- plotting of stored database runs

## Requirements

- Python 3.12
- QCoDeS
- Matplotlib
- pytest

## Setup

Create and activate a Conda environment:

```bash
conda create -n qcodes python=3.12
conda activate qcodes
