import sys
import os

# Add 'src' directory to the Python path to enable package-style imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyfastplot.app import main

if __name__ == "__main__":
    main()
