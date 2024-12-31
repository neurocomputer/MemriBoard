"""
Модель мемристивного устройства
Создана по модели Гусейнова Давуда Вадимовича. Примеры применения в:

Kipelkin, Ivan M., et al. "Memristor-based model of neuronal excitability
and synaptic potentiation." Frontiers in Neuroscience 18 (2024): 1456386.
https://doi.org/10.3389/fnins.2024.1456386

Kipelkin, Ivan, et al. "Mathematical and experimental model of neuronal
oscillator based on memristor-based nonlinearity." Mathematics 11.5 (2023): 1268.
https://doi.org/10.3390/math11051268
"""

import math as m
import numpy as np

class MemristorModel():
    '''
    Модель мемристивного устройства
    '''
    step: float = 1/1000000 # шаг моделирования (1 мкс)
    state_variable: float = 1.0 # переменная состояния (1.0 - СНС)
    area_filament: float = 1.7e-12 # площадь филаментов
    fi_ion: float = 0.8 # энергетический барьер
    voltage_react_reset: float = 0.4 # пороговое напряжение reset
    voltage_react_set: float = -0.4 # пороговое напряжение set
    BOLZMAN: float = 1.38e-23 # постоянная Больцмана
    ELECTRON_CHARGE: float = 1.6e-19 # заряд электрона
    resistance_max: int = 100000 # максимальное сопротивление в кОм
    resistance_min: int = 100 # минимальное сопротивление в кОм
    min_w_lock_noise: float = 0.01 # границы шума
    max_w_lock_noise: float = 0.7 # границы шума
    noise_rate: float = 0.03 # уровень шума
    noise_flag: int = 1 # флаг шума
    # эмпирические константы
    c_reset: float = 0.0004
    c_set: float = 0.0002
    t_reset: int = 88
    t_set: int = 7
    B: float = 8e22
    T: int = 300
    C1: float = 0.2
    DR: int = 1
    fi_electron: int = 1

    def apply_voltage(self, v_inp: float) -> float:
        '''
        Подача напряжения v_inp на мемристор
        '''
        if self.t_reset > 0:
            r_reset = self.c_reset * self.t_reset
        if self.t_set > 0:
            r_set = self.c_set * self.t_set
        if self.t_reset < 0:
            r_reset = self.c_reset / abs(self.t_reset)
        if self.t_set < 0:
            r_set = self.c_set / abs(self.t_set)
        if self.t_reset == 0:
            r_reset = self.c_reset * 1
        if self.t_set == 0:
            r_set = self.c_set * 1
        A = self.DR*1e8*m.exp(1-300/self.T)
        if v_inp > 0:
            if v_inp >= self.voltage_react_reset:
                self.state_variable = self.state_variable-1e13*self.step*r_reset*m.exp(self.ELECTRON_CHARGE*(-self.fi_ion+self.C1*v_inp)/(self.BOLZMAN*self.T))
            j_lin = A * v_inp
            j_nonlin = self.B*v_inp*m.exp(-(self.ELECTRON_CHARGE/(self.BOLZMAN*self.T))*(self.fi_electron-0.5*0.07*m.sqrt(v_inp)))
        elif v_inp < 0:
            if v_inp < self.voltage_react_set:
                self.state_variable = self.state_variable+1e13*self.step*r_set*m.exp(self.ELECTRON_CHARGE*(-self.fi_ion-self.C1*v_inp)/(self.BOLZMAN*self.T))
            j_lin = A * v_inp
            j_nonlin = self.B*v_inp*m.exp(-(self.ELECTRON_CHARGE/(self.BOLZMAN*self.T))*(self.fi_electron-0.5*0.07*m.sqrt(abs(v_inp))))
        elif v_inp == 0:
            return 0
        # добавляем шум
        if self.noise_flag:
            if (self.min_w_lock_noise < self.state_variable < self.max_w_lock_noise) and (not (self.voltage_react_set < v_inp < self.voltage_react_reset)):
                self.state_variable += np.random.normal(loc=0, scale=abs(self.state_variable*self.noise_rate))
            if self.state_variable > 1:
                self.state_variable = 1
            if self.state_variable < 0:
                self.state_variable = 0
            if self.state_variable <= self.min_w_lock_noise and (not (self.voltage_react_set < v_inp < self.voltage_react_reset)):
                self.state_variable += abs(np.random.normal(loc=0.01, scale=abs(self.noise_rate)))
        # считаем ток
        current = (self.state_variable*j_lin+(1-self.state_variable)*j_nonlin)*self.area_filament
        if self.resistance_max:
            if v_inp/current > self.resistance_max:
                current = v_inp/self.resistance_max
        if self.resistance_min:
            if v_inp/current < self.resistance_min:
                current = v_inp/self.resistance_min
        return current
