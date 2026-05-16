from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QSizePolicy, QWidget
from PySide6.QtCore import QRect, QTimer
import numpy as np

class AspectRatioWidget(QWidget):
    def __init__(self, widget, width, height, parent=None):
        super().__init__(parent)
        self.aspect_ratio = float(width) / float(height)
        self.widget = widget
        self.widget.setParent(self)
        
    def set_aspect_ratio(self, width, height):
        self.aspect_ratio = float(width) / float(height)
        from PySide6.QtGui import QResizeEvent
        # Trigger resize event to recalculate safely
        if self.size().width() > 0 and self.size().height() > 0:
            self.resizeEvent(QResizeEvent(self.size(), self.size()))
        
    def resizeEvent(self, event):
        w = self.width()
        h = self.height()
        
        if h == 0 or w == 0: return
        
        current_aspect = w / h
        
        if current_aspect > self.aspect_ratio:
            # Too wide, constrain width
            new_w = int(h * self.aspect_ratio)
            new_h = h
        else:
            # Too tall, constrain height
            new_w = w
            new_h = int(w / self.aspect_ratio)
            
        # Center the widget
        x = (w - new_w) // 2
        y = (h - new_h) // 2
        
        new_rect = QRect(x, y, new_w, new_h)
        # Only set geometry if it actually changed to prevent infinite layout loops
        if self.widget.geometry() != new_rect:
            self.widget.setGeometry(new_rect)

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=6, height=5, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        
        # Set size policy to expand and fit the layout
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(100, 100)
        
        self.init_annot()
        self.figure.canvas.mpl_connect("motion_notify_event", self.hover)
        
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._apply_resize)

    def init_annot(self):
        # Initialize tooltip (annotation) box
        self.annot = self.axes.annotate(
            "", xy=(0,0), xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round4,pad=0.5", fc="lightyellow", ec="black", lw=0.5, alpha=0.9),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0")
        )
        self.annot.set_visible(False)
        self.annot.set_zorder(100)

    def hover(self, event):
        if not hasattr(self, 'annot') or not self.annot:
            return
            
        vis = self.annot.get_visible()
        if event.inaxes == self.axes:
            found = False
            for line in self.axes.get_lines():
                cont, ind = line.contains(event)
                if cont:
                    # Get the specific point closest to the mouse
                    xdata, ydata = line.get_data()
                    idx = ind['ind'][0]
                    x, y = xdata[idx], ydata[idx]
                    
                    self.annot.xy = (x, y)
                    label = line.get_label()
                    text = f"{label}\nX: {x:.3f}\nY: {y:.3f}"
                    self.annot.set_text(text)
                    self.annot.set_visible(True)
                    found = True
                    break
            
            if not found and vis:
                self.annot.set_visible(False)
            
            if found or vis != self.annot.get_visible():
                self.figure.canvas.draw_idle()
        else:
            if vis:
                self.annot.set_visible(False)
                self.figure.canvas.draw_idle()

    def set_fig_size(self, width, height, dpi=None):
        self.export_width = float(width)
        self.export_height = float(height)
        if dpi is not None:
            self.export_dpi = dpi
            
        w = self.width()
        if w > 0 and self.export_width > 0:
            self._pending_width = w
            self._apply_resize()

    def resizeEvent(self, event):
        # Allow base class to do its internal resize logic first
        super().resizeEvent(event)
        
        # Override the figure size to keep physical inches constant and scale via DPI.
        # Use a timer to debounce the expensive tight_layout and redraw.
        if hasattr(self, 'export_width') and hasattr(self, 'export_height') and self.export_width > 0:
            self._pending_width = event.size().width()
            self._resize_timer.start(100) # 100ms debounce

    def _apply_resize(self):
        w = getattr(self, '_pending_width', 0)
        if w > 0 and hasattr(self, 'export_width') and self.export_width > 0:
            new_dpi = w / self.export_width
            self.figure.set_size_inches(self.export_width, self.export_height, forward=False)
            self.figure.set_dpi(new_dpi)
            self.figure.tight_layout()
            self.draw_idle()
