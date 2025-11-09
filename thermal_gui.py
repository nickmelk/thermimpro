import datetime
import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.widgets as wdg
import numpy as np
from matplotlib.colors import Normalize
import matplotlib.image as mpimg

from thermal_image import ThermalImage

class ThermalGUI:
    def __init__(self, image: ThermalImage):
        plt.style.use("dark_background")

        self.window, ((self.raw_view, self.curve_panel), (self.thermal_view, self.misc_panel)) = plt.subplots(
            nrows=2,
            ncols=2,
            figsize=(14, 7),
            gridspec_kw={"left": 0.05,
                         "right": 0.95,
                         "top": 0.95,
                         "bottom": 0.05,
                         "wspace": 0.01
                        }
        )

        self.image = image

        self._build_layout()
        self._setup_images()
        self._init_display()

    def _build_layout(self):
        """Prepare inset axes for UI elements."""

        self.open_button_container = inset_axes(
            parent_axes=self.raw_view,
            width="30%",
            height="20%",
            loc="center left",
            bbox_to_anchor=(-0.355, 0, 1, 1),
            bbox_transform=self.raw_view.transAxes
        )
        self.palette_radio_container = inset_axes(
            parent_axes=self.thermal_view,
            width="30%",
            height="50%",
            loc="center left",
            bbox_to_anchor=(-0.355, 0, 1, 1),
            bbox_transform=self.thermal_view.transAxes,
            axes_kwargs={"fc": "dimgray"}
        )
        self.save_button_container = inset_axes(
            parent_axes=self.thermal_view,
            width="21%",
            height="20%",
            loc="lower left",
            bbox_to_anchor=(-0.355, -0.021, 1, 1),
            bbox_transform=self.thermal_view.transAxes
        )
        self.hotspot_button_container = inset_axes(
            parent_axes=self.thermal_view,
            width="6%",
            height="8%",
            loc="lower left",
            bbox_to_anchor=(-0.115, 0.1, 1, 1),
            bbox_transform=self.thermal_view.transAxes
        )
        self.coldspot_button_container = inset_axes(
            parent_axes=self.thermal_view,
            width="6%",
            height="8%",
            loc="lower left",
            bbox_to_anchor=(-0.115, -0.021, 1, 1),
            bbox_transform=self.thermal_view.transAxes
        )
        self.colorbar_container = inset_axes(
            parent_axes=self.thermal_view,
            width="5%",
            height="100%",
            loc="right",
            bbox_to_anchor=(0.1, 0, 1, 1),
            bbox_transform=self.thermal_view.transAxes
        )
        self.vmin_slider_container = inset_axes(
            parent_axes=self.misc_panel,
            width="30%",
            height="10%",
            loc="upper left",
            bbox_to_anchor=(0.06, -0.1, 1, 1),
            bbox_transform=self.misc_panel.transAxes
        )
        self.vmax_slider_container = inset_axes(
            parent_axes=self.misc_panel,
            width="30%",
            height="10%",
            loc="upper left",
            bbox_to_anchor=(0.06, -0.2, 1, 1),
            bbox_transform=self.misc_panel.transAxes
        )

    def _setup_images(self):
        """Set up images for raw and thermal views."""

        self.raw_image = self.raw_view.imshow(
            X=np.zeros((480, 640)),
            cmap="gray"
        )

        self.thermal_image = self.thermal_view.imshow(
            X=np.zeros((480, 640)),
            cmap="inferno"
        )

    def _init_display(self):
        """
        Prepare initial visuals and text fields for the display.
        """

        for panel in self.window.axes:
            if panel is not self.colorbar_container:
                panel.axis("off")

        self.raw_temp_text = self.raw_view.text(
            x=1,
            y=-0.07,
            s="",
            ha="right",
            transform=self.raw_view.transAxes
        )
        self.raw_view.set_title("Raw Image")

        self.max_temp_text = self.thermal_view.text(
            x=-0.33,
            y=1,
            s="",
            va="top",
            transform=self.thermal_view.transAxes,
            family="monospace"
        )
        self.min_temp_text = self.thermal_view.text(
            x=-0.33,
            y=0.94,
            s="",
            va="top",
            transform=self.thermal_view.transAxes,
            family="monospace"
        )
        self.avg_temp_text = self.thermal_view.text(
            x=-0.33,
            y=0.88,
            s="",
            va="top",
            transform=self.thermal_view.transAxes,
            family="monospace"
        )
        self.thermal_temp_text = self.thermal_view.text(
            x=1,
            y=-0.07,
            s="",
            ha="right",
            transform=self.thermal_view.transAxes
        )
        self.thermal_view.set_title("Ironbow")

        self.colorbar = self.window.colorbar(
            mappable=self.thermal_image,
            cax=self.colorbar_container,
            label="Temperature (°C)"
        )

        self.misc_panel.text(
            x=0.156,
            y=1,
            s="Threshold",
            va="top",
            family="monospace"
        )
        self.metadata = self.misc_panel.text(
            x=0.43,
            y=1,
            s="",
            va="top",
            family="monospace"
        )

        self.window.text(
            x=0.992,
            y=0.03,
            s="ThermImPro v1.0\nCopyright ©2025 Mykola Melnyk (aka NickMelk)",
            size=8,
            ha="right"
        )

        self.window_manager = plt.get_current_fig_manager()
        self.window_manager.set_window_title("ThermImPro")
        self.window_manager.window.showMaximized()

    def _add_widgets(self):
        """

        """

        self.raw_cursor = wdg.Cursor(
            ax=self.raw_view,
            lw=0.7,
            ls="-."
        )

        self.open_button = wdg.Button(
            ax=self.raw_sidebar,
            label="Open file",
            color="dimgray",
            hovercolor="darkgray"
        )

        self.thermal_cursor = wdg.Cursor(
            ax=self.thermal_view,
            lw=0.7,
            ls="-.",
            c="black"
        )

        self.palette_radio = wdg.RadioButtons(
            ax=self.thermal_sidebar_upper,
            labels=("Grayscale", "Ironbow", "Rainbow", "Glowbow"),
            active=1,
            activecolor="green"
        )

        self.save_button = wdg.Button(
            ax=self.thermal_sidebar_lower,
            label="Save file",
            color="dimgray",
            hovercolor="darkgray"
        )

        self.hotspot_button = wdg.Button(
            ax=self.thermal_sidebar_lower_right,
            label="H",
            color="red",
            hovercolor="lightcoral"
        )

        self.coldspot_button = wdg.Button(
            ax=self.thermal_sidebar_lower_rights,
            label="C",
            color="blue",
            hovercolor="cornflowerblue"
        )
        
        self.slider_min = wdg.Slider(
            ax=self.thermal_slider_base,
            label="Lower",
            valmin=0,
            valmax=10,
            valinit=1,
            valstep=0.1,
            initcolor="none",
            track_color="white"
        )
        self.slider_max = wdg.Slider(
            ax=self.thermal_slider_bases,
            label="Upper",
            valmin=90,
            valmax=100,
            valinit=99,
            valstep=0.1,
            initcolor="none",
            track_color="white"
        )

    def _interactive(self):
        self.window.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.open_button.on_clicked(lambda event: open_file(self))
        self.palette_radio.on_clicked(self.on_palette_change)
        self.save_button.on_clicked(self.save_file)
        self.hotspot_button.on_clicked(self.show_hotspot)
        self.coldspot_button.on_clicked(self.show_coldspot)
        self.slider_min.on_changed(self.change_clim_min)
        self.slider_max.on_changed(self.change_clim_max)

    def update_gfx(self, image: ThermalImage = None):
        """

        """

        # self.slider_min.reset()
        # self.slider_max.reset()

        if self.image.dtype == np.uint16:
            self.calibration_curve()

        metadata_info = ""

        for key in self.image.metadata:
            metadata_info += f"{key + ':':35}{self.image.metadata[key]}\n"

        if image:
            self.image = image

        if hasattr(self, "hotspot_marker"):
            self.hotspot_marker.remove()

        if hasattr(self, "coldspot_marker"):
            self.coldspot_marker.remove()

        y, x = np.unravel_index(np.argmax(self.image.tempc), self.image.tempc.shape)
        self.hotspot_marker, = self.thermal_view.plot(x, y, marker="+", markersize=12, markeredgecolor="red", markerfacecolor="white", lw=1.5)
        self.hotspot_marker.set_visible(False)

        y, x = np.unravel_index(np.argmin(self.image.tempc), self.image.tempc.shape)
        self.coldspot_marker, = self.thermal_view.plot(x, y, marker="+", markersize=12, markeredgecolor="blue", markerfacecolor="none", lw=1.5)
        self.coldspot_marker.set_visible(False)

        self.raw_image.set_data(self.image.raw)
        vmax = 255 if self.image.dtype == np.float32 else 65535
        self.raw_image.set_clim(vmin=0, vmax=vmax)

        self.thermal_image.set_data(self.image.tempc)
        self.thermal_image.set_clim(np.percentile(self.image.tempc, 1), np.percentile(self.image.tempc, 99))

        self.max_temp_text.set_text(f"Max: {np.max(self.image.tempc):.3f}°C")
        self.min_temp_text.set_text(f"Min: {np.min(self.image.tempc):.3f}°C")
        self.avg_temp_text.set_text(f"Avg: {np.mean(self.image.tempc):.3f}°C")

        for view in (self.raw_image, self.thermal_image):
            view.set_extent((-0.5, self.image.raw.shape[1] - 0.5, self.image.raw.shape[0] - 0.5, -0.5))

        self.window.canvas.draw_idle()

    def show_hotspot(self, event):
        """

        """

        self.hotspot_marker.set_visible(not self.hotspot_marker.get_visible())
        self.window.canvas.draw_idle()

    def show_coldspot(self, event):
        """

        """

        self.coldspot_marker.set_visible(not self.coldspot_marker.get_visible())
        
        self.window.canvas.draw_idle()

    def change_clim_min(self, value):
        self.thermal_image.set_clim(vmin=np.percentile(self.image.tempc, value))
        self.window.canvas.draw_idle()

    def change_clim_max(self, value):
        self.thermal_image.set_clim(vmax=np.percentile(self.image.tempc, value))
        self.window.canvas.draw_idle()

    def on_palette_change(self, label):
        """

        """
        
        self.thermal_view.set_title(label)

        colormaps = {"Grayscale": "gray", "Ironbow": "inferno", "Rainbow": "jet", "Glowbow": "hot"}

        self.thermal_image.set_cmap(colormaps.get(label, "inferno"))
        self.thermal_image.set_clim(np.percentile(self.image.tempc, 1), np.percentile(self.image.tempc, 99))

        self.window.canvas.draw_idle()

    def save_file(self, event = None):
        """

        """

        cmap_name = self.thermal_image.get_cmap().name
        cmap = plt.get_cmap(cmap_name)

        temp_norm = Normalize(vmin=np.percentile(self.active_therm_c, 1), vmax=np.percentile(self.active_therm_c, 99))
        norm_image = temp_norm(self.active_therm_c)

        rgb_image = cmap(norm_image)[..., :3]
        rgb_uint8 = (rgb_image * 255).astype(np.uint8)

        filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        mpimg.imsave(f"output/{filename}.jpg", rgb_uint8)

    def on_mouse_move(self, event):
        """

        """

        if event.inaxes is self.raw_view or event.inaxes is self.thermal_view:
            x = int(event.xdata)
            y = int(event.ydata)

            temp_c = self.image.tempc[y, x]
            temp_f = self.image.tempf[y, x]

            if event.inaxes is self.raw_view:
                self.raw_temp_text.set_text(f"Temp: {temp_c:.2f}°C, {temp_f:.2f}°F")
                self.thermal_temp_text.set_text("")

            else:
                self.thermal_temp_text.set_text(f"Temp: {temp_c:.2f}°C, {temp_f:.2f}°F")
                self.raw_temp_text.set_text("")

        else:
            self.raw_temp_text.set_text("")
            self.thermal_temp_text.set_text("")
        
        self.window.canvas.draw_idle()

    def calibration_curve(self):
        """

        """

        values = np.arange(0, 65536)
        temp_vals = self.image.raw_to_tempc(values)

        self.curve_panel.clear()
        self.curve_panel.plot(values, temp_vals, c="orange")
        self.curve_panel.set_title("Calibration Curve: Temperature vs. Digital Signal Output (Raw Pixel Value)")
        self.curve_panel.set_xlabel("Digital Signal Output (Raw Pixel Value)")
        self.curve_panel.set_ylabel("Estimated Temperature (°C)")
        self.curve_panel.grid(True)

def open_file(window: ThermalGUI | None = None) -> ThermalImage | None:
    """
    Creates and returns a `ThermalImage` object from an image selected
    in a file dialog.

    If no file is chosen, returns None. If a `window` is provided, its
    image is replaced and the view is updated.
    """

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.raw *.jpg *.jpeg *.png *.tif *.tiff")]
    )

    root.destroy()

    if not file_path:
        return None
    
    image = ThermalImage(file_path)
    
    if window and image.raw is not None:
        window.update_gfx(image)
    
    else:
        return image
