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

Preset tickets, available by default, are:

- *blank* &mdash; empty ticket that all.
- *endurance* &mdash; standart endurance test for RRAM cells.
- *iv-curve*, *iv-curve-set*, *iv-curve-reset*, *iv-curve-reversed* &mdash; tickets for measuring pulsed IV-curves.
- *measure* &mdash; ticket for measuring cell resistance.
- *programming*, *programming-reversed* &mdash; for programming specific resistance (see [Terminate condition](#terminate-condition)).
- *retention* &mdash; ticket for measuring the retention of the resistive states.
- *plast-dep-pot*, *plast-pot-dep* &mdash; tickets for studying potentiation and depression behaviours of the memristive cells.

By double-clicking the ticket on the right side of the window (or pressing **Edit** button), you can adjust the ticket parameters (voltage applied to the cell, number of cycles, etc.): the [Signal editing window](#signal-editing-window) opens.
**Apply to the cell** button opens [Apply window](#applying-the-experiment) where you can start the experiment.

#### Signal editing window

The signal window is opened via [Experiment plan](#configuring-your-experiment) window, it allows you to set the signal which is applied to the memristive cell.

![Signal Setup Window](assets/signal.png)

Set and reset signals can be controlled independently in the top half of the window: the pulse amplitudes (in volts) and widths (**Time: ms and μs**) can be adjusted. The **Amound** field specifies the amount of set or reset sweeps in a set-reset cycle, the **Repeat** fields specifies the total amount of set-reset cycles. If the **Dec** flag is off, the voltage sweeps from **Start** to **Stop** with the specified **Step**. If the **Dec** flag is on, the voltage also sweeps from **Stop** to **Start**.
For example, measuring 10 IV curves requires the following parameters:

|            |Start| Stop| Step | Quantity |Decrement| Time, ms| Time, μs |
|------------|-----|-----|------|----------|---------|---------|----------|
| **Reset**  | 0.0 | 1.6 | 0.05 |     1    |    +    |    0    |    100   |
|  **Set**   | 0.0 | 1.2 | 0.05 |     1    |    +    |    0    |    100   |

**Sending order:** Reset-Set; **Repeat**: 10 times

##### Standart pulse sequence

Each measurement point consists of two parts &mdash; a voltage pulse with the adjustable amplitude for changing the resistive state of the cell, and a read pulse that always follows it. The amplitude of the reading pulse is fixed in the *settings.ini* file.
During the experiment, the resistive state of the cell is controlled only via read pulses with constant amplitude.

##### Terminate condition

The terminate condition can be specified in the [Signal editing window](#signal-editing-window) and ***it is checked after every measurement point is acquired***. The **pass** condition turns the terminator off. For other condition values, you need to enter the resistance in the **Value** field (or **Min** and **Max** fields), and it will be compared to the acquired resistance.
For example, the [Signal editing window figure](#signal-editing-window) shows standart terminate condition for programming resistive states via ***write-verify algorithm***: the **condition** is set to **><**. The experiment (for this ticket only) will automatically stop when the resistance of the memory cell will be from 5000 to 5500 Ohm.
You can increase the amount of set-reset cycles to ensure that the memristive cell reaches the desired resistance range.
You can add other tickets after the programming ticket (for example, a retention ticket) to create an autonomous experiment.

### Applying the experiment

###### Signal setup result:

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