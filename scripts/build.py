import PyInstaller.__main__
import os
import shutil
import sys

# Determine the project root directory (one level up from the scripts directory)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Name of your main script (entry point)
main_script = os.path.join(project_root, 'run.py')

# Name of the output executable
exe_name = 'countdown-timer'

# Output directory for the bundled app
dist_path = os.path.join(project_root, 'dist')

# Build directory for PyInstaller's working files
build_path = os.path.join(project_root, 'build')

# Path to the data directory
data_dir = os.path.join(project_root, 'data')

# PyInstaller command arguments
pyinstaller_args = [
    '--name={}'.format(exe_name),
    '--onedir',  # Create a one-folder bundle
    '--windowed',  # Application is windowed, no console
    # Add the data directory. Syntax is 'source{os.pathsep}destination_in_bundle'
    # os.pathsep is ';' on Windows, ':' on Linux/macOS
    '--add-data={}{}{}'.format(data_dir, os.pathsep, 'data'),
    '--distpath={}'.format(dist_path),
    '--workpath={}'.format(build_path),
    '--specpath={}'.format(project_root), # Place .spec file in project root
    '--clean',  # Clean PyInstaller cache and remove temporary files before building
    # '--noconfirm', # Overwrite output directory without asking
]

# Add the main script to the arguments
pyinstaller_args.append(main_script)

def build():
    print("Starting PyInstaller build...")
    print(f"Project Root: {project_root}")
    print(f"Main Script: {main_script}")
    print(f"Output Directory (dist): {dist_path}")
    print(f"Build Directory (build): {build_path}")
    print(f"Data Directory to include: {data_dir} -> data")
    
    # Ensure dist and build paths are clean if they exist from previous builds
    # PyInstaller's --clean might not remove everything if paths are outside its default structure
    if os.path.exists(dist_path):
        print(f"Removing existing dist directory: {dist_path}")
        shutil.rmtree(dist_path)
    if os.path.exists(build_path):
        print(f"Removing existing build directory: {build_path}")
        shutil.rmtree(build_path)
    
    # Create dist_path if it doesn't exist, as PyInstaller expects it for --distpath
    os.makedirs(dist_path, exist_ok=True)

    print(f"Running PyInstaller with arguments: {' '.join(pyinstaller_args)}")

    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("Build successful!")
        print(f"Executable and accompanying files are in: {os.path.join(dist_path, exe_name)}")
    except Exception as e:
        print(f"An error occurred during the build process: {e}")
        sys.exit(1)
    finally:
        # Clean up: remove the .spec file and the build directory
        spec_file = os.path.join(project_root, f'{exe_name}.spec')
        if os.path.exists(spec_file):
            print(f"Removing spec file: {spec_file}")
            os.remove(spec_file)
        # The build_path is usually removed by PyInstaller if the build is successful,
        # but we ensure it's gone, especially if --clean wasn't fully effective or build failed.
        if os.path.exists(build_path):
            print(f"Removing build directory: {build_path}")
            shutil.rmtree(build_path)
        print("Cleanup complete.")

if __name__ == '__main__':
    build()
