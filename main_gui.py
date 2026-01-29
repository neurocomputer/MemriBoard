"""
Графический интерфейс окна
"""

#pylint: disable=E0611,E1101

import os
import sys
import numpy as np

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QWidget, QFileDialog, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtCore import Qt, QRect, QPoint

# загрузка модели
from MemNet.componenets import load_model
from MemNet.matmul import ElementWiseMatMul
#from MemriCORE.rpi_modes import RPI_modes
#import MemriCORE.rp5_fpga_c.fpga_wrapper as driver
import RPi.GPIO as gpio
from MemriCORE.rp5_python.rpi_modes import RPI_modes # pylint: disable=C0415

gpio.setwarnings(False)

#conn = RPI_modes()
conn = RPI_modes()

model_path = 'PlaneDetection/[0.015907004475593567, 1.0]'
model_name = 'best_class.custom'
model = load_model(os.path.join(model_path, model_name))

#core_1 = ElementWiseMatMul(model_path, conn)
#core_1.read_mem_weights()
#core_1.find_weights_model(model.layers[0].get_weights(), layer_id='0_Conv2D')

core_2 = ElementWiseMatMul(model_path, conn)
core_2.read_mem_weights()
core_2.find_weights_model(model.layers[2].get_weights(), layer_id='2_Dense')

#model.layers[0].matmul = core_1.process_layer
model.layers[2].matmul = core_2.process_layer

def gray_сonversion(image):
    grayValue = 0.07 * image[:,:,2] + 0.72 * image[:,:,1] + 0.21 * image[:,:,0]
    gray_img = grayValue.astype(np.uint8)
    return gray_img

def qimage_to_array_bytes(qimage):
    """Convert QImage to numpy array using bytes"""
    qimage = qimage.convertToFormat(QImage.Format_RGB888)

    width = qimage.width()
    height = qimage.height()

    # Получаем данные как bytes
    ptr = qimage.bits()
    ptr.setsize(qimage.byteCount())

    # Создаем array из bytes
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 3))

    return arr

