import matplotlib.pyplot as plt

from thermal_gui import ThermalGUI


def main() -> None:
    ThermalGUI.open_file()
    plt.show()


if __name__ == "__main__":
    main()
