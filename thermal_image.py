import os
import tkinter as tk
import json

import numpy as np
import cv2

class ThermalImage:
    def __init__(self, path: str):
        self.path = path
        self.raw = None

        self._load_image()

        if self.raw is not None:
            if self.dtype == np.float32:
                self.tempc = self.raw

            else:
                self._load_metadata()
                self.raw_to_tempc()

            self.tempc_to_tempf()

    def _load_image(self):
        """
        Load an image and store it in `self.raw`, with its data type
        recorded in `self.dtype`.

        The method supports two formats:
        - `.raw`, 32-bit float (float32) data of fixed size 640×480
        - standard image files (e.g., PNG, TIFF) with 16-bit depth
        """

        ext = os.path.splitext(self.path)[1].lower()

        try:
            if ext == ".raw":
                raw_data = np.fromfile(file=self.path, dtype="<f4")
                raw_image = raw_data.reshape((480, 640))

            else:
                raw_image = cv2.imread(filename=self.path, flags=2)
                
                if raw_image.dtype != np.uint16:
                    raise TypeError(
                        "unsupported image format (expected 16-bit)"
                    )

            self.raw = raw_image
            self.dtype = self.raw.dtype

        except Exception as error:
            tk.messagebox.showerror(
                title="Image Load Error",
                message="Could not open image file. "
                        f"{type(error).__name__}: {error}."
            )

    def _load_metadata(self):
        """Load metadata from a JSON file."""

        with open("metadata.json") as file:
            self.metadata = json.loads(file.read())

    def raw_to_tempc(self, values = None):
        """
        
        """

        emiss = self.metadata["Emissivity"]
        obj_dist = self.metadata["Object Distance"]
        refl_app_temp = self.metadata["Reflected Apparent Temperature"]
        atm_temp = self.metadata["Atmospheric Temperature"]
        rel_hum = self.metadata["Relative Humidity"]
        atm_trans_a_1 = self.metadata["Atmospheric Trans Alpha 1"]
        atm_trans_a_2 = self.metadata["Atmospheric Trans Alpha 2"]
        atm_trans_b_1 = self.metadata["Atmospheric Trans Beta 1"]
        atm_trans_b_2 = self.metadata["Atmospheric Trans Beta 2"]
        atm_trans_x = self.metadata["Atmospheric Trans X"]
        planck_r1 = self.metadata["Planck R1"]
        planck_b = self.metadata["Planck B"]
        planck_f = self.metadata["Planck F"]
        planck_o = self.metadata["Planck O"]
        planck_r2 = self.metadata["Planck R2"]

        h2o = rel_hum * np.exp(1.5587 + 0.06939 * atm_temp - 0.00027816 * atm_temp**2 + 0.00000068455 * atm_temp**3)
        tau = atm_trans_x * np.exp(-np.sqrt(obj_dist) * (atm_trans_a_1 + atm_trans_b_1 * np.sqrt(h2o))) + (1 - atm_trans_x) * np.exp(-np.sqrt(obj_dist) * (atm_trans_a_2 + atm_trans_b_2 * np.sqrt(h2o)))
        raw_atm = planck_r1 / (planck_r2 * (np.exp(planck_b / (atm_temp + 273.15)) - planck_f)) - planck_o
        raw_refl = planck_r1 / (planck_r2 * (np.exp(planck_b / (refl_app_temp + 273.15)) - planck_f)) - planck_o
        raw_refl_term = raw_refl * tau * (1-emiss)

        if values is not None:
            raw_obj_vals = (values - raw_atm * (1 - tau) - raw_refl_term) / (emiss * tau)

            with np.errstate(invalid = "ignore", divide = "ignore"):
                temp_vals = np.where(
                    raw_obj_vals > 0,
                    planck_b / np.log(planck_r1 / (planck_r2 * (raw_obj_vals + planck_o)) + planck_f) - 273.15,
                    np.nan
                )

            return temp_vals

        raw_obj = (self.raw.astype(np.float32) - raw_atm * (1 - tau) - raw_refl_term) / (emiss * tau)
        self.tempc = planck_b / np.log(planck_r1 / (planck_r2 * (raw_obj + planck_o)) + planck_f) - 273.15

    def tempc_to_tempf(self):
        """
        Convert `self.tempc` to Fahrenheit and store the result in
        `self.tempf`.
        """

        self.tempf = self.tempc*9/5 + 32
