import logging
import os
import sys
from pathlib import Path

LOG_DIR = Path.home() / ".pyfastplot"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "pyfastplot.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("pyFastPlot")
logger.info("Application starting...")


def _is_frozen() -> bool:
    """Return True when running from a bundled executable."""
    return getattr(sys, "frozen", False) or "NUITKA_PYTHON_EXE" in os.environ


def _configure_dev_import_path() -> None:
    """Add the local src layout to sys.path during source-tree execution."""
    if _is_frozen():
        return

    src_path = Path(__file__).resolve().parent / "src"
    src_text = str(src_path)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)


_configure_dev_import_path()

try:
    from pyfastplot.app import main
except Exception as exc:
    logger.critical("Failed to start pyfastplot module.", exc_info=True)
    logger.critical("Error: %s", exc)
    logger.critical("Current directory: %s", Path.cwd())
    logger.critical("Executable: %s", sys.executable)
    print(f"CRITICAL ERROR: See log file at {LOG_FILE} for details.")
    if not _is_frozen():
        input("\nPress Enter to exit...")
    sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.critical("Unhandled exception during execution", exc_info=True)
        sys.exit(1)
