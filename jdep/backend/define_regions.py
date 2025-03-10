import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.widgets import Button, RadioButtons
from matplotlib.backend_bases import Event as MPLEvent
import matplotlib.colors as mcolors
from PIL import Image
import matplotlib.path as mpath
from typing import Optional

class RegionLabeler:
    """
    Class to help with defining regions on a plot by clicking on boundaries.
    """
    
    def __init__(self, image_path: str, tag: Optional[str]=None):
        # Load the image
        self.image = plt.imread(image_path)
        self.height, self.width = self.image.shape[:2]
        self.tag = tag
        
        # Create a blank mask with the same dimensions as the image
        self.mask = np.zeros((self.height, self.width), dtype=np.uint8)
        
        # Dictionary to store region definitions and bit values
        self.regions = {
            'A':  {'bit':  1, 'color': 'red', 'points': []},
            "A'": {'bit':  2, 'color': 'blue', 'points': []},
            'A"': {'bit':  4, 'color': 'green', 'points': []},
            'B':  {'bit':  8, 'color': 'yellow', 'points': []},
            "B'": {'bit': 16, 'color': 'cyan', 'points': []},
            'C':  {'bit': 32, 'color': 'magenta', 'points': []},
            'D':  {'bit': 64, 'color': 'orange', 'points': []},
        }
        
        # Current active region
        self.active_region = None
        self.current_points = []
        self.current_polygon = None
        
        # Create a figure with a fixed size
        self.fig = plt.figure(figsize=(16, 8))
        self.setup_layout()
        self.setup_displays()
        self.setup_controls()
        
        # Connect the mouse click event
        self.click_cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Set status text
        self.status_text = self.fig.text(0.3, 0.02, 'Ready: Select a region to start', 
                                         ha='center', fontsize=12)

    def setup_layout(self):
        # Create a layout with dedicated areas
        self.gs_main = self.fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=0.1)
        
        # Create subgridspecs for the left and right sides
        self.gs_left = self.gs_main[0].subgridspec(1, 2, width_ratios=[0.25, 0.75], wspace=0.05)
        self.gs_right = self.gs_main[1]

    def setup_displays(self):
        # Set up the image display
        self.ax_image = self.fig.add_subplot(self.gs_left[1])
        self.ax_image.imshow(self.image, origin='upper')
        self.ax_image.set_title('Original Image - Click to define regions')
        self.ax_image.set_xlim(0, self.width)
        self.ax_image.set_ylim(self.height, 0)
        
        # Set up the mask display
        self.ax_mask = self.fig.add_subplot(self.gs_right)
        self.mask_display = self.ax_mask.imshow(
            np.zeros((self.height, self.width, 4)), 
            origin='upper'
        )
        self.ax_mask.set_title('Generated Bitmask')
        self.ax_mask.set_xlim(0, self.width)
        self.ax_mask.set_ylim(self.height, 0)
        
        # Set axes to show the full 0-360 range on both sides
        for ax in [self.ax_image, self.ax_mask]:
            ax.set_xticks(np.linspace(0, self.width, 5))
            ax.set_xticklabels([f"{int(x)}" for x in np.linspace(0, 360, 5)])
            ax.set_yticks(np.linspace(0, self.height, 5))
            ax.set_yticklabels([f"{int(y)}" for y in np.linspace(0, 360, 5)])

    def setup_controls(self):
        # Create a control panel on the left
        self.ax_controls = self.fig.add_subplot(self.gs_left[0])
        self.ax_controls.set_title('Controls')
        self.ax_controls.axis('off')
        
        # Create custom radio buttons using regular buttons instead
        region_names = list(self.regions.keys())
        self.region_buttons = []
        
        # Add title for region selection
        self.ax_controls.text(0.5, 0.99, "Select Region:", ha='center',
                              fontsize=12, fontweight='bold',
                              transform=self.ax_controls.transAxes)
        
        # Create a button for each region
        for i, region_name in enumerate(region_names):
            # Calculate y position for button
            y_pos = 0.85 - (i * 0.07)
            ax = self.fig.add_axes([0.05, y_pos, 0.15, 0.05])
            
            # Create button with region color
            button = Button(ax, region_name, color=self.regions[region_name]['color'])
            button.on_clicked(lambda event, r=region_name: self.start_region(r))
            self.region_buttons.append(button)
        
        # Create action buttons
        finish_ax = self.fig.add_axes([0.05, 0.36, 0.15, 0.05])
        self.finish_button = Button(finish_ax, 'Finish Region', color='lightblue')
        self.finish_button.on_clicked(self.finish_region)
        
        clear_ax = self.fig.add_axes([0.05, 0.29, 0.15, 0.05])
        self.clear_button = Button(clear_ax, 'Clear Current', color='lightcoral')
        self.clear_button.on_clicked(self.clear_current)
        
        save_ax = self.fig.add_axes([0.05, 0.22, 0.15, 0.05])
        self.save_button = Button(save_ax, 'Save Mask', color='lightgreen')
        self.save_button.on_clicked(self.save_mask)
        
        # Add a legend for bit values
        legend_ax = self.fig.add_axes([0.05, 0.08, 0.15, 0.08])
        legend_ax.axis('off')
        legend_ax.set_title('Region Bit Values')
        
        y_pos = 0.9
        for i, (region_name, region_data) in enumerate(self.regions.items()):
            if i == 4:
                y_pos = 0.9
            legend_ax.text(0.1+0.5*(i//4), y_pos, f"{region_name}: {region_data['bit']}", 
                           color=region_data['color'], fontweight='bold',
                           transform=legend_ax.transAxes)
            y_pos -= 0.25

    def start_region(self, region_name: str):
        self.active_region = region_name
        self.current_points = []
        
        if self.current_polygon:
            self.current_polygon.remove()
            self.current_polygon = None
            
        self.update_status(f"Drawing region {region_name}")

    def on_click(self, event: MPLEvent):
        if event.inaxes != self.ax_image or self.active_region is None:
            return
            
        # Add the clicked point to the current region
        self.current_points.append((event.xdata, event.ydata))
        
        # Update the displayed polygon
        if len(self.current_points) > 2:
            if self.current_polygon:
                self.current_polygon.remove()
                
            poly = np.array(self.current_points)
            self.current_polygon = Polygon(poly, fill=True, alpha=0.3, 
                                           color=self.regions[self.active_region]['color'],
                                           hatch='///')
            self.ax_image.add_patch(self.current_polygon)
        
        # Also plot the points
        self.ax_image.plot(event.xdata, event.ydata, 'o', 
                          color=self.regions[self.active_region]['color'],
                          markersize=5)
        
        self.fig.canvas.draw_idle()

    def finish_region(self, event: MPLEvent):
        if self.active_region is None or len(self.current_points) < 3:
            self.update_status("Need at least 3 points to define a region")
            return
            
        # Store the points for this region
        self.regions[self.active_region]['points'] = self.current_points.copy()
        
        # Update the mask
        self.update_mask()
        
        # Reset the current region
        self.clear_current(None)
        self.update_status(f"Region {self.active_region} added to mask. Select another region.")

    def clear_current(self, event: MPLEvent):
        if self.current_polygon:
            self.current_polygon.remove()
            self.current_polygon = None
            
        self.current_points = []
        
        # Remove point markers
        for line in self.ax_image.lines[:]:
            if line.get_markersize() == 5:  # Our point markers
                line.remove()
        
        self.fig.canvas.draw_idle()
        
    def update_mask(self):
        # Convert the polygon to a mask
        if not self.current_points:
            return
            
        # Create a polygon for the current region
        poly = np.array(self.current_points)
        
        # Create a mask for the region using Path.contains_points
        y, x = np.mgrid[:self.height, :self.width]
        points = np.vstack((x.flatten(), y.flatten())).T
        
        path = mpath.Path(poly)
        mask = path.contains_points(points)
        mask = mask.reshape(self.height, self.width)
        
        # Update the region mask with the bit value
        bit_value = self.regions[self.active_region]['bit']
        self.mask[mask] |= bit_value  # Use bitwise OR to set this bit
        
        # Update the mask display
        self.update_mask_display()

    def update_mask_display(self):
        # Create a visualization of the bitmask
        colored_mask = np.zeros((self.height, self.width, 4))  # RGBA
        
        # For each region, add its color to the visualization where the bit is set
        for region_name, region_data in self.regions.items():
            bit = region_data['bit']
            color = mcolors.to_rgba(region_data['color'])
            
            # Find pixels where this bit is set
            bit_set = (self.mask & bit) > 0
            
            if np.any(bit_set):
                # Add this color with transparency to those pixels
                for i in range(3):  # RGB channels
                    colored_mask[bit_set, i] += color[i] * 0.7
                colored_mask[bit_set, 3] = 0.7  # Alpha channel
        
        # Normalize RGB channels if needed
        rgb_max = colored_mask[:,:,:3].max()
        if rgb_max > 1.0:
            colored_mask[:,:,:3] /= rgb_max
        
        # Update the display
        self.mask_display.set_data(colored_mask)
        self.fig.canvas.draw_idle()

    def update_status(self, message):
        self.status_text.set_text(message)
        self.fig.canvas.draw_idle()

    def save_mask(self, event):
        # Save the mask as a numpy array
        file_tag = f"_{self.tag}" if self.tag else ''
        np.save(f"region_bitmask{file_tag}.npy", self.mask)
        
        # Also save as a colored image for visualization
        colored_img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for region_name, region_data in self.regions.items():
            bit = region_data['bit']
            color_rgb = np.array(mcolors.to_rgb(region_data['color'])) * 255
            
            # Find pixels where this bit is set
            bit_set = (self.mask & bit) > 0
            
            # Set those pixels to this color
            if np.any(bit_set):
                for i in range(3):
                    colored_img[bit_set, i] = color_rgb[i]
                
        # Save the colored visualization
        Image.fromarray(colored_img).save(f"region_visualization{file_tag}.png")
        
        self.update_status(f"Mask saved to region_bitmask{file_tag}.npy and region_visualization{file_tag}.png")


def run_labeler(image_path: str, tag: Optional[str]=None):
    labeler = RegionLabeler(image_path, tag=tag)
    plt.tight_layout()
    plt.show()
    return labeler  # Return the labeler object so it doesn't get garbage collected


if __name__ == "__main__":
    try:
        import sys
        if len(sys.argv) > 1:
            image_path = sys.argv[1]
        app = run_labeler('zarka-2018a-fig-1a.png', tag='io')
        # app = run_labeler('zarka-2018a-fig-1b.png', tag='nonio')
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
