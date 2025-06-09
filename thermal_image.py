from tkinter import messagebox

import cv2
import numpy as np

class ThermalImage:
    def __init__(self, metadata: dict):
        # External parameters
        self.emiss = metadata["Emissivity"]                                 # Emissivity
        self.obj_dist = metadata["Object Distance"]                         # Object Distance
        self.refl_app_temp = metadata["Reflected Apparent Temperature"]     # Reflected Apparent Temperature
        self.atm_temp = metadata["Atmospheric Temperature"]                 # Atmospheric Temperature
        self.rel_hum = metadata["Relative Humidity"]                        # Relative Humidity
        self.atm_trans_a_1 = metadata["Atmospheric Trans Alpha 1"]          # Atmospheric Trans Alpha 1
        self.atm_trans_a_2 = metadata["Atmospheric Trans Alpha 2"]          # Atmospheric Trans Alpha 2
        self.atm_trans_b_1 = metadata["Atmospheric Trans Beta 1"]           # Atmospheric Trans Beta 1
        self.atm_trans_b_2 = metadata["Atmospheric Trans Beta 2"]           # Atmospheric Trans Beta 2
        self.atm_trans_x = metadata["Atmospheric Trans X"]                  # Atmospheric Trans X

        # Calibration parameters (specific to each FLIR thermal camera)
        self.planck_r1 = metadata["Planck R1"]                              # Planck R1
        self.planck_b = metadata["Planck B"]                                # Planck B
        self.planck_f = metadata["Planck F"]                                # Planck F
        self.planck_o = metadata["Planck O"]                                # Planck O
        self.planck_r2 = metadata["Planck R2"]                              # Planck R2

        self.gray_16_image = None
        self.therm_image_c = None
        self.therm_image_f = None

    # Loading RAW(.raw) file
    def load_raw_file(self, file_path, width = 640, height = 480):
        raw_data = np.fromfile(file_path, dtype = "<f4")  # Reading binary data (little-endian 32-bit float)

        # frame_size = width * height

        self.gray_16_image = raw_data.reshape((height, width)) # when working with frames use [frame_size:]
        self.therm_image_c = self.gray_16_image
        self.therm_image_f = (self.therm_image_c * 9/5) + 32 # Calculating temperatures for the image in °F

        return self.gray_16_image, self.therm_image_c, self.therm_image_f

    # Loading 16-bit TIFF(.tiff)/PNG(.png) file
    def load_16_bit_file(self, file_path):
        self.gray_16_image = cv2.imread(file_path, cv2.IMREAD_ANYDEPTH)

        if self.gray_16_image is None:
            messagebox.showerror(title = "Error", message = "No image loaded! Please open a valid image file.")

            return None

        self.raw_to_temperature()

        return self.gray_16_image, self.therm_image_c, self.therm_image_f

    def raw_to_temperature(self, pixel_vals = None):
        # Converting relative humidity into vapour pressure of water
        h2o = self.rel_hum * np.exp(1.5587 + 0.06939 * self.atm_temp - 0.00027816 * self.atm_temp**2 + 0.00000068455 * self.atm_temp**3)

        # Transmission through atmosphere
        tau = self.atm_trans_x * np.exp(-np.sqrt(self.obj_dist) * (self.atm_trans_a_1 + self.atm_trans_b_1 * np.sqrt(h2o))) + (1 - self.atm_trans_x) * np.exp(-np.sqrt(self.obj_dist) * (self.atm_trans_a_2 + self.atm_trans_b_2 * np.sqrt(h2o)))
        
        raw_atm = self.planck_r1 / (self.planck_r2 * (np.exp(self.planck_b / (self.atm_temp + 273.15)) - self.planck_f)) - self.planck_o

        raw_atm_one_minus_tau = raw_atm * (1 - tau)

        # Radiance reflected from the object
        raw_refl = self.planck_r1 / (self.planck_r2 * (np.exp(self.planck_b / (self.refl_app_temp + 273.15)) - self.planck_f)) - self.planck_o
        raw_refl_term = raw_refl * tau * (1 - self.emiss)

        if pixel_vals is None:
            # Calculating object signal
            raw_obj = (self.gray_16_image.astype(np.float32) - raw_atm_one_minus_tau - raw_refl_term) / (self.emiss * tau)

            # Calculating temperatures for the image in °C
            self.therm_image_c = self.planck_b / np.log(self.planck_r1 / (self.planck_r2 * (raw_obj + self.planck_o)) + self.planck_f) - 273.15

            # Calculating temperatures for the image in °F
            self.therm_image_f = (self.therm_image_c * 9 / 5) + 32
        
        else:
            raw_obj_vals = (pixel_vals - raw_atm_one_minus_tau - raw_refl_term) / (self.emiss * tau)

            with np.errstate(invalid = "ignore", divide = "ignore"):
                temp_vals = np.where(
                    raw_obj_vals > 0,
                    self.planck_b / np.log(self.planck_r1 / (self.planck_r2 * (raw_obj_vals + self.planck_o)) + self.planck_f) - 273.15,
                    np.nan
                )

            return temp_vals
