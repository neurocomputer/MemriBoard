"""
Подключение по COM порту через pyserial
Можно заменить на другую библиотеку сохранив методы
"""

import serial

class Serial():
    """
    Подключение по COM порту через pyserial
    """

    ser: serial.Serial = None

    def __init__(self):
        self.baudrate = 115200

    def com_open(self, portnum, timeout=0.075):
        """
        Открытие COM порта
        """
        try:
            self.ser = serial.Serial(portnum, baudrate=self.baudrate, timeout=timeout)
        except serial.SerialException as se:
            print("Ошибка порта:", str(se))

    def com_is_open(self):
        """
        Проверка открыт ли COM порт
        """
        status = False
        if self.ser is not None:
            status = self.ser.is_open
        return status

    def com_whait_ready(self, timeout):
        """
        Ожидание готовности COM порта
        """
        pass # в pyserial не реализовано

    def com_can_read_line(self):
        """
        Порт может читать
        """
        return True # в pyserial не реализовано

    def com_read_line(self):
        """
        Прочесть линию из порта
        """
        line = None
        connect = 1
        while connect:
            try:
                line = self.ser.readline()
                if line:
                    break
                connect -= 1
            except OSError as se:
                print("Ошибка порта:", str(se))
                break
        return line

    def com_close(self):
        """
        Закрытие COM порта
        """
        if self.ser is not None:
            if self.ser.is_open:
                self.ser.close()

    def com_write(self, data):
        """
        Запись в COM порт
        """
        status = -1
        try:
            status = self.ser.write(data)
        except OSError as se:
            print("Ошибка порта:", str(se))
        return status
