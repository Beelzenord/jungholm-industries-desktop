#!/usr/bin/env python3
"""
Script to create macOS .icns icon file from source image.
macOS app icons should be 1024x1024 PNG format, then converted to .icns
"""
import subprocess
import sys
from pathlib import Path

def create_macos_icon():
    """Create macOS .icns icon from source image"""
    assets_dir = Path(__file__).parent / "assets"
    source_image = assets_dir / "jungholm-logo.jpeg"
    icon_dir = assets_dir / "jungholm-logo.iconset"
    icns_file = assets_dir / "jungholm-logo.icns"
    
    if not source_image.exists():
        print(f"Error: Source image not found: {source_image}")
        return False
    
    # Create iconset directory
    icon_dir.mkdir(exist_ok=True)
    
    # Required icon sizes for macOS (in points, @1x and @2x)
    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]
    
    print("Creating icon sizes...")
    for size, filename in sizes:
        output_path = icon_dir / filename
        try:
            # Use sips (macOS built-in) to resize and convert to PNG
            # sips automatically converts to PNG when output has .png extension
            result = subprocess.run([
                "sips", "-s", "format", "png",
                "-z", str(size), str(size),
                str(source_image), "--out", str(output_path)
            ], check=True, capture_output=True, text=True)
            print(f"  Created {filename} ({size}x{size})")
        except subprocess.CalledProcessError as e:
            print(f"  Error creating {filename}: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            return False
    
    # Convert iconset to .icns using iconutil
    print(f"\nConverting to .icns format...")
    try:
        subprocess.run([
            "iconutil", "-c", "icns",
            str(icon_dir), "-o", str(icns_file)
        ], check=True, capture_output=True)
        print(f"✓ Successfully created: {icns_file}")
        
        # Clean up iconset directory
        import shutil
        shutil.rmtree(icon_dir)
        print("✓ Cleaned up temporary iconset directory")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting to .icns: {e}")
        return False
    except FileNotFoundError:
        print("Error: iconutil not found. This script requires macOS.")
        return False

if __name__ == "__main__":
    if sys.platform != "darwin":
        print("Warning: This script is designed for macOS.")
        print("On macOS, run this script to generate the .icns file.")
        sys.exit(1)
    
    success = create_macos_icon()
    sys.exit(0 if success else 1)

