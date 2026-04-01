# ThermImPro - Thermal Image Processing
# Copyright (C) 2026 Mykola Melnyk

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
Module for loading and processing FLIR radiometric thermal images.
Includes ThermalImage class and temperature conversion functions.
"""


from dataclasses import dataclass, field
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
    External parameters, calibration parameters, and coefficients for
    raw-to-temperature conversion.

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
    tau : float
        Atmospheric transmission.
    ra : float
        Atmospheric radiance.
    rr : float
        Reflected radiance.
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
    tau: float = field(init=False)
    ra: float = field(init=False)
    rr: float = field(init=False)

    def __post_init__(self: Self) -> None:
        """
        Compute tau (atmospheric transmission), ra (atmospheric
        radiance), and rr (reflected radiance).
        """

        h2o = self.rh * np.exp(1.5587+0.06939*self.at-0.00027816*self.at**2
            +0.00000068455*self.at**3)
        self.tau = self.atx*np.exp(-np.sqrt(self.od)*(self.ata1+self.atb1
            *np.sqrt(h2o))) + (1.0-self.atx)*np.exp(-np.sqrt(self.od)
            *(self.ata2+self.atb2*np.sqrt(h2o)))
        self.ra = self.pr1/(self.pr2*(np.exp(self.pb/(self.at+273.15))
            -self.pf)) - self.po
        self.rr = self.pr1/(self.pr2*(np.exp(self.pb/(self.rat+273.15))
            -self.pf)) - self.po


class ThermalImage:
    """
    Represents thermal image data obtained from a radiometric thermal
    image.

    Extracts raw thermal data, and converts it to Kelvin, Celsius, and
    Fahrenheit.
    """
    
    def __init__(self: Self, file_path: str) -> None:
        """
        Initialize a ThermalImage instance from the radiometric input.
        """

        self.file_path: str = file_path

        data = self._extract_raw_data()
        self.shape: tuple[int, int] = data.shape

        self.metadata: dict[str, float] = {}
        self._extract_metadata()
        mdata = self._parse_metadata()

        self.kelvin: np.ndarray = to_kelvin(raw=data, m=mdata)
        self.celsius: np.ndarray = to_celsius(self.kelvin)
        self.fahrenheit: np.ndarray = to_fahrenheit(self.celsius)

        self.plot_data: np.ndarray = to_celsius(
            to_kelvin(raw=np.arange(RANGE_16BIT), m=mdata)
        )

    def _extract_raw_data(self: Self) -> np.ndarray:
        """
        Extract raw thermal data from the radiometric input using
        ExifTool.
        """
        
        try:
            process = subprocess.run(
                args=["exiftool", "-rawthermalimage", "-b", self.file_path],
                capture_output=True, check=True
            )
        except FileNotFoundError:
            raise RuntimeError("ExifTool not installed or missing from PATH")
        except subprocess.CalledProcessError:
            raise RuntimeError("ExifTool failed to process the file")

        if not process.stdout:
            raise ValueError("No data extracted from the file")

        raw_image = cv2.imdecode(
            buf=np.frombuffer(buffer=process.stdout, dtype=np.uint8),
            flags=cv2.IMREAD_UNCHANGED
        )

        if raw_image is None:
            raise ValueError("No data decoded")
        if raw_image.dtype != np.uint16:
            raise ValueError("Invalid raw thermal image format")

        # Endianness check (in case of MM or format other than TIFF swap bytes)
        if process.stdout[:2] != b"II":
            raw_image = raw_image.byteswap()
        
        return raw_image.astype(np.float32)
    
    def _extract_metadata(self: Self) -> None:
        """
        Extract metadata from the radiometric input using ExifTool.
        """

        process = subprocess.run(
            args=["exiftool", self.file_path], capture_output=True, text=True
        )

        for line in process.stdout.splitlines():
            if len(self.metadata) >= len(METADATA_KEYS):
                break

            parts = line.split(":")
            key = parts[0].strip()

            if key in METADATA_KEYS:
                value = float(parts[1].split()[0])
                self.metadata[key] = value

    def _parse_metadata(self: Self) -> Metadata:
        """Parse metadata into a Metadata instance."""

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
            pr2=self.metadata["Planck R2"]
        )


def to_kelvin(raw: np.ndarray, m: Metadata) -> np.ndarray:
    """Convert the raw thermal data to Kelvin."""

    obj_signal = (raw-m.ra*(1.0-m.tau)-(m.rr*m.tau*(1.0-m.e))) / (m.e*m.tau)

    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(
            obj_signal > 0.0,
            m.pb / np.log(m.pr1/(m.pr2*(obj_signal+m.po))+m.pf),
            np.nan
        )


def to_celsius(kelvin: np.ndarray) -> np.ndarray:
    """Convert thermal data in Kelvin to Celsius."""

    return kelvin - 273.15


def to_fahrenheit(celsius: np.ndarray) -> np.ndarray:
    """Convert thermal data in Celsius to Fahrenheit."""

    return celsius*9.0/5.0 + 32.0
