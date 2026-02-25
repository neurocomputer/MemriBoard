# MemriBoard Manual

## Table of contents

- [**Product Overview**](#product-overview)
- [**Working with individual cells**](#working-with-individual-cells)
<!-- - [Инференс нейросети](#инференс-нейросети)
- [Демо нейросети](#демо-нейросети)  -->

## Product Overview

The program can run on any operating system with python 3.9 or higher support.

### Connecting the crossbar array

The connection window appears at startup. In it, you can select a crossbar you are working with, COM-port to which the device is connected, or choose the simulation mode.

![Connection window](assets/connect_window.png)

It is possible to add multiple crossbars if the device is used with different crossbars. A separate interaction history log is created for each.

#### Creating a database entry for new crossbar array

![Crossbar creation](assets/add_crossbar.png)

When adding a crossbar array, enter its **serial number**, the number of rows (**BL** &mdash; Bit Line) and columns (**WL** &mdash; Word Line) in the crossbar array (applicable for various architectures and experimental connection), the type of commands (switched, without switching), **crossbar type** (simulator or real), and, if necessary, a comment.

If you are adding a real crossbar, you must first connect the device to the USB port, and specify the port name in the **Choose COM-port** field.
After connecting, a new crossbar is created in memory, or an existing one is loaded, and a view and interaction window opens.

#### Settings

![Settings window](assets/settings.png)

- **Update** the configutation from settings.ini.
- Selection of **ADC bit depth**: 10 bits (Arduino ADC) or 14 bits (external ADC, oversampling).
- Adjustment of **calibration coefficient**.
- Adjustment of the software **current limiter (CC)** (works by predicting the current of the next pulse, based on last measured resistance).

## Main window

![Window](assets/connected.png)

Main window has a table which displays resistances of the memory cells. At the top of the window, there are general functionality buttons:

- **RRAM** for working with the crossbar array as a memory bank.
- **Math** for matrix multiplication.
- **ANN** for working with neural networks (WIP).
- [**Tests**](#tests) to conduct general crossbar testing on multiple cells.
- **Snapshot** shows a color map of the resistances.
- [**Settings**](#settings).

### Working with individual cells

In addition to the general functionality, it is possible to work with each cell separately. To open the cell menu, double-click on it with the left mouse button.

![Crossbar_cell](assets/crossbar_cell.png)

The window that opens displays the basic information about the cell and contains basic functionality for working with it:

- **Update** &mdash; read the resistance of the cell.
- [**History**](#history-window) &mdash; get the journal of all experiments conducted on the cell.
- [**New experiment**](#configuring-your-experiment) &mdash; create new experiment plan.

#### History window

![Cell History Window](assets/history.png)

The window displays all experiments performed on the cell. By clicking on the experiment you can get it's brief overview (**Brief** tab on the right side of the window) or ***export measurement data*** to csv (**Full** tab on the right side of the window, then press **Export to csv**). The data is exported separately for each part of the experiment (ticket).
In lower left part of the window, you can **load the experiment** to [repeat](#signal-editing-window) it or export the experiment plan as a single ticket.

### Configuring your experiment

Experiment configuration window can be opened via [Cell info](#working-with-individual-cells) window or via [Tests](#tests) window.

![Experiment plan window](assets/new_exp.png)

The window allows you to create a new experiment with a cell. It is made up of tickets &mdash; preset experiments, such as iv-curve, endurance, programming, etc. You can **add** multiple tickets from left side of the window to the experiment plan (**Add to plan** button), or you can create a new ticket (**New** button in the bottom left corner). The **Load** button on the right side of the window allows you to load a ticket that was previously applied to one of the cells. You can also directly **import** tickets from a *.json* file.
You can enter the experiment **name** in the lower right part of the window.
By double-clicking the ticket on the right side of the window (or pressing **Edit** button), you can adjust the ticket parameters (voltage applied to the cell, number of cycles, etc.): the [Signal editing window](#signal-editing-window) opens.

###### Signal editing window:
When editing a signal or creating a new one, the signal editing window opens. Each signal consists of two parts - an adjustable pulse of action on the cell, and a pulse of reading the state of the cell. Pulse of interaction has settings of amplitude, duration, and order of signal supply in case of its multiplicity. The signal can be either forward (reset) or reverse (set). It is possible to set the reason for the interruption of the signal and preview its graph. Start, stop and step are indicated in volts.
For example, to remove the VAC of the cell, the following parameters are indicated:

|        |Start| Stop| Step | Quantity |Decrement| MS| ISS |
|--------|-----|-----|------|----------|---------|---|-----|
| Direct | 0.0 | 1.6 | 0.05 |     1    |    +    | 0 | 100 |
|  Back  | 0.0 | 1.2 | 0.05 |     1    |    +    | 0 | 100 |

*Signaling: straight-back; Repeat: 1 time*

###### Signal setup result:
![Signal Setup Window](assets/signal.png)

To run the created experiment, click the Apply To Cell button to apply it to the selected cell.
After that, the experiment window will open. It contains:
- Graph rendering field. It is possible to change the data displayed along the axes and change the display method (points, line, asterisks). If you do not want to render the graph in real time, it is recommended that you turn off the Display setting below.
- Experiment control panel. Buttons for starting, pausing and stopping the experiment, as well as a scale for the progress of the experiment.
After the experiment is completed, a notification of completion will be shown, and in the event of a software [current_limiter](#Settings).
###### BAX Cell Experiment Window:
![Experiment Window](assets/apply.png)
</p>

### Tests


<!-- 
### Инференс нейросети


### Демо нейросети -->