class ImageViewer(QLabel):
    """
    Кастомный отображатель картинок
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 1px solid gray;")
        self.setFixedSize(640, 480)

        # Переменные для выделения области
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.selection_rect = QRect()

    def setPixmap(self, pixmap): #pylint: disable=C0103
        """
        Установить картику в лейбл
        """
        super().setPixmap(pixmap.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def mousePressEvent(self, event): #pylint: disable=C0103
        """
        Событие нажатия мыши
        """
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()

    def mouseMoveEvent(self, event): #pylint: disable=C0103
        """
        Событие перемещения мыши
        """
        if self.drawing:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event): #pylint: disable=C0103
        """
        Событие отпускания мыши
        """
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.end_point = event.pos()

            # Создаем прямоугольник выделения
            x1 = min(self.start_point.x(), self.end_point.x())
            y1 = min(self.start_point.y(), self.end_point.y())
            x2 = max(self.start_point.x(), self.end_point.x())
            y2 = max(self.start_point.y(), self.end_point.y())

            self.selection_rect = QRect(x1, y1, x2 - x1, y2 - y1)
            self.update()

    def paintEvent(self, event): #pylint: disable=C0103
        """
        Событие отрисовки
        """
        super().paintEvent(event)

        # Рисуем прямоугольник выделения
        if self.drawing or not self.selection_rect.isNull():
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
            if self.drawing:
                rect = QRect(self.start_point, self.end_point).normalized()
            else:
                rect = self.selection_rect
            painter.drawRect(rect)

    def get_selection_rect(self):
        """
        Получить прямоугольное выделение на рисунке
        """
        return self.selection_rect

class MainWindow(QMainWindow):
    """
    Основное окно
    """

    original_image = None
    scaled_image = None
    scaled_cropped = None

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """
        Отрисовка интерфейса
        """
        self.setWindowTitle('Plane detection')
        #self.setGeometry(100, 100, 1200, 600)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        # Кнопка открытия изображения
        self.open_button = QPushButton('Открыть изображение')
        self.open_button.clicked.connect(self.open_image)
        button_layout.addWidget(self.open_button)

        # Layout для изображений
        images_layout = QHBoxLayout()
        main_layout.addLayout(images_layout)

        # Поле 1 - основное изображение с возможностью выделения
        self.image_label1 = ImageViewer()
        self.image_label1.setText("Откройте изображение")
        images_layout.addWidget(self.image_label1)

        # Поле 2 - выделенная область
        self.image_label2 = QLabel()
        self.image_label2.setAlignment(Qt.AlignCenter)
        self.image_label2.setStyleSheet("border: 1px solid gray;")
        self.image_label2.setMinimumSize(280, 280)
        self.image_label2.setText("Выделенная область появится здесь")
        images_layout.addWidget(self.image_label2)

        # Кнопка для извлечения выделенной области
        self.extract_button = QPushButton('Извлечь выделенную область')
        self.extract_button.clicked.connect(self.extract_selection)
        self.extract_button.setEnabled(False)
        button_layout.addWidget(self.extract_button)

        # Кнопка Распознать
        self.class_button = QPushButton('Распознать')
        self.class_button.clicked.connect(self.class_image)
        self.class_button.setEnabled(False)
        button_layout.addWidget(self.class_button)

        self.result_label = QLabel()
        self.result_label.setText("Класс изображения")
        button_layout.addWidget(self.result_label)

        # Переменные для хранения изображений
        self.original_image = None
        self.scaled_image = None

    def class_image(self):
        """
        Распознать изображение
        """
        croped_image = gray_сonversion(qimage_to_array_bytes(self.scaled_cropped))
        croped_image = croped_image[..., np.newaxis]
        output = model.predict(croped_image[np.newaxis, ...]/255)
        if output[0][0] < 0.5:
            img_class = "Небо {:.2f}".format(output[0][0])
        else:
            img_class = "БАС {:.2f}".format(output[0][0])
        self.result_label.setText(img_class)

    def open_image(self):
        """
        Открыть изображение
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение", 
            "", 
            "Images (*.jpg *.jpeg *.png *.bmp)"
        )

        if file_path:
            # Загружаем изображение
            self.original_image = QImage(file_path)
            if self.original_image.isNull():
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение")
                return

            # Масштабируем изображение до 640x480
            self.scaled_image = self.original_image.scaled(
                640, 480)

            # Отображаем в поле 1
            self.image_label1.setPixmap(QPixmap.fromImage(self.scaled_image))
            self.image_label1.selection_rect = QRect()  # Сбрасываем выделение
            self.image_label2.clear()
            self.image_label2.setText("Выделите область на левом изображении")
            self.extract_button.setEnabled(True)

    def extract_selection(self):
        """
        Извлечь изображение из выделенной области
        """
        if not self.scaled_image or self.image_label1.selection_rect.isNull():
            QMessageBox.warning(self, "Внимание", "Сначала выделите область на изображении")
            return

        # Получаем координаты выделенной области
        selection_rect = self.image_label1.get_selection_rect()

        # Проверяем, что выделение не пустое
        if selection_rect.width() == 0 or selection_rect.height() == 0:
            QMessageBox.warning(self, "Внимание", "Выделенная область слишком мала")
            return

        # Извлекаем выделенную область из масштабированного изображения
        cropped_image = self.scaled_image.copy(selection_rect)

        # Масштабируем до 28x28
        self.scaled_cropped = cropped_image.scaled(
            28, 28, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )

        # Увеличиваем для отображения (чтобы было лучше видно)
        display_image = self.scaled_cropped.scaled(
            280, 280, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )

        # Отображаем в поле 2
        self.image_label2.setPixmap(QPixmap.fromImage(display_image))

        self.class_button.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
