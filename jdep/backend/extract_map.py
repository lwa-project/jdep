import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from scipy import ndimage
from typing import Dict, Any, Optional

def extract_data(image_path: str='zarka-2018a-fig-1a.png',
                 colorbar_path: str='zarka-2018a-fig-1a-legend-cropped.png',
                 max_probability: float=65.3, tag: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract probability data from the image using the colorbar's vertical gradient.
    """
    
    # Load the image and colorbar
    img = Image.open(image_path)
    img_array = np.array(img)
    
    cb = Image.open(colorbar_path)
    cb_array = np.array(cb)
    
    # Convert to float
    plot_area = img_array.astype(np.float32)
    
    # Get the colorbar's central column as reference
    colorbar_center = cb_array[:, cb_array.shape[1]//2]
    
    # Probability values range from max_probability% at the top to 0% at the bottom
    probability_values = np.linspace(max_probability, 0, len(colorbar_center))
    
    # Create the probability map
    height, width = plot_area.shape[:2]
    probability_map = np.zeros((height, width))
    
    # Handle white text/boundaries
    luminance = plot_area.mean(axis=2) / 255 * 100
    white_mask = (luminance > 90)
    
    # Grow (dilate) the white mask by one pixel in all directions
    white_mask = ndimage.binary_dilation(white_mask, structure=np.ones((3,3)))
    
    print("Mapping colors to probabilities...")
    for i in range(height):
        for j in range(width):
            if white_mask[i, j]:
                probability_map[i, j] = np.nan  # Will be interpolated
                continue
                
            # Get the pixel color from the smoothed image
            pixel_color = plot_area[i, j]
            
            # Find the closest matching color in the colorbar
            # Use squared distance without square root for efficiency
            color_distances = np.sum((colorbar_center - pixel_color)**2, axis=1)
            closest_idx = np.argmin(color_distances)
            
            # Assign the corresponding probability
            probability_map[i, j] = probability_values[closest_idx]
            
    # Interpolate all NaN values using an iterative approach
    # This fills in white regions and hot pixels with smooth transitions
    nan_mask = np.isnan(probability_map)
    
    # Use a larger window for better interpolation
    window_size = 1
    max_iterations = 20
    iteration = 0
    
    while np.any(nan_mask) and iteration < max_iterations:
        iteration += 1
        print(f"Interpolation iteration {iteration}, {np.sum(nan_mask)} NaN values remaining")
        
        # Only update the remaining NaN values
        new_map = probability_map*1.0
        for i, j in zip(*np.where(nan_mask)):
            neighbors = []
            
            # Use a window around the current pixel
            for ni in range(max(0, i-window_size), min(height, i+window_size+1)):
                for nj in range(max(0, j-window_size), min(width, j+window_size+1)):
                    if not np.isnan(probability_map[ni, nj]):
                        # Weight by distance (closer pixels have more influence)
                        dist = np.sqrt((ni-i)**2 + (nj-j)**2)
                        weight = -dist**2 / (2 * 1.0**2) + 1e-8
                        neighbors.append((probability_map[ni, nj], weight))
            
            if len(neighbors) > (2*window_size+1)*(2*window_size+1)*0.3:
                # Weighted average
                values, weights = zip(*neighbors)
                new_map[i, j] = np.average(values, weights=weights)
                nan_mask[i, j] = False
                
        probability_map = new_map
        
    # Create coordinates for CML and Satellite Phase
    cml = np.linspace(0, 360, width)
    phase = np.linspace(360, 0, height)  # Reversed
    
    # Save the results
    file_tag = f"_{tag}" if tag else ''
    np.save(f"probability_map{file_tag}.npy", probability_map)
    np.save(f"cml_coordinates{file_tag}.npy", cml)
    np.save(f"phase_coordinates{file_tag}.npy", phase)
    
    # Create a visualization
    plt.figure(figsize=(12, 10))
    plt.imshow(probability_map, origin='upper', extent=[0, 360, 0, 360], cmap='jet')
    plt.colorbar(label='Probability (%)')
    
    plt.title('Jupiter-Satellite Interaction Probability Map')
    plt.xlabel('CML (°)')
    plt.ylabel('Satellite Phase (°)')
    plt.grid(True, alpha=0.3)
    plt.savefig(f"probability_map{file_tag}.png")
    
    print("Data extraction complete. Files saved.")
    
    return {
        'probability_map': probability_map,
        'cml': cml,
        'phase': phase
    }


if __name__ == "__main__":
    # Figure 1(a) - all emission
    extract_data(image_path='zarka-2018a-fig-1a.png',
                 colorbar_path='zarka-2018a-fig-1a-legend-cropped.png',
                 max_probability=63.5, tag='all')
    
    # Figure 1(b) - non-Io emission
    extract_data(image_path='zarka-2018a-fig-1b.png',
                 colorbar_path='zarka-2018a-fig-1a-legend-cropped.png',
                 max_probability=17.0, tag='nonio')
