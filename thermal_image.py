from dataclasses import dataclass
from typing import Self
import subprocess

import numpy as np
import cv2


METADATA_KEYS = {
    "Emissivity",
    "Object Distance",
    "Reflected Apparent Temperature",
    "Atmospheric Temperature",
    "Relative Humidity",
    "Atmospheric Trans Alpha 1",
    "Atmospheric Trans Alpha 2",
    "Atmospheric Trans Beta 1",
    "Atmospheric Trans Beta 2",
    "Atmospheric Trans X",
    "Planck R1",
    "Planck B",
    "Planck F",
    "Planck O",
    "Planck R2"
}
RANGE_16BIT = 65536


@dataclass
class Metadata:
    """
    External and calibration parameters for raw-to-temperature
    conversion.

    Attributes
    ----------
    e : float
        Emissivity factor of the object.
    od : float
        Object distance in metres.
    rat : float
        Reflected apparent temperature in °C.
    at : float
        Atmospheric temperature in °C.
    rh : float
        Relative humidity as a fraction (0–1).
    ata1 : float
        Attenuation constant Alpha 1 for atmosphere without water
        vapour.
    ata2 : float
        Attenuation constant Alpha 2 for atmosphere without water
        vapour.
    atb1 : float
        Attenuation constant Beta 1 for water vapour.
    atb2 : float
        Attenuation constant Beta 2 for water vapour.
    atx : float
        Scaling factor X for attenuation.
    pr1 : float
        Calibration constant Planck R1.
    pb : float
        Calibration constant Planck B.
    pf : float
        Calibration constant Planck F.
    po : float
        Calibration constant Planck O.
    pr2 : float
        Calibration constant Planck R2.
    """

    e: float
    od: float
    rat: float
    at: float
    rh: float
    ata1: float
    ata2: float
    atb1: float
    atb2: float
    atx: float
    pr1: float
    pb: float
    pf: float
    po: float
    pr2: float


class ThermalImage:
    """."""
    
    def __init__(self: Self, file_path: str) -> None:
        """Initialize ThermalImage from the given file path."""

        self.file_path = file_path
        self.raw_image = None
        self.width = None
        self.height = None
        self.metadata = None
        self.temp_k = None
        self.temp_c = None
        self.temp_f = None

        self._extract_raw_thermal_image()
        self._convert_image()

    def _extract_raw_thermal_image(self: Self) -> None:
        """
        Extract and load raw thermal image and metadata from the given
        radiometric thermal image using exiftool.
        """
        
        with open("out.png", "wb") as file:
            subprocess.run(
                ["exiftool", "-rawthermalimage", "-b", self.file_path],
                stdout=file
            )
        raw_image = cv2.imread(
            filename="out.png", flags=cv2.IMREAD_UNCHANGED
        )

        if raw_image is None:
            raise ValueError("File is empty")
        if raw_image.dtype != np.uint16:
            raise ValueError(
                "Unsupported image format (expected 16-bit)"
            )
        
        self.raw_image = raw_image.astype(np.float32)
        self.height, self.width = raw_image.shape

        self._load_metadata()

    def _load_metadata(self: Self) -> None:
        """Load metadata from a JSON file."""

        self.metadata = {}

        process = subprocess.run(
            ["exiftool", self.file_path], capture_output=True, text=True
        )

        for line in process.stdout.splitlines():
            key = line.split(":")[0].strip()
            if key in METADATA_KEYS:
                print(line)
                value = line.split(":")[1].strip()
                value = float(value.split(" ")[0])
                self.metadata[key] = value

    def _convert_image(self: Self) -> None:
        """
        Convert the raw image to thermal images (in Kelvin, Celsius, and
        Fahrenheit).
        """

        mdata = self._extract_metadata()
        self._to_kelvin(mdata)
        self._to_celsius()
        self._to_fahrenheit()
        self._compute_plot_data(mdata)

    def _extract_metadata(self: Self) -> Metadata:
        """
        Extract external and calibration parameters from metadata into
        a Metadata instance.
        """

        return Metadata(
            e=self.metadata["Emissivity"],
            od=self.metadata["Object Distance"],
            rat=self.metadata["Reflected Apparent Temperature"],
            at=self.metadata["Atmospheric Temperature"],
            rh=self.metadata["Relative Humidity"],
            ata1=self.metadata["Atmospheric Trans Alpha 1"],
            ata2=self.metadata["Atmospheric Trans Alpha 2"],
            atb1=self.metadata["Atmospheric Trans Beta 1"],
            atb2=self.metadata["Atmospheric Trans Beta 2"],
            atx=self.metadata["Atmospheric Trans X"],
            pr1=self.metadata["Planck R1"],
            pb=self.metadata["Planck B"],
            pf=self.metadata["Planck F"],
            po=self.metadata["Planck O"],
            pr2=self.metadata["Planck R2"],
        )

    def _compute_temp_vars(self: Self, m: Metadata) -> tuple[float, ...]:
        """
        Compute intermediate values for raw-to-temperature conversion:

        tau : atmospheric transmission
        ra : atmospheric radiance
        rr : reflected radiance
        """

        h2o = m.rh * np.exp(1.5587+0.06939*m.at-0.00027816*m.at**2.0
              +0.00000068455*m.at**3.0)
        tau = (m.atx*np.exp(-np.sqrt(m.od)*(m.ata1+m.atb1*np.sqrt(h2o)))
               + (1.0-m.atx)*np.exp(-np.sqrt(m.od)*(m.ata2+m.atb2
               *np.sqrt(h2o))))
        ra = m.pr1/(m.pr2*(np.exp(m.pb/(m.at+273.15))-m.pf)) - m.po
        rr = m.pr1/(m.pr2*(np.exp(m.pb/(m.rat+273.15))-m.pf)) - m.po

        return (tau, ra, rr)

    def _convert_to_temp_k(self: Self, signal: np.ndarray, m: Metadata) -> None:
        """
        Convert object signal to temperature in Kelvin using Planck's
        law.
        """

        with np.errstate(divide="ignore", invalid="ignore"):
            kelvin = np.where(
                signal > 0.0,
                m.pb / np.log(m.pr1/(m.pr2*(signal+m.po))+m.pf),
                np.nan
            )
        
        return kelvin
    
    def _to_kelvin(self: Self, mdata: Metadata) -> None:
        """Convert the raw image to a thermal image in Kelvin."""

        tau, ra, rr = self._compute_temp_vars(mdata)
        obj_signal = ((self.raw_image-ra*(1.0-tau)-(rr*tau*(1.0-mdata.e)))
                      / (mdata.e*tau))
        self.temp_k = self._convert_to_temp_k(signal=obj_signal, m=mdata)

    def _to_celsius(self: Self) -> None:
        """Convert the thermal image from Kelvin to Celsius."""

        self.temp_c = self.temp_k - 273.15

    def _to_fahrenheit(self: Self) -> None:
        """Convert the thermal image from Celsius to Fahrenheit."""

        self.temp_f = self.temp_c*9.0/5.0 + 32

    def _compute_plot_data(self: Self, mdata: Metadata) -> None:
        obj_signal = np.arange(RANGE_16BIT)
        temp_k = self._convert_to_temp_k(signal=obj_signal, m=mdata)
        self.plot_data = (obj_signal, temp_k- 273.15)
    
    def _swap_byte_order(self: Self) -> None:
        """."""

        self.raw_image = self.raw_image.astype(np.uint16).byteswap()
        self.raw_image = self.raw_image.astype(np.float32)
        self._convert_image()
