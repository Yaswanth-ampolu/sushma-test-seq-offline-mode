"""
Build script for creating executable from the Spring Test App.
"""
import os
import sys
import shutil
import subprocess
import argparse


def build_exe(one_file=False, console=False, clean=False):
    """Build executable using PyInstaller.
    
    Args:
        one_file: Whether to build a single executable file.
        console: Whether to show console window.
        clean: Whether to clean build files before building.
    """
    print("Building Spring Test App executable...")
    
    # Clean build files if requested
    if clean and os.path.exists("build"):
        print("Cleaning build directory...")
        shutil.rmtree("build")
    
    if clean and os.path.exists("dist"):
        print("Cleaning dist directory...")
        shutil.rmtree("dist")
    
    # Determine PyInstaller options
    options = []
    
    # Name of the application
    options.append("--name=SpringTestApp")
    
    # Icon
    icon_path = os.path.join("resources", "icon.ico")
    if os.path.exists(icon_path):
        options.append(f"--icon={icon_path}")
        print(f"Using icon: {icon_path}")
    else:
        print(f"Warning: Icon file not found at {icon_path}")
    
    # One file or directory mode
    if one_file:
        options.append("--onefile")
    else:
        options.append("--onedir")
    
    # Console or window mode
    if console:
        options.append("--console")
    else:
        options.append("--windowed")
    
    # Add all required data directories
    # Check if directories exist before adding them
    data_dirs = [
        "resources",
        "appdata",
        "ui",
        "utils",
        "models",
        "services",
        "logs"  # Add logs directory
    ]
    
    for dir_name in data_dirs:
        if os.path.exists(dir_name):
            # Use semicolon as separator on Windows
            options.append(f"--add-data={dir_name};{dir_name}")
            print(f"Adding data directory: {dir_name}")
    
    # Add other PyInstaller options as needed
    options.append("--clean")  # Clean PyInstaller cache
    options.append("--noconfirm")  # Replace output directory without confirmation
    
    # Path to main script
    main_script = "main.py"
    
    # Assemble the command
    command = ["pyinstaller"] + options + [main_script]
    
    # Run PyInstaller
    print("Running PyInstaller with options:", " ".join(options))
    try:
        subprocess.run(command, check=True)
        print("Build completed successfully!")
        
        # Create launcher batch file for one-file builds
        if one_file:
            exe_path = os.path.join("dist", "SpringTestApp.exe")
            wrapper_path = os.path.join("dist", "SpringTestApp_ClearChat.bat")
            
            with open(wrapper_path, "w") as f:
                f.write(f'@echo off\n"{os.path.abspath(exe_path)}" --clear-chat\n')
            
            print(f"Created wrapper batch file at: {wrapper_path}")
            print("Executable created at: dist/SpringTestApp.exe")
            print("You can also use the 'SpringTestApp_ClearChat.bat' to always clear chat history on startup")
        else:
            print("Executable created at: dist/SpringTestApp/SpringTestApp.exe")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Spring Test App executable")
    parser.add_argument("--onefile", action="store_true", help="Build a single executable file")
    parser.add_argument("--console", action="store_true", help="Show console window")
    parser.add_argument("--clean", action="store_true", help="Clean build files before building")
    
    args = parser.parse_args()
    
    build_exe(
        one_file=args.onefile,
        console=args.console,
        clean=args.clean
    ) 