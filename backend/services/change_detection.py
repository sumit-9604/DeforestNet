import numpy as np
from pathlib import Path
from backend.utils.ndvi import calculate_ndvi, calculate_deforestation_mask
from backend.utils.logger import setup_logger

logger = setup_logger("change_detection")

class ChangeDetectionService:
    def __init__(self, threshold: float = 0.25):
        """
        Args:
            threshold (float): Minimum NDVI drop to classify as deforestation.
        """
        self.threshold = threshold

    def detect_changes(self, imagery_paths: dict, raw_alert_area: float) -> dict:
        """
        Loads satellite bands, computes NDVI, generates deforestation mask,
        and returns metrics about the verified forest loss.
        """
        try:
            before_paths = imagery_paths["before"]
            after_paths = imagery_paths["after"]
            
            # Load numpy arrays
            b_red = np.load(before_paths["red"])
            b_nir = np.load(before_paths["nir"])
            
            a_red = np.load(after_paths["red"])
            a_nir = np.load(after_paths["nir"])
            
            # 1. Compute NDVI arrays
            ndvi_before = calculate_ndvi(b_red, b_nir)
            ndvi_after = calculate_ndvi(a_red, a_nir)
            
            # 2. Compute means
            mean_ndvi_before = float(np.mean(ndvi_before))
            mean_ndvi_after = float(np.mean(ndvi_after))
            mean_ndvi_diff = mean_ndvi_before - mean_ndvi_after
            
            # 3. Create deforestation mask
            mask = calculate_deforestation_mask(ndvi_before, ndvi_after, self.threshold)
            
            # Calculate what percentage of the image has deforested pixels
            total_pixels = mask.size
            deforested_pixels = int(np.sum(mask))
            deforested_ratio = deforested_pixels / total_pixels
            
            # Calculate verified area in hectares
            # In a real system, we reproject the mask polygon and calculate UTM area.
            # In our hybrid/simulation mode, we estimate the verified area by multiplying
            # the raw GFW alert area by the deforested ratio (calibrated to represent the verified portion).
            # If deforested ratio is high, we verify the full alert area.
            verified_area_ha = round(raw_alert_area * (deforested_ratio / 0.15), 2)
            # Cap verified area at a reasonable multiple/fraction
            verified_area_ha = max(0.1, min(verified_area_ha, raw_alert_area * 1.5))
            
            # Check if alert is verified (if any pixel block was deforested, e.g. ratio > 0.005)
            is_verified = deforested_ratio > 0.005
            
            # Save the mask array to the alert's directory
            alert_dir = Path(before_paths["red"]).parent.parent
            mask_path = alert_dir / "deforestation_mask.npy"
            np.save(mask_path, mask)
            
            logger.info(
                f"Change detection completed. Before NDVI: {mean_ndvi_before:.3f}, "
                f"After NDVI: {mean_ndvi_after:.3f}, Drop: {mean_ndvi_diff:.3f}. "
                f"Verified area: {verified_area_ha} ha. Verified: {is_verified}"
            )
            
            return {
                "is_verified": is_verified,
                "ndvi_before_mean": mean_ndvi_before,
                "ndvi_after_mean": mean_ndvi_after,
                "ndvi_diff_mean": mean_ndvi_diff,
                "verified_area_ha": verified_area_ha,
                "deforestation_mask_path": str(mask_path),
                "deforested_pixel_ratio": deforested_ratio,
                "before_ndvi_array": ndvi_before,  # returned for helper functions
                "after_ndvi_array": ndvi_after,
                "deforestation_mask": mask
            }
            
        except Exception as e:
            logger.error(f"Error in change detection: {e}")
            return {
                "is_verified": False,
                "ndvi_before_mean": 0.0,
                "ndvi_after_mean": 0.0,
                "ndvi_diff_mean": 0.0,
                "verified_area_ha": 0.0,
                "deforestation_mask_path": None,
                "deforested_pixel_ratio": 0.0,
                "error": str(e)
            }
