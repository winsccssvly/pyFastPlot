from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMenu,
    QStyleFactory,
    QTreeWidget,
    QTreeWidgetItem,
)

TABLE_ROLE = Qt.ItemDataRole.UserRole
ITEM_KIND_ROLE = Qt.ItemDataRole.UserRole + 1
FILE_BASED_ROLE = Qt.ItemDataRole.UserRole + 2
LABEL_ROLE = Qt.ItemDataRole.UserRole + 3


class FileListWidget(QTreeWidget):
    file_dropped_signal = Signal(str)
    new_table_signal = Signal()
    delete_table_signal = Signal(str)
    delete_tables_signal = Signal(list)
    rename_table_signal = Signal(str, str)
    reload_table_signal = Signal(str)
    delete_all_signal = Signal()
    axis_selection_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._updating = False
        windows_style = QStyleFactory.create("Windows")
        if windows_style is not None:
            self.setStyle(windows_style)
        self.setColumnCount(1)
        self.header().hide()
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemChanged.connect(self.on_item_changed)

    def add_table_item(self, text: str, is_file_based: bool = False) -> None:
        item = QTreeWidgetItem([text])
        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
        )
        item.setData(0, TABLE_ROLE, text)
        item.setData(0, ITEM_KIND_ROLE, "table")
        item.setData(0, FILE_BASED_ROLE, is_file_based)
        self.addTopLevelItem(item)

    def update_table_columns(
        self,
        table_name: str,
        labels: list[str],
        x_label: str,
        y_labels: list[str],
    ) -> None:
        table_item = self._table_item(table_name)
        if table_item is None:
            return

        self._updating = True
        table_item.takeChildren()
        table_item.setData(0, LABEL_ROLE, x_label)
        y_set = set(y_labels)
        for label in labels:
            child = QTreeWidgetItem([label])
            child.setFlags(
                child.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEnabled
            )
            child.setData(0, TABLE_ROLE, table_name)
            child.setData(0, ITEM_KIND_ROLE, "column")
            child.setData(0, LABEL_ROLE, label)
            child.setCheckState(0, self._check_state(label in y_set))
            self._set_x_highlight(child, label == x_label)
            table_item.addChild(child)
        table_item.setExpanded(True)
        self._updating = False

    def selected_table_names(self) -> list[str]:
        names: list[str] = []
        for item in self.selectedItems():
            name = self.table_name_for_item(item)
            if name and name not in names:
                names.append(name)
        return names

    def selected_plot_sources(self) -> list[tuple[str, str, str]]:
        sources: list[tuple[str, str, str]] = []
        for index in range(self.topLevelItemCount()):
            table_item = self.topLevelItem(index)
            if table_item is None:
                continue
            table_name = table_item.text(0)
            x_label = self.x_label_for_table(table_name)
            if not x_label:
                continue
            for child_index in range(table_item.childCount()):
                child = table_item.child(child_index)
                if child is None:
                    continue
                if child.checkState(0) == Qt.CheckState.Checked:
                    sources.append((table_name, x_label, child.text(0)))
        return sources

    def table_name_for_item(self, item: QTreeWidgetItem | None) -> str:
        if item is None:
            return ""
        value = item.data(0, TABLE_ROLE)
        return str(value) if value else ""

    def x_label_for_table(self, table_name: str) -> str:
        table_item = self._table_item(table_name)
        if table_item is None:
            return ""
        for index in range(table_item.childCount()):
            child = table_item.child(index)
            if child is None:
                continue
            if child.data(0, LABEL_ROLE) == table_item.data(0, LABEL_ROLE):
                return child.text(0)
        return ""

    def y_labels_for_table(self, table_name: str) -> list[str]:
        table_item = self._table_item(table_name)
        if table_item is None:
            return []
        labels: list[str] = []
        for index in range(table_item.childCount()):
            child = table_item.child(index)
            if child is not None and child.checkState(0) == Qt.CheckState.Checked:
                labels.append(child.text(0))
        return labels

    def set_filter_text(self, text: str) -> None:
        query = text.strip().lower()
        for index in range(self.topLevelItemCount()):
            table_item = self.topLevelItem(index)
            if table_item is None:
                continue
            table_match = query in table_item.text(0).lower()
            any_child_visible = False
            for child_index in range(table_item.childCount()):
                child = table_item.child(child_index)
                if child is None:
                    continue
                child_match = query in child.text(0).lower()
                child_visible = not query or table_match or child_match
                child.setHidden(not child_visible)
                any_child_visible = any_child_visible or child_visible
            table_item.setHidden(
                bool(query) and not table_match and not any_child_visible
            )
            if query and any_child_visible:
                table_item.setExpanded(True)

    def count(self) -> int:
        return self.topLevelItemCount()

    def row(self, item: QTreeWidgetItem) -> int:
        top_item = item if item.parent() is None else item.parent()
        return self.indexOfTopLevelItem(top_item)

    def takeItem(self, index: int) -> QTreeWidgetItem | None:
        return self.takeTopLevelItem(index)

    def on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._updating:
            return
        kind = item.data(0, ITEM_KIND_ROLE)
        if kind == "table":
            self._handle_table_renamed(item)
        elif kind == "column" and column == 0:
            self.axis_selection_changed.emit(self.table_name_for_item(item))

    def show_context_menu(self, pos) -> None:
        item = self.itemAt(pos)
        table_name = self.table_name_for_item(item)
        menu = QMenu()
        new_table_action = menu.addAction("New Table")
        collapse_action = menu.addAction("Collapse All")
        delete_all_action = menu.addAction("Delete All")
        menu.addSeparator()
        reload_action = None
        delete_action = None
        set_x_action = None

        if table_name:
            if item is not None and item.data(0, ITEM_KIND_ROLE) == "column":
                set_x_action = menu.addAction("Set as X")
            table_item = self._table_item(table_name)
            if table_item is not None and table_item.data(0, FILE_BASED_ROLE):
                reload_action = menu.addAction("Reload from source")
            selected = self.selected_table_names()
            delete_text = "Delete" if len(selected) <= 1 else f"Delete {len(selected)}"
            delete_action = menu.addAction(delete_text)

        action = menu.exec(self.mapToGlobal(pos))
        if action == new_table_action:
            self.new_table_signal.emit()
        elif action == collapse_action:
            self.collapseAll()
        elif action == delete_all_action:
            self.delete_all_signal.emit()
        elif action == set_x_action and item is not None:
            self.set_x_column(item)
        elif action == delete_action and table_name:
            selected = self.selected_table_names()
            if len(selected) > 1:
                self.delete_tables_signal.emit(selected)
            else:
                self.delete_table_signal.emit(table_name)
        elif reload_action and action == reload_action:
            self.reload_table_signal.emit(table_name)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete:
            selected = self.selected_table_names()
            if len(selected) > 1:
                self.delete_tables_signal.emit(selected)
            elif selected:
                self.delete_table_signal.emit(selected[0])
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        """Handle fixed-row controls and keep column selection visually neutral."""
        if event.button() == Qt.MouseButton.LeftButton:
            for index in range(self.topLevelItemCount()):
                item = self.topLevelItem(index)
                if item is None:
                    continue
                if self._delete_button_rect(item).contains(event.pos()):
                    self.delete_table_signal.emit(self.table_name_for_item(item))
                    event.accept()
                    return
        clicked_item = self.itemAt(event.pos())
        clicked_column = (
            clicked_item is not None
            and clicked_item.data(0, ITEM_KIND_ROLE) == "column"
        )
        super().mousePressEvent(event)
        if clicked_column and clicked_item is not None:
            # Columns are controls (check or Set as X), not selected datasets.
            # Keep file-row selection visible while suppressing blue column rows.
            clicked_item.setSelected(False)

    def paintEvent(self, event) -> None:
        """Draw fixed-right delete controls and X-axis badges over tree rows."""
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            if item is None:
                continue
            rect = self._delete_button_rect(item)
            if not rect.isEmpty() and self.viewport().rect().intersects(rect):
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(190, 63, 63))
                painter.drawRoundedRect(rect, 3, 3)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "x")
            x_label = item.data(0, LABEL_ROLE)
            for child_index in range(item.childCount()):
                child = item.child(child_index)
                if child is None:
                    continue
                if child.data(0, LABEL_ROLE) != x_label:
                    continue
                badge_rect = self._x_axis_badge_rect(child)
                if badge_rect.isEmpty() or not self.viewport().rect().intersects(
                    badge_rect
                ):
                    continue
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(54, 91, 125))
                painter.drawRoundedRect(badge_rect, 3, 3)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "X axis")
        painter.end()

    def _table_item(self, table_name: str) -> QTreeWidgetItem | None:
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            if item is not None and item.text(0) == table_name:
                return item
        return None

    def _delete_button_rect(self, item: QTreeWidgetItem) -> QRect:
        """Return the viewport-fixed delete target aligned to a table row."""
        item_rect = self.visualItemRect(item)
        if item_rect.isEmpty():
            return QRect()
        size = min(16, max(12, item_rect.height() - 4))
        return QRect(
            self.viewport().width() - size - 3,
            item_rect.top() + (item_rect.height() - size) // 2,
            size,
            size,
        )

    def _x_axis_badge_rect(self, item: QTreeWidgetItem) -> QRect:
        """Return the fixed-right X-axis badge for a selected column row."""
        item_rect = self.visualItemRect(item)
        if item_rect.isEmpty():
            return QRect()
        width = 43
        height = min(16, max(12, item_rect.height() - 4))
        return QRect(
            self.viewport().width() - width - 3,
            item_rect.top() + (item_rect.height() - height) // 2,
            width,
            height,
        )

    def set_x_column(self, item: QTreeWidgetItem) -> None:
        table_item = item.parent()
        if table_item is None:
            return
        label = item.text(0)
        table_item.setData(0, LABEL_ROLE, label)
        self._apply_x_highlights(table_item, label)
        self.viewport().update()
        self.axis_selection_changed.emit(table_item.text(0))

    def _handle_table_renamed(self, item: QTreeWidgetItem) -> None:
        old_name = str(item.data(0, TABLE_ROLE) or "")
        new_name = item.text(0).strip()
        if not old_name or old_name == new_name:
            return
        name_in_use = any(
            candidate is not None
            and candidate is not item
            and candidate.text(0) == new_name
            for candidate in (
                self.topLevelItem(index) for index in range(self.topLevelItemCount())
            )
        )
        if not new_name or name_in_use:
            self._updating = True
            item.setText(0, old_name)
            self._updating = False
            return
        self.rename_table_signal.emit(old_name, new_name)
        item.setText(0, new_name)
        item.setData(0, TABLE_ROLE, new_name)
        for index in range(item.childCount()):
            child = item.child(index)
            if child is not None:
                child.setData(0, TABLE_ROLE, new_name)

    def _apply_x_highlights(self, table_item: QTreeWidgetItem, x_label: str) -> None:
        for index in range(table_item.childCount()):
            child = table_item.child(index)
            if child is not None:
                self._set_x_highlight(child, child.text(0) == x_label)

    def _set_x_highlight(self, item: QTreeWidgetItem, is_x: bool) -> None:
        """Clear row coloring; X selection is represented by an overlay badge."""
        item.setBackground(0, QBrush())
        item.setForeground(0, QBrush())
        item.setToolTip(0, "X axis" if is_x else "")

    def _check_state(self, checked: bool) -> Qt.CheckState:
        return Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
