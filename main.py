import matplotlib.pyplot as plt

from thermal_gui import ThermalGUI, open_file

def main():
    image = open_file()

    if image and image.raw is not None:
        window = ThermalGUI(image)
        plt.show()

if __name__ == "__main__":
    main()
