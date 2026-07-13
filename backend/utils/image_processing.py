import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from backend.utils.logger import setup_logger

logger = setup_logger("image_processing")

def contrast_stretch(img: np.ndarray) -> np.ndarray:
    """
    Applies simple 2-98% cumulative contrast stretching to enhance satellite bands
    and return a standard 0-255 uint8 image.
    """
    # Handle single bands or multiple bands
    if len(img.shape) == 3:
        stretched = np.zeros_like(img, dtype=np.uint8)
        for i in range(img.shape[2]):
            stretched[:, :, i] = contrast_stretch_band(img[:, :, i])
        return stretched
    else:
        return contrast_stretch_band(img)

def contrast_stretch_band(band: np.ndarray) -> np.ndarray:
    """Stretches a single band to uint8 [0, 255] using percentiles"""
    # Filter nan/inf
    band = np.nan_to_num(band, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Get percentiles
    p2, p98 = np.percentile(band, (2, 98))
    
    if p98 == p2:
        # Uniform image
        return np.zeros_like(band, dtype=np.uint8)
        
    # Stretch
    stretched = (band - p2) / (p98 - p2) * 255.0
    stretched = np.clip(stretched, 0, 255).astype(np.uint8)
    return stretched

def apply_ndvi_colormap(ndvi: np.ndarray) -> np.ndarray:
    """
    Applies a custom pseudo-color colormap to an NDVI array:
    - Values < 0: Water/Clouds/Bare rock -> Blue/Grey
    - Values 0 to 0.2: Bare soil/Sand -> Brownish/Yellowish
    - Values 0.2 to 0.5: Sparse vegetation -> Light Green
    - Values > 0.5: Dense forest -> Dark Green
    """
    h, w = ndvi.shape
    colored = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Normalized NDVI is between -1 and 1
    # Let's map it to color thresholds
    
    # Water/Non-vegetated (NDVI < 0) -> Blueish-grey
    mask_water = ndvi < 0
    colored[mask_water] = [180, 100, 50]  # BGR format for OpenCV (blueish-grey)
    
    # Bare soil (0 <= NDVI < 0.2) -> Brown/Yellow
    mask_soil = (ndvi >= 0) & (ndvi < 0.2)
    # Interpolate from brown [19, 69, 139] to light yellow [130, 220, 240]
    for y in range(h):
        # Optimized mapping
        soil_indices = np.where(mask_soil[y])[0]
        for x in soil_indices:
            val = ndvi[y, x] / 0.2
            b = int(19 + val * (130 - 19))
            g = int(69 + val * (220 - 69))
            r = int(139 + val * (240 - 139))
            colored[y, x] = [b, g, r]
            
    # Sparse vegetation (0.2 <= NDVI < 0.5) -> Light Green
    mask_sparse = (ndvi >= 0.2) & (ndvi < 0.5)
    for y in range(h):
        indices = np.where(mask_sparse[y])[0]
        for x in indices:
            val = (ndvi[y, x] - 0.2) / 0.3
            b = int(30 + val * (50 - 30))
            g = int(180 + val * (230 - 180))
            r = int(30 + val * (100 - 30))
            colored[y, x] = [b, g, r]
            
    # Dense forest (NDVI >= 0.5) -> Dark Green
    mask_dense = ndvi >= 0.5
    for y in range(h):
        indices = np.where(mask_dense[y])[0]
        for x in indices:
            val = min((ndvi[y, x] - 0.5) / 0.5, 1.0)
            b = int(10 + val * (20 - 10))
            g = int(100 + val * (140 - 100))
            r = int(10 + val * (20 - 10))
            colored[y, x] = [b, g, r]
            
    return colored

def generate_comparison_image(
    before_rgb: np.ndarray,
    after_rgb: np.ndarray,
    before_ndvi: np.ndarray,
    after_ndvi: np.ndarray,
    deforestation_mask: np.ndarray,
    save_path: str
) -> bool:
    """
    Creates a 2x2 panel comparison image:
    Panel (1,1): Before RGB (Enhanced)
    Panel (1,2): After RGB (Enhanced)
    Panel (2,1): Before NDVI (Colormapped)
    Panel (2,2): After NDVI (Colormapped) + Deforestation Mask Overlayed (in red)
    
    Saves the output image to `save_path`.
    """
    try:
        # 1. Enhance and resize RGB images to standard size, e.g. 400x400
        size = (400, 400)
        
        b_rgb = cv2.resize(contrast_stretch(before_rgb), size)
        a_rgb = cv2.resize(contrast_stretch(after_rgb), size)
        
        # 2. Get colormapped NDVI
        b_ndvi_col = cv2.resize(apply_ndvi_colormap(before_ndvi), size)
        a_ndvi_col = cv2.resize(apply_ndvi_colormap(after_ndvi), size)
        
        # 3. Create deforestation mask overlay on the after NDVI
        mask_resized = cv2.resize(deforestation_mask, size, interpolation=cv2.INTER_NEAREST)
        overlay = a_ndvi_col.copy()
        # Overlay red color [0, 0, 255] where mask is 1
        overlay[mask_resized > 0] = [0, 0, 255]
        
        # Blend the overlay with the NDVI image for a semi-transparent red alert look
        a_ndvi_alert = cv2.addWeighted(a_ndvi_col, 0.4, overlay, 0.6, 0)
        
        # 4. Assemble the grid
        top_row = np.hstack((b_rgb, a_rgb))
        bottom_row = np.hstack((b_ndvi_col, a_ndvi_alert))
        grid = np.vstack((top_row, bottom_row))
        
        # Convert BGR (OpenCV) to RGB (Pillow) for text rendering and saving
        grid_rgb = cv2.cvtColor(grid, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(grid_rgb)
        
        # Draw labels
        draw = ImageDraw.Draw(pil_img)
        
        # Draw panels bounding boxes and text
        # Simple rectangles for label backgrounds
        draw.rectangle([(10, 10), (160, 35)], fill=(0, 0, 0, 180))
        draw.text((15, 13), "Before (True Color)", fill=(255, 255, 255))
        
        draw.rectangle([(410, 10), (550, 35)], fill=(0, 0, 0, 180))
        draw.text((415, 13), "After (True Color)", fill=(255, 255, 255))
        
        draw.rectangle([(10, 410), (140, 435)], fill=(0, 0, 0, 180))
        draw.text((15, 413), "Before NDVI", fill=(255, 255, 255))
        
        draw.rectangle([(410, 410), (630, 435)], fill=(0, 0, 0, 180))
        draw.text((415, 413), "After NDVI + Deforestation (Red)", fill=(255, 255, 255))
        
        # Save image
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        pil_img.save(save_path)
        logger.info(f"Comparison image successfully generated at: {save_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate comparison image: {e}")
        return False
