# ThermImPro v1.1
# Copyright (c) 2026 Mykola Melnyk
# Licensed under the GNU General Public License v3.0 (GPLv3)
# See LICENSE file for full license details


"""
ThermImPro main script.
"""


import matplotlib.pyplot as plt

from thermal_gui import ThermalGUI


def main() -> None:
    ThermalGUI.open_file()
    plt.show()


if __name__ == "__main__":
    main()
