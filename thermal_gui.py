import os
import json
import datetime
import tkinter as tk
from tkinter import filedialog

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets as wdg
import matplotlib.image as mpimg
from matplotlib.colors import Normalize
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from thermal_image import ThermalImage

class ThermalGUI:
    def __init__(self):
        plt.style.use("dark_background")

        metadata = load_metadata()

        self.image = ThermalImage(metadata)

        self.fig, ((self.ax_raw, self.ax_graph), (self.ax_thermal, self.ax_info)) = plt.subplots(2, 2, figsize = (15, 8))
        self.fig.canvas.manager.set_window_title("ThermImPro") # cool name, isn't it? :)

        self.ax_toolbar_raw = inset_axes(self.ax_raw, width = "30%", height = "20%", loc = "center left", bbox_to_anchor = (-0.355, 0, 1, 1), bbox_transform = self.ax_raw.transAxes)

        self.ax_toolbar_thermal = inset_axes(self.ax_thermal, width = "30%", height = "50%", loc = "center left", bbox_to_anchor = (-0.355, 0, 1, 1), bbox_transform = self.ax_thermal.transAxes)
        self.ax_rbtn_toolbar_th = inset_axes(self.ax_thermal, width = "30%", height = "50%", loc = "center left", bbox_to_anchor = (-0.355, 0, 1, 1), bbox_transform = self.ax_thermal.transAxes)
        self.ax_btn_toolbar_th = inset_axes(self.ax_thermal, width = "30%", height = "20%", loc = "lower left", bbox_to_anchor = (-0.355, -0.021, 1, 1), bbox_transform = self.ax_thermal.transAxes)
        self.ax_colorbar_thermal = inset_axes(self.ax_thermal, width = "5%", height = "100%", loc = "right", bbox_to_anchor = (0.1, 0, 1, 1), bbox_transform = self.ax_thermal.transAxes)

        for ax in (self.ax_raw, self.ax_thermal, self.ax_graph, self.ax_info, self.ax_toolbar_thermal, self.ax_colorbar_thermal):
            ax.axis("off")

        image_size = (metadata["Raw Thermal Image Height"], metadata["Raw Thermal Image Width"])

        self.raw_image = self.ax_raw.imshow(np.zeros(image_size), cmap = "gray")
        self.ax_raw.set_title("Raw Image")

        self.thermal_image = self.ax_thermal.imshow(np.zeros(image_size), cmap = "inferno")
        self.ax_thermal.set_title("Ironbow")

        self.calibr_curve = self.ax_graph

        self.signature = self.fig.text(0.992, 0.03, s = "ThermImPro v1.0\nCopyright ©2025 Mykola Melnyk (aka NickMelk)", fontsize = 8, horizontalalignment = "right")

        self.text_raw = self.ax_raw.text(1, -0.1, s = "", horizontalalignment = "right", verticalalignment = "bottom", transform = self.ax_raw.transAxes)

        self.max_temp_thermal = self.ax_thermal.text(-0.33, 1, s = "", horizontalalignment = "left", verticalalignment = "top", transform = self.ax_thermal.transAxes)
        self.min_temp_thermal = self.ax_thermal.text(-0.33, 0.94, s = "", horizontalalignment = "left", verticalalignment = "top", transform = self.ax_thermal.transAxes)
        self.avg_temp_thermal = self.ax_thermal.text(-0.33, 0.88, s = "", horizontalalignment = "left", verticalalignment = "top", transform = self.ax_thermal.transAxes)

        self.text_thermal = self.ax_thermal.text(1, -0.1, s = "", horizontalalignment = "right", verticalalignment = "bottom", transform = self.ax_thermal.transAxes)

        self.cursor_raw = wdg.Cursor(ax = self.ax_raw, horizOn = True, vertOn = True, linewidth = 0.7, color = "white", linestyle = "-.")

        self.open_button = wdg.Button(ax = self.ax_toolbar_raw, label = "Open file", color = "dimgray", hovercolor = "green")
        self.open_button.on_clicked(self.open_file)

        self.cursor_thermal = wdg.Cursor(ax = self.ax_thermal, horizOn = True, vertOn = True, linewidth = 0.7, color = "black", linestyle = "-.")

        self.palette_radiobtn = wdg.RadioButtons(ax = self.ax_rbtn_toolbar_th, labels = ("Grayscale", "Ironbow", "Rainbow", "Glowbow"), active = 1, activecolor = "green")
        self.palette_radiobtn.on_clicked(self.on_palette_change)

        self.save_button = wdg.Button(ax = self.ax_btn_toolbar_th, label = "Save file", color = "dimgray", hovercolor = "green")
        self.save_button.on_clicked(self.save_file)

        metadata_info = ""

        for key in metadata:
            metadata_info += f"{key + ":":35}{metadata[key]}\n"
        
        self.info = self.ax_info.text(0, -0.1, s = metadata_info, horizontalalignment = "left", verticalalignment = "bottom", family = "monospace")

        self.fig.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        self.image_loaded = False

    def open_file(self, event = None):
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(filetypes = [("Image Files", "*.raw *.jpg *.jpeg *.png *.tif *.tiff")])

        root.destroy()

        if not file_path:
            if not self.image_loaded:
                plt.close()

            return

        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == ".raw":
            try:
                gray_16_image, therm_image_c, therm_image_f = self.image.load_raw_file(file_path)

            except Exception:
                if not self.image_loaded:
                    plt.close()

                tk.messagebox.showerror(title = "Load Error", message = "Failed to load image.")

                return
            
            if gray_16_image.dtype == np.float32:
                self.image_loaded = True

                self.active_gray_16 = gray_16_image
                self.active_therm_c = therm_image_c
                self.active_therm_f = therm_image_f
            
            else:
                if not self.image_loaded:
                    plt.close()

                tk.messagebox.showerror(title = "Invalid Image Format", message = "The selected image is not in float32 format.")

                return

        else:
            try:
                gray_16_image, therm_image_c, therm_image_f = self.image.load_16_bit_file(file_path)

            except Exception:
                if not self.image_loaded:
                    plt.close()

                tk.messagebox.showerror(title = "Load Error", message = "Failed to load image.")

                return

            if gray_16_image.dtype == np.uint16:
                self.image_loaded = True

                self.active_gray_16 = gray_16_image
                self.active_therm_c = therm_image_c
                self.active_therm_f = therm_image_f

            else:
                if not self.image_loaded:
                    plt.close()

                tk.messagebox.showerror(title = "Invalid Image Format", message = "The selected image is not in uint16 format.")

                return

        self.raw_image.set_data(gray_16_image)
        colors_max = {np.uint8: 255, np.uint16: 65535}
        self.raw_image.set_clim(0, colors_max.get(gray_16_image.dtype.type, np.max(gray_16_image)))

        # Applying colorful palette to the 16-bit image
        self.thermal_image.set_data(therm_image_c)
        self.thermal_image.set_clim(np.percentile(therm_image_c, 1), np.percentile(therm_image_c, 99))

        if file_ext != ".raw":
            self.draw_calibration_curve()

        self.palette_radiobtn.ax.set_facecolor("dimgray")

        self.max_temp_thermal.set_text(f"Max: {np.max(therm_image_c):.3f}°C")
        self.min_temp_thermal.set_text(f"Min:  {np.min(therm_image_c):.3f}°C")
        self.avg_temp_thermal.set_text(f"Avg:  {np.mean(therm_image_c):.3f}°C")

        try:
            if hasattr(self, "colorbar_thermal") and self.colorbar_thermal:
                self.thermal_image.set_clim(np.percentile(self.active_therm_c, 1), np.percentile(self.active_therm_c, 99))

                self.colorbar_thermal.update_normal(self.thermal_image)

            else:
                self.ax_colorbar_thermal.clear()
                self.colorbar_thermal = self.fig.colorbar(self.thermal_image, cax = self.ax_colorbar_thermal)
                self.colorbar_thermal.set_label("Temperature (°C)")

        except Exception:
            pass

        self.fig.canvas.draw_idle()

    # Changing thermal image pallette
    def on_palette_change(self, label):
        self.ax_thermal.set_title(label)

        colormaps = {"Grayscale": "gray", "Ironbow": "inferno", "Rainbow": "jet", "Glowbow": "hot"}

        self.thermal_image.set_cmap(colormaps.get(label, "inferno"))
        self.thermal_image.set_clim(np.percentile(self.active_therm_c, 1), np.percentile(self.active_therm_c, 99))

        try:
            self.colorbar_thermal.update_normal(self.thermal_image)

        except Exception:
            pass

        self.fig.canvas.draw_idle()

    def save_file(self, event = None):
        cmap_name = self.thermal_image.get_cmap().name
        cmap = plt.get_cmap(cmap_name)

        temp_norm = Normalize(vmin = np.percentile(self.active_therm_c, 1), vmax = np.percentile(self.active_therm_c, 99))
        norm_image = temp_norm(self.active_therm_c)

        rgb_image = cmap(norm_image)[..., :3]
        rgb_uint8 = (rgb_image * 255).astype(np.uint8)

        filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        mpimg.imsave(f"output/{filename}.jpg", rgb_uint8)

    def on_mouse_move(self, event):
        if not self.image_loaded:
            return

        if event.inaxes is self.ax_raw or event.inaxes is self.ax_thermal:
            x = int(event.xdata)
            y = int(event.ydata)

            temp_c = self.active_therm_c[y, x]
            temp_f = self.active_therm_f[y, x]

            if event.inaxes is self.ax_raw:
                self.text_raw.set_text(f"{temp_c:.2f}°C, {temp_f:.2f}°F")
                self.text_thermal.set_text("")

            else:
                self.text_thermal.set_text(f"{temp_c:.2f}°C, {temp_f:.2f}°F")
                self.text_raw.set_text("")

        else:
            self.text_raw.set_text("")
            self.text_thermal.set_text("")
        
        self.fig.canvas.draw_idle()

    def draw_calibration_curve(self):
        pixel_vals = np.arange(0, 65536, dtype = np.float32)

        self.calibr_curve.clear()
        self.calibr_curve.plot(pixel_vals, self.image.raw_to_temperature(pixel_vals), color = "orange")
        self.calibr_curve.set_title("Calibration Curve: Temperature vs. Digital Signal Output (Raw Pixel Value)")
        self.calibr_curve.set_xlabel("Digital Signal Output (Raw Pixel Value)")
        self.calibr_curve.set_ylabel("Estimated Temperature (°C)")
        self.calibr_curve.grid(True)

    def show(self):
        plt.show()

def load_metadata() -> dict:
    """
    Loads metadata from a JSON file.

    Returns:
        dict: Metadata parameters stored in the dictionary.
    """

    with open("metadata.json") as file:
        metadata = json.loads(file.read())

    return metadata
