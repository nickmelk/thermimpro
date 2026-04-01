# ThermImPro v1.1
# Copyright (c) 2026 Mykola Melnyk
# Licensed under the GNU General Public License v3.0 (GPLv3)
# See LICENSE file for full license details

"""

"""

from typing import Self, Any
from datetime import datetime
import os
import tkinter as tk
from tkinter import filedialog

import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.widgets as wdg
import numpy as np
from matplotlib.colorbar import Colorbar
from matplotlib.backend_bases import DrawEvent, ResizeEvent, MouseEvent
from matplotlib.lines import Line2D

from thermal_image import ThermalImage


DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_VMAX = 99
DEFAULT_VMIN = 1
CMAPS = {
    "Grayscale": "gray",
    "Ironbow": "inferno",
    "Rainbow": "jet",
    "Glowbow": "hot"
}


class ThermalGUI:
    def __init__(self: Self) -> None:
        """."""

        self.window: plt.Figure | None = None
        self.image_panel: plt.Axes | None = None
        self.graph_panel: plt.Axes | None = None
        self.info_panel: plt.Axes | None = None
        self.open_button_container: Any | None = None
        self.save_button_container: Any | None = None
        self.palette_radio_container: Any | None = None
        self.vmax_slider_container: Any | None = None
        self.vmin_slider_container: Any | None = None
        self.hotspot_button_container: Any | None = None
        self.coldspot_button_container: Any | None = None
        self.open_button: wdg.Button | None = None
        self.save_button: wdg.Button | None = None
        self.palette_radio: wdg.RadioButtons | None = None
        self.vmax_slider: wdg.Slider | None = None
        self.vmin_slider: wdg.Slider | None = None
        self.hotspot_button: wdg.Button | None = None
        self.coldspot_button: wdg.Button | None = None
        self.image: plt.AxesImage | None = None
        self.colorbar: plt.Colorbar | None = None
        self.crosshair_cursor_bg: Line2D | None = None
        self.crosshair_cursor_fg: Line2D | None = None
        self.hotspot_marker: Line2D | None = None
        self.coldspot_button: Line2D | None = None
        self.metadata_text: plt.Text | None = None
        self.max_temperature_text: plt.Text | None = None
        self.min_temperature_text: plt.Text | None = None
        self.avg_temperature_text: plt.Text | None = None
        self.temperature_text: plt.Text | None = None
        self.footer_text: plt.Text | None = None
        self.bg: Any | None = None
        self.data: ThermalImage | None = None
        self.limits: Any | None = None

        self._create_window()
        self._create_layout()
        self._create_widgets()
        self._init_display()
        self._create_texts()
        self._bind_events()

    @classmethod
    def open_file(cls: type[Self], window: Self | None = None) -> None:
        """
        Creates and returns a ThermalImage object from an image selected
        in a file dialog.

        If no file is chosen, returns None. If a window is provided, its
        image is replaced and the view is updated.
        """

        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image Files", "*.jpeg *.jpg *.png *.tif *.tiff")
            ]
        )

        if not file_path:
            return

        try:
            image = ThermalImage(file_path)
        except Exception as error:
            tk.messagebox.showerror(
                title="ThermImPro", message=f"{type(error).__name__}: {error}."
            )
            return

        if window is None:
            window = ThermalGUI()
        window._update_gfx(image)

    def _create_window(self: Self) -> None:
        """Create the main application window."""

        plt.style.use("dark_background")
        self.window = plt.figure(num="ThermImPro", figsize=(14.0, 7.0))

        gridspec = self.window.add_gridspec(nrows=3, ncols=3)

        self.image_panel = self.window.add_subplot(gridspec[:, :2])
        self.graph_panel = self.window.add_subplot(gridspec[0, 2])
        self.info_panel = self.window.add_subplot(gridspec[1:, 2])

        self.window.subplots_adjust(left=0.14, right=0.98, wspace=0.42)

        for panel in self.window.axes:
            panel.axis("off")

    def _create_layout(self: Self) -> None:
        """Create containers for widgets."""

        self.open_button_container = inset_axes(
            parent_axes=self.image_panel, width="20%", height="10%",
            loc="upper left", bbox_to_anchor=(-0.23, 0.008, 1.0, 1.0),
            bbox_transform=self.image_panel.transAxes
        )
        self.save_button_container = inset_axes(
            parent_axes=self.image_panel, width="20%", height="10%",
            loc="upper left", bbox_to_anchor=(-0.23, -0.12, 1.0, 1.0),
            bbox_transform=self.image_panel.transAxes
        )
        self.palette_radio_container = inset_axes(
            parent_axes=self.image_panel, width="20%", height="27%",
            loc="upper left", bbox_to_anchor=(-0.23, -0.248, 1.0, 1.0),
            bbox_transform=self.image_panel.transAxes,
            axes_kwargs={"fc": "dimgray"}
        )
        self.vmax_slider_container = inset_axes(
            parent_axes=self.image_panel, width="14%", height="3%",
            loc="upper left", bbox_to_anchor=(-0.23, -0.578, 1.0, 1.0),
            bbox_transform=self.image_panel.transAxes
        )
        self.vmin_slider_container = inset_axes(
            parent_axes=self.image_panel, width="14%", height="3%",
            loc="upper left", bbox_to_anchor=(-0.23, -0.618, 1.0, 1.0),
            bbox_transform=self.image_panel.transAxes
        )
        self.hotspot_button_container = inset_axes(
            parent_axes=self.image_panel, width="9%", height="6%",
            loc="upper left", bbox_to_anchor=(-0.23, -0.668, 1.0, 1.0),
            bbox_transform=self.image_panel.transAxes
        )
        self.coldspot_button_container = inset_axes(
            parent_axes=self.image_panel, width="9%", height="6%",
            loc="upper left", bbox_to_anchor=(-0.12, -0.668, 1.0, 1.0),
            bbox_transform=self.image_panel.transAxes
        )

    def _create_widgets(self: Self) -> None:
        """Create widgets."""

        self.open_button = wdg.Button(
            ax=self.open_button_container, label="Open",
            color="dimgray", hovercolor="dimgray"
        )
        self.save_button = wdg.Button(
            ax=self.save_button_container, label="Save",
            color="dimgray", hovercolor="dimgray"
        )
        self.palette_radio = wdg.RadioButtons(
            ax=self.palette_radio_container,
            labels=("Grayscale", "Ironbow", "Rainbow", "Glowbow"),
            active=1, activecolor="green"
        )
        self.vmax_slider = wdg.Slider(
            ax=self.vmax_slider_container, label="",
            valmin=0.0, valmax=100.0, valinit=DEFAULT_VMAX,
            valfmt="%4d%%", valstep=1.0, initcolor="none",
            handle_style={"edgecolor": "dimgray"}, fc="orchid"
        )
        self.vmin_slider = wdg.Slider(
            ax=self.vmin_slider_container, label="",
            valmin=0.0, valmax=100.0, valinit=DEFAULT_VMIN,
            valfmt="%4d%%", valstep=1.0, initcolor="none",
            handle_style={"edgecolor": "dimgray"}, fc="orchid"
        )
        self.hotspot_button = wdg.Button(
            ax=self.hotspot_button_container, label="HOT",
            color="red", hovercolor="red"
        )
        self.coldspot_button = wdg.Button(
            ax=self.coldspot_button_container, label="COLD",
            color="blue", hovercolor="blue"
        )

        self.vmax_slider.slidermin = self.vmin_slider
        self.vmin_slider.slidermax = self.vmax_slider

    def _init_display(self: Self) -> None:
        """Initialize the image display and its elements."""

        self.image = self.image_panel.imshow(
            X=np.zeros((DEFAULT_HEIGHT, DEFAULT_WIDTH)),
            cmap="inferno", aspect="auto"
        )

        self.crosshair_cursor_bg, = self.image_panel.plot(
            [], [], animated=True, c="black", marker="+", mew=2.5, ms=13.5
        )
        self.crosshair_cursor_fg, = self.image_panel.plot(
            [], [], animated=True, c="white", marker="+", ms=12.0
        )

        self.hotspot_marker, = self.image_panel.plot(
            [], [], c="red", marker="+", mew=2.5, ms=13.5, visible=False
        )
        self.coldspot_marker, = self.image_panel.plot(
            [], [], c="blue", marker="+", mew=2.5, ms=13.5, visible=False
        )

        colorbar_container = inset_axes(
            parent_axes=self.image_panel, width="3%", height="100%",
            loc="right", bbox_to_anchor=(0.05, 0.0, 1.0, 1.0),
            bbox_transform=self.image_panel.transAxes
        )
        self.colorbar = Colorbar(
            ax=colorbar_container, mappable=self.image,
            format="%d", label="Temperature, °C"
        )
    
    def _create_texts(self: Self) -> None:
        """Create text elements."""

        self.image_panel.text(
            x=-0.17, y=0.446, s="Threshold", family="monospace",
            transform=self.image_panel.transAxes, va="top"
        )
        self.metadata_text = self.info_panel.text(
            x=-0.1, y=0.9, s="", family="monospace", va="top"
        )
        self.max_temperature_text = self.image_panel.text(
            x=-0.225, y=0.235, s="", family="monospace",
            transform=self.image_panel.transAxes, va="top"
        )
        self.min_temperature_text = self.image_panel.text(
            x=-0.115, y=0.235, s="", family="monospace",
            transform=self.image_panel.transAxes, va="top"
        )
        self.avg_temperature_text = self.image_panel.text(
            x=-0.170, y=0.11, s="", family="monospace",
            transform=self.image_panel.transAxes, va="top"
        )
        self.temperature_text = self.image_panel.text(
            x=1.0, y=-0.05, s="", animated=True, ha="right",
            transform=self.image_panel.transAxes
        )
        self.footer_text = self.window.text(
            x=0.992, y=0.03,
            s="ThermImPro v1.1\nCopyright ©2026 Mykola Melnyk",
            size=8.0, ha="right"
        )

    def _bind_events(self: Self) -> None:
        """Bind events to handlers."""

        self.window.canvas.mpl_connect(s="draw_event", func=self._on_draw)
        self.window.canvas.mpl_connect(s="resize_event", func=self._on_resize)
        self.window.canvas.mpl_connect(
            s="motion_notify_event", func=self._on_move
        )

        self.open_button.on_clicked(lambda _: self.open_file(self))
        self.save_button.on_clicked(self._save_file)
        self.palette_radio.on_clicked(self._set_palette)
        self.vmax_slider.on_changed(
            lambda value: self._set_clim(clim="vmax", val=value)
        )
        self.vmin_slider.on_changed(
            lambda value: self._set_clim(clim="vmin", val=value)
        )
        self.hotspot_button.on_clicked(
            lambda _: self._toggle_marker(self.hotspot_marker)
        )
        self.coldspot_button.on_clicked(
            lambda _: self._toggle_marker(self.coldspot_marker)
        )

    def _on_draw(self: Self, _: DrawEvent) -> None:
        """Cache the window background on draw events."""

        self.bg = self.window.canvas.copy_from_bbox(self.window.bbox)

    def _on_resize(self: Self, _: ResizeEvent) -> None:
        """Scale text elements on resize events."""

        width = self.window.get_figwidth() * self.window.dpi
        scale = np.clip(a=width/1920.0, a_min=0.5, a_max=2.0)

        for text in self.window.findobj(matplotlib.text.Text):
            size = 10.0 if text is self.footer_text else 12.0
            text.set_fontsize(scale*size)

        self.window.canvas.draw_idle()

    def _on_move(self: Self, event: MouseEvent) -> None:
        """
        Update the crosshair cursor position and temperature text on
        mouse movement.
        """
        
        is_in_image_panel = event.inaxes is self.image_panel

        if is_in_image_panel:
            xdata = np.clip(
                a=event.xdata, a_min=0.0, a_max=self.data.shape[1]-1.0
            )
            ydata = np.clip(
                a=event.ydata, a_min=0.0, a_max=self.data.shape[0]-1.0
            )

            self._update_cursor_position(x=xdata, y=ydata)
            self._update_temperature_text(x=int(xdata), y=int(ydata))
        
        self.window.canvas.restore_region(self.bg)

        for artist in (self.crosshair_cursor_bg, self.crosshair_cursor_fg,
                self.temperature_text):
            artist.set_visible(is_in_image_panel)

            if is_in_image_panel:
                self.image_panel.draw_artist(artist)
        
        self.window.canvas.blit(self.window.bbox)

    def _update_cursor_position(self: Self, x: float, y: float) -> None:
        """Update the crosshair cursor position."""

        self.crosshair_cursor_bg.set_data([x], [y])
        self.crosshair_cursor_fg.set_data([x], [y])

    def _update_temperature_text(self: Self, x: int, y: int) -> None:
        """
        Update the temperature text with the value in (x, y).
        """

        temp_c = self.data.celsius[y, x]
        temp_f = self.data.fahrenheit[y, x]
        temp_k = self.data.kelvin[y, x]

        self.temperature_text.set_text(
            f"Temperature: {temp_c:.2f} °C / {temp_f:.2f} °F / {temp_k:.2f} K"
        )
    
    def _save_file(self: Self, _: MouseEvent) -> None:
        """Export the thermal image as a PNG file."""

        os.makedirs(name="saves", exist_ok=True)

        filename = datetime.now().strftime("%Y%m%d%H%M%S")
        vmin, vmax = int(self.vmin_slider.val), int(self.vmax_slider.val)

        plt.imsave(
            fname=f"saves/{filename}.png", arr=self.data.celsius,
            vmin=self.limits[vmin], vmax=self.limits[vmax],
            cmap=self.image.get_cmap()
        )
    
    def _set_palette(self: Self, palette: str) -> None:
        """Set the colormap and reset the image color limits."""

        self.image.set_cmap(CMAPS[palette])
        self._reset_clim()

        self.window.canvas.draw_idle()

    def _reset_clim(self: Self) -> None:
        """Reset the image color limits and sliders."""

        self.image.set_clim(
            vmin=self.limits[DEFAULT_VMIN], vmax=self.limits[DEFAULT_VMAX]
        )

        self.vmax_slider.reset()
        self.vmin_slider.reset()

    def _set_clim(self: Self, clim: str, val: float) -> None:
        """Set the image color limits."""

        if clim == "vmax":
            self.image.set_clim(vmax=self.limits[int(val)])
        else:
            self.image.set_clim(vmin=self.limits[int(val)])
        
        self.window.canvas.draw_idle()

    def _toggle_marker(self: Self, marker: Line2D) -> None:
        """Toggle the visibility of the marker."""

        marker.set_visible(not marker.get_visible())
        
        self.window.canvas.draw_idle()
    
    def _update_gfx(self: Self, image: ThermalImage) -> None:
        """."""

        self.data = image
        self.limits = np.percentile(a=self.data.celsius, q=np.arange(101))

        self.image.set_data(self.data.celsius)

        self._reset_clim()
        self.palette_radio.set_active(1)

        self._update_marker_positions()
        self._set_texts()

        self.image.set_extent(
            (-0.5, self.data.shape[1]-0.5, self.data.shape[0]-0.5, -0.5)
        )

        self.calibration_curve()
        self.metadata_text.set_text(
            "\n".join(
                f"{key + ':':35}{value}"
                for key, value in self.data.metadata.items()
            )
        )

        self.window.canvas.draw_idle()   

    def _update_marker_positions(self: Self) -> None:
        """Update the positions of the hotspot and coldspot markers."""

        indices = np.argmax(self.data.celsius), np.argmin(self.data.celsius)
        y, x = np.unravel_index(indices=indices, shape=self.data.shape)

        self.hotspot_marker.set_data([x[0]], [y[0]])
        self.coldspot_marker.set_data([x[1]], [y[1]])

        self.hotspot_marker.set_visible(False)
        self.coldspot_marker.set_visible(False)

    def _set_texts(self: Self) -> None:
        """."""

        self.max_temperature_text.set_text(
            f"{'MAX':^9}"
            f"\n{np.max(self.data.celsius):<6.2f} °C"
            f"\n{np.max(self.data.fahrenheit):<6.2f} °F"
            f"\n{np.max(self.data.kelvin):<7.2f} K"
        )
        self.min_temperature_text.set_text(
            f"{'MIN':^9}"
            f"\n{np.min(self.data.celsius):<6.2f} °C"
            f"\n{np.min(self.data.fahrenheit):<6.2f} °F"
            f"\n{np.min(self.data.kelvin):<7.2f} K"
        )
        self.avg_temperature_text.set_text(
            f"{'AVG':^9}"
            f"\n{np.mean(self.data.celsius):<6.2f} °C"
            f"\n{np.mean(self.data.fahrenheit):<6.2f} °F"
            f"\n{np.mean(self.data.kelvin):<7.2f} K"
        )

    def calibration_curve(self: Self) -> None:
        """."""

        self.graph_panel.clear()
        self.graph_panel.plot(self.data.plot_data, c="orange")
        self.graph_panel.set_title("Calibration Curve")
        self.graph_panel.set_xlabel("Digital Signal Output (Raw Pixel Value)")
        self.graph_panel.set_ylabel("Estimated Temperature (°C)")
        self.graph_panel.grid(True)
