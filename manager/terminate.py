"""
Терминаторы. Они нужны чтобы прерывать работу очереди
по условию. Условие задается для каждого тикета одно и
сравнивается с результатом. Результат может быть 
представлен списком в котором на позиции 0 стоит число int.

Терминатор можно создать свой по образу имеющихся.
Поскольку терминатор создается один для тикета как
экземпляр класса, то можно создавать терминаторы с
накоплением результата. Если в список добавить id, то
можно создавать терминаторы для четных и не четных
значений результата.

pass: pass
equal: res == value : ==
equal_in: min <= res <= max : ><
equal_out: res <= min or res >= max : <>
less: int res < value : <
bigger: res > value : >
"""

# pylint: disable=too-few-public-methods

class Pass():
    """
    Прерывание не требуется
    """

    def __init__(self, value: int) -> None:
        pass

    def __call__(self, result: list) -> bool:
        return False

class Equal():
    """
    Проверка равности
    """

    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self, result: list) -> bool:
        flag = False
        if result[0] == self.value:
            flag = True
        return flag

class EqualIn():
    """
    Проверка равности в диапазоне
    """

    def __init__(self, values: list) -> None:
        self.minv = values[0]
        self.maxv = values[1]

    def __call__(self, result: list) -> bool:
        flag = False
        if self.minv <= result[0] <= self.maxv:
            flag = True
        return flag

class EqualOut():
    """
    Проверка равности за диапазоном
    """

    def __init__(self, values: list) -> None:
        self.minv = values[0]
        self.maxv = values[1]

    def __call__(self, result: list) -> bool:
        flag = False
        if result[0] <= self.minv or result[0] >= self.maxv:
            flag = True
        return flag

class Less():
    """
    Проверка меньше
    """

    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self, result: list) -> bool:
        flag = False
        if result[0] < self.value:
            flag = True
        return flag

class Bigger():
    """
    Проверка больше
    """

    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self, result: list) -> bool:
        flag = False
        if result[0] > self.value:
            flag = True
        return flag

# привязка ярлыков к терминаторам
terminators = {'pass': Pass,
               '==': Equal,
               '><': EqualIn,
               '<>': EqualOut,
               '<': Less,
               '>': Bigger
               }
