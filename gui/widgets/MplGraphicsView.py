from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure



class MplGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.plot_scene = QGraphicsScene(self)
        self.setScene(self.plot_scene)
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.plot_scene.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        
        self.ax.plot([1, 2, 3], [1, 4, 9])
        
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.canvas.resize(self.viewport().size())
        self.plot_scene.setSceneRect(0, 0, self.viewport().width(), self.viewport().height())