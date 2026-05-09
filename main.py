import sys
import os

# Check if the application is running in a standalone (frozen) environment
is_frozen = getattr(sys, 'frozen', False) or 'NUITKA_PYTHON_EXE' in os.environ

if not is_frozen:
    # In development, add 'src' to the path to enable package imports
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

try:
    from pyfastplot.app import main
except ImportError as e:
    # If the app fails to start, print details to help debugging
    print(f"CRITICAL: Failed to import pyfastplot module.")
    print(f"Error: {e}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Executable: {sys.executable}")
    # Prevent the console from closing immediately so the user can read the error
    input("\nPress Enter to exit...")
    sys.exit(1)

if __name__ == "__main__":
    main()
