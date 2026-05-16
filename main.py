import sys
import os
import logging
from pathlib import Path

# Set up logging directory and file
log_dir = Path.home() / ".pyfastplot"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "pyfastplot.log"

logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("pyFastPlot")
logger.info("Application starting...")

# Check if the application is running in a standalone (frozen) environment
is_frozen = getattr(sys, 'frozen', False) or 'NUITKA_PYTHON_EXE' in os.environ

if not is_frozen:
    # In development, add 'src' to the path to enable package imports
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

try:
    from pyfastplot.app import main
except Exception as e:
    # If the app fails to start, log details to help debugging
    logger.critical(f"Failed to start pyfastplot module.")
    logger.critical(f"Error: {e}", exc_info=True)
    logger.critical(f"Current Directory: {os.getcwd()}")
    logger.critical(f"Executable: {sys.executable}")
    
    # Prevent the console from closing immediately so the user can read the error
    print(f"CRITICAL ERROR: See log file at {log_file} for details.")
    input("\nPress Enter to exit...")
    sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical("Unhandled exception during execution", exc_info=True)
        sys.exit(1)
