from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=6, height=5, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.set_fig_size(width, height, dpi)
        
        self.init_annot()
        self.figure.canvas.mpl_connect("motion_notify_event", self.hover)

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
        if dpi is None:
            dpi = self.figure.get_dpi()
        self.figure.set_size_inches(width, height)
        self.figure.set_dpi(dpi)
        self.figure.tight_layout()
        self.draw_idle()
