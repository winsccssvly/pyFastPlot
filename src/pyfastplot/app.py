import sys
import os
from PySide6.QtWidgets import QApplication

from .models.data_model import DataModel
from .views.main_window import MainWindow
from .presenters.main_presenter import MainPresenter

def resource_path(relative_path):
    """ Helper function to handle resource paths for both dev environment and compiled executable. """
    # When built with Nuitka/PyInstaller, use the temporary folder path (_MEIPASS).
    # In standard Python environment, use the current directory.
    # The root path should be 3 levels up from src/pyfastplot/app.py
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
    
    base_path = getattr(sys, '_MEIPASS', project_root)
    return os.path.join(base_path, relative_path)

def main():
    # Required object for any PySide application to manage event loops and OS interaction.
    app = QApplication(sys.argv)
    
    # Set window and taskbar icon
    icon_path = resource_path(os.path.join("assets", "data-analytics.png"))
    if os.path.exists(icon_path):
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(icon_path))
        
    # [MVP Pattern Assembly]
    # 1. Model: Handles data storage and logic
    model = DataModel()
    
    # 2. View: Handles UI components and display
    view = MainWindow()
    
    # 3. Presenter: Mediator between View and Model
    presenter = MainPresenter(view, model)
    
    # Display the main UI window
    view.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()