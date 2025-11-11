#!/usr/bin/env python3
"""
Create a macOS .app bundle for proper dock icon display.
This script creates a proper .app bundle structure with Info.plist
that references the .icns icon file.
"""
import subprocess
import sys
import shutil
from pathlib import Path

def create_app_bundle():
    """Create a macOS .app bundle"""
    script_dir = Path(__file__).parent
    app_name = "jungholm-instruments-gateway"
    app_bundle = script_dir / f"{app_name}.app"
    contents_dir = app_bundle / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    # Remove existing bundle if it exists
    if app_bundle.exists():
        print(f"Removing existing {app_bundle.name}...")
        shutil.rmtree(app_bundle)
    
    # Create bundle structure
    print(f"Creating {app_bundle.name} bundle...")
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy icon to Resources
    icon_source = script_dir / "assets" / "jungholm-logo.icns"
    if icon_source.exists():
        icon_dest = resources_dir / "jungholm-logo.icns"
        shutil.copy2(icon_source, icon_dest)
        print(f"  Copied icon to Resources")
    else:
        print(f"  Warning: Icon file not found at {icon_source}")
    
    # Create Info.plist
    info_plist = contents_dir / "Info.plist"
    bundle_id = "com.jungholminstruments.gateway"
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>{app_name}</string>
    <key>CFBundleIconFile</key>
    <string>jungholm-logo</string>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>jungholm instruments Gateway</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>"""
    
    info_plist.write_text(plist_content)
    print(f"  Created Info.plist")
    
    # Create launcher script
    launcher_script = macos_dir / app_name
    python_path = sys.executable
    main_script = script_dir / "main.py"
    
    # Find Qt plugins directory
    import os
    import PySide6
    pyside6_dir = os.path.dirname(PySide6.__file__)
    qt_plugins_dir = os.path.join(pyside6_dir, 'Qt', 'plugins')
    
    launcher_content = f"""#!/bin/bash
# Change to script directory
cd "{script_dir}"

# Set PYTHONPATH to include the script directory
export PYTHONPATH="{script_dir}:$PYTHONPATH"

# Set Qt plugin path so Qt can find the cocoa platform plugin
export QT_PLUGIN_PATH="{qt_plugins_dir}"

# Load environment variables from .env file if it exists
if [ -f "{script_dir}/.env" ]; then
    set -a
    source "{script_dir}/.env"
    set +a
fi

# Create log file for errors
LOG_FILE="{script_dir}/app_error.log"
echo "$(date): Starting application" >> "$LOG_FILE"

# Run the Python application
# Capture both stdout and stderr for debugging
"{python_path}" "{main_script}" "$@" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

# If app exited with an error, show it
if [ $EXIT_CODE -ne 0 ]; then
    echo "$(date): Application exited with code $EXIT_CODE" >> "$LOG_FILE"
    # Show error dialog on macOS
    osascript -e 'display dialog "Application error. Check app_error.log for details." buttons {{"OK"}} default button "OK" with title "jungholm instruments Gateway"'
fi

exit $EXIT_CODE
"""
    
    launcher_script.write_text(launcher_content)
    launcher_script.chmod(0o755)
    print(f"  Created launcher script")
    
    print(f"\n✓ Successfully created {app_bundle.name}")
    print(f"\nTo run the app:")
    print(f"  open {app_bundle.name}")
    print(f"\nOr double-click {app_bundle.name} in Finder")
    
    return True

if __name__ == "__main__":
    if sys.platform != "darwin":
        print("Error: This script is designed for macOS only.")
        sys.exit(1)
    
    success = create_app_bundle()
    sys.exit(0 if success else 1)

