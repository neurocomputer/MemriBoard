"""
Сделать exe для Windows
"""
import os
import shutil
import subprocess

command = "pyinstaller --onefile main.py"
_ = subprocess.run(command, shell=True, capture_output=True, text=True)
source_directory = os.path.join(os.getcwd(),'gui','uies')
destination_directory = os.path.join(os.getcwd(),'dist','gui','uies')
try:
    shutil.copytree(source_directory, destination_directory)
    print(f"Каталог успешно скопирован из {source_directory} в {destination_directory}.")
except FileExistsError:
    print(f"Каталог {destination_directory} уже существует.")
except Exception as e:
    print(f"Ошибка при копировании каталога: {e}")
source_directory = os.path.join(os.getcwd(),'tickets')
destination_directory = os.path.join(os.getcwd(),'dist','tickets')
try:
    shutil.copytree(source_directory, destination_directory)
    print(f"Каталог успешно скопирован из {source_directory} в {destination_directory}.")
except FileExistsError:
    print(f"Каталог {destination_directory} уже существует.")
except Exception as e:
    print(f"Ошибка при копировании каталога: {e}")
shutil.rmtree(os.path.join(os.getcwd(),'build'))
os.remove(os.path.join(os.getcwd(),'crossbar_gui.spec'))
