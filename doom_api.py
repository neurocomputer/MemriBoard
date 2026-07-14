"""API for doom"""
import os
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal, QThread

from manager.service import a2r


ticket_folder = os.path.join(os.getcwd(), 'tickets')
ticket_0_name = 'SIM_RESET'
ticket_1_name = 'SIM_SET'




def doom_drawer(window: QMainWindow) -> None:    
    
    



class Write_All_Cells_binary(QThread):
    """
    Послать одинаковый тикет на все ячейки
    """
    count_changed = pyqtSignal(int)
    progress_finished = pyqtSignal(int)

    def __init__(self, ticket_0, ticket_1, matrix: bool, parent=None):
        QThread.__init__(self, parent)
        self.parent = parent
        self.ticket_0 = ticket_0
        self.ticket_1 = ticket_1
        self.matrix = matrix
        self.need_stop = False

    def run(self):
        """
        Запуск потока посылки тикета
        """
        counter = 0
        for i in range(self.parent.man.col_num):
            if self.need_stop:
                break
            for j in range(self.parent.man.row_num):
                if self.need_stop: 
                    break
                self.ticket["params"]["wl"] = i
                self.ticket["params"]["bl"] = j
                # временное решение, лучше переписать на потоки
                _, memristor_id = self.parent.man.db.get_memristor_id(i, j, self.parent.man.crossbar_id)
                for task in self.parent.man.menu[self.ticket['mode']](self.ticket['params'],
                                                 self.ticket['terminate'],
                                                 self.parent.man.blank_type):
                    result = self.parent.man.conn.impact(task[0]) # result = (resistance, id)
                try:
                    last_resistance = int(a2r(self.parent.man.gain,
                                              self.parent.man.res_load,
                                              self.parent.man.vol_read,
                                              self.parent.man.adc_bit,
                                              self.parent.man.vol_ref_adc,
                                              self.parent.man.res_switches,
                                              result[0]))
                except IndexError:
                    last_resistance = 0
                _ = self.parent.man.db.update_last_resistance(memristor_id, last_resistance)
                counter += 1
                self.count_changed.emit(counter)
        self.progress_finished.emit(counter)


if __name__ == '__main__':
    main()