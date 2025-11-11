"""Utility functions for loading Qt Style Sheets (QSS)"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_stylesheet(filename: str) -> str:
    """
    Load a QSS stylesheet from the styles directory.
    
    Args:
        filename: Name of the QSS file (e.g., 'login.qss')
        
    Returns:
        Stylesheet content as string, or empty string if file not found
    """
    styles_dir = Path(__file__).parent.parent / "styles"
    stylesheet_path = styles_dir / filename
    
    if not stylesheet_path.exists():
        logger.warning(f"Stylesheet not found: {stylesheet_path}")
        return ""
    
    try:
        with open(stylesheet_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Loaded stylesheet: {filename}")
        return content
    except Exception as e:
        logger.error(f"Error loading stylesheet {filename}: {e}")
        return ""

