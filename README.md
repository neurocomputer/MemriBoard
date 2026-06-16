# MemriBoard

## Memristors are coming!

This program is designed to conduct experiments on memristors and memristrive crossbar arrays using various measurement architectures (for example, MemArdBoard and MemRaspBoard boards). The program includes the functionality of taking measurements and taking various characteristics of memristors, automatic testing, using memristors as ReRAM memory, performing mathematical operations and working with artificial neural networks. The program also has a memristor simulator, so you can try it without the hardware.

![Program view](docs/assets/general.png)

## Installation

To run MemriBoard, you need a Python interpreter with a version of at least 3.9.6. To clone the repository, run the command:

```bash
git clone git@github.com:neurocomputer/MemBoard.git
```

Next, configure the virtual environment and install the necessary packages:

```bash
python3 -m venv venv
. venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### First launch

Use the file 'main.py' to start the program. After starting the program, the files `settings.ini` (contains the necessary settings), `base.db` (database of experimental results), `app.log` (program log) will be automatically created in the directory. When you are using the app in simulation mode, files with the extension `.cb` containing the memristor array model will also be created.

## User manual

User manuals are available in the [`/docs` folder](https://github.com/neurocomputer/MemBoard/blob/main/docs/README.md) in this repository.

## Pre-built binaries for Windows

For windows users there are pre-built binaries available. Dowload the archive below and unpack it. There are two folders inside (`gui`, `tickets`) and `main.exe` file. Run it to start the application. When updating the app, you only need to change `main.exe` file. In this case, all configuration and experiment data will remain in new version.

|Date|Link|Commentary|
|-|-|-|
|2025.02.16|[Download .zip](https://disk.yandex.ru/d/mRvaQKJZvJ8cKg)||
|2025.02.18|[Download .zip](https://disk.yandex.ru/d/sDn3gHRMWB_Ngw)|Testing updated|
|2025.02.28|[Download .zip](https://disk.yandex.ru/d/0tTmugFL6xE7eQ)|Many bugfixes|
|2025.03.10|[Download .zip](https://disk.yandex.ru/d/xJ0hcCIJJtwVqg)|Testing updated|

## Feedback

If you found a bug or have any questions or suggestions, please email `seach@inbox.ru` or create an [issue on GitHub](https://github.com/neurocomputer/MemriBoard/issues).
