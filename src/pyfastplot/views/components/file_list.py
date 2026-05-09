from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QListWidget, QMenu, QListWidgetItem

class FileListWidget(QListWidget):
    file_dropped_signal = Signal(str)
    delete_table_signal = Signal(str)
    rename_table_signal = Signal(str, str) # old_name, new_name
    reload_table_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemChanged.connect(self.on_item_changed)
        
    def add_table_item(self, text, is_file_based=False):
        super().addItem(text)
        item = self.item(self.count() - 1)
        if item:
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setData(Qt.ItemDataRole.UserRole, item.text())
            item.setData(Qt.ItemDataRole.UserRole + 1, is_file_based)
        
    def on_item_changed(self, item):
        old_name = item.data(Qt.ItemDataRole.UserRole)
        new_name = item.text()
        if old_name and new_name and old_name != new_name:
            self.rename_table_signal.emit(old_name, new_name)
            item.setData(Qt.ItemDataRole.UserRole, new_name)

    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        if item is not None:
            menu = QMenu()
            is_file_based = item.data(Qt.ItemDataRole.UserRole + 1)
            
            reload_action = None
            if is_file_based:
                reload_action = menu.addAction("Reload from source")
                
            delete_action = menu.addAction("Delete table")
            
            action = menu.exec(self.mapToGlobal(pos))
            if action == delete_action:
                self.delete_table_signal.emit(item.text())
            elif reload_action and action == reload_action:
                self.reload_table_signal.emit(item.text())

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()
            
    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()
            
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.csv'):
                    self.file_dropped_signal.emit(file_path)
