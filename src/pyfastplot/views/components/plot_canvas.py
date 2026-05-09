from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
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
        if not hasattr(self, 'annot') or not self.annot: return
        
        vis = self.annot.get_visible()
        if event.inaxes == self.axes:
            min_dist = float('inf')
            closest_line = None
            closest_idx = None
            
            for line in self.axes.get_lines():
                cont, ind = line.contains(event)
                if cont:
                    x, y = line.get_data()
                    # Coordinates of data points that fell within the event radius
                    valid_indices = ind["ind"]
                    xy_data = np.column_stack((x[valid_indices], y[valid_indices]))
                    
                    # Convert to display (pixel) coordinates for visual comparison with mouse cursor
                    xy_display = self.axes.transData.transform(xy_data)
                    event_xy = np.array([event.x, event.y])
                    
                    # Calculate Euclidean distances between mouse cursor and each point
                    distances = np.linalg.norm(xy_display - event_xy, axis=1)
                    
                    # Find the nearest point within this specific line segment
                    local_min_idx = np.argmin(distances)
                    local_min_dist = distances[local_min_idx]
                    
                    # Check if this is the overall closest point among all lines
                    if local_min_dist < min_dist:
                        min_dist = local_min_dist
                        closest_line = line
                        closest_idx = valid_indices[local_min_idx]
            
            if closest_line is not None:
                self.update_annot(closest_line, {"ind": [closest_idx]})
                self.annot.set_visible(True)
                self.figure.canvas.draw_idle()
                return
                
        if vis:
            self.annot.set_visible(False)
            self.figure.canvas.draw_idle()

    def update_annot(self, line, ind):
        x, y = line.get_data()
        idx = ind["ind"][0]
        self.annot.xy = (x[idx], y[idx])
        label = line.get_label()
        if label and not label.startswith("_"):
            text = f"[{label}]\nX: {x[idx]:.4g}\nY: {y[idx]:.4g}"
        else:
            text = f"X: {x[idx]:.4g}\nY: {y[idx]:.4g}"
        self.annot.set_text(text)

    def set_fig_size(self, width, height, dpi=100):
        self.figure.set_size_inches(width, height)
        self.setFixedSize(int(width * dpi), int(height * dpi))
        self.draw()
