import numpy as np

def calculate_ndvi(red_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """
    Computes the Normalized Difference Vegetation Index (NDVI).
    Formula: (NIR - Red) / (NIR + Red)
    
    Args:
        red_band (np.ndarray): 2D numpy array of Red band values (Sentinel-2 Band 4)
        nir_band (np.ndarray): 2D numpy array of Near-Infrared band values (Sentinel-2 Band 8)
        
    Returns:
        np.ndarray: 2D numpy array with NDVI values in the range [-1.0, 1.0]
    """
    # Ensure float calculations
    red = red_band.astype(float)
    nir = nir_band.astype(float)
    
    denominator = nir + red
    numerator = nir - red
    
    # Handle division by zero or NaN values
    # Return 0.0 or nan where the denominator is 0
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = np.where(denominator != 0, numerator / denominator, 0.0)
        
    # Clip to valid NDVI range [-1, 1] in case of numerical noise
    ndvi = np.clip(ndvi, -1.0, 1.0)
    
    return ndvi

def calculate_deforestation_mask(ndvi_before: np.ndarray, ndvi_after: np.ndarray, threshold: float = 0.2) -> np.ndarray:
    """
    Creates a binary mask showing areas where NDVI has dropped significantly, 
    indicating forest cover loss.
    
    Args:
        ndvi_before (np.ndarray): NDVI array before the period
        ndvi_after (np.ndarray): NDVI array after the period
        threshold (float): Minimum NDVI drop to trigger alert (default 0.2)
        
    Returns:
        np.ndarray: Binary array (1 where forest loss occurred, 0 elsewhere)
    """
    # Deforestation is characterized by a significant drop in NDVI (e.g. from 0.7 to 0.3)
    ndvi_drop = ndvi_before - ndvi_after
    
    # Filter where NDVI dropped by more than the threshold and before NDVI was high (indicating it was forest)
    deforestation_mask = (ndvi_drop >= threshold) & (ndvi_before > 0.4)
    
    return deforestation_mask.astype(np.uint8)
