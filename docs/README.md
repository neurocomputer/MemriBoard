## Table of contents

- [Product Overview](#Product-Overview)
- [Cells operating](#Cells-operating)
<!-- - [Инференс нейросети](#инференс-нейросети)
- [Демо нейросети](#демо-нейросети)  -->

### Product Overview
<p>The program can run on any operating system with python 3.9 or higher support.</p>
<p>A start-up window appears at startup. In it, you can select the COM port to which the device is connected, or select the mode of the device software simulation:</p> 

###### Starting connection window:
![Starting connection window](assets/connect_window.png)

<p>It is possible to add multiple crossbars if the device is used with different crossbars. A separate interaction history log is created for each.</p>

<p>When adding a crossbar, you enter its serial number, the number of rows and columns in the crossbar (applicable for various architectures and experimental connection), the type of commands (switched, without switching), the type of crossbar, and, if necessary, a comment:</p>


###### Crossbar creation window:
![Connection window unwrapped](assets/add_crossbar.png)

###### Settings
- Configuration update functionality from settings.ini.
- Selection of ADC width (10 bits (Arduino ADC) and 14 bits (external ADC, oversampling)).
- Adjustment of calibration factor.
- Adjustment of the software current limiter (by predicting the current of the next pulse, based on the resistance).  
###### Settings window:
![Settings window](assets/settings.png)



<p>
If you are adding a real crossbar, you must first connect the device to the USB port, and specify the port name in the "Select COM port" field.
After connecting, a new crossbar is created in memory, or an existing one is loaded, and a view and interaction window opens.

##### Main window:
![Window](assets/connected.png)
- RRAM for working with memory.
- Math for matrix multiplication.
- ANN for working with neural networks.
- Tests to conduct general crossbar testing with multiple cells.
- Snapshot contains a crossbar color map.
- [Settings](#Settings).
</p>

### Working width individual cells
<p>In addition to the general functionality, it is possible to work with each cell separately. To open the cell menu, double-click on it with the left mouse button.

###### Crossbar cell Window:
![Crossbar_cell](assets/crossbar_cell.png)

The window that opens displays the basic information about the cell and contains basic functionality for working with it:


- "Update" - read the resistance of the cell.
- ###### "History"
    Opens a window displaying all experiments performed on the cell. By clicking on the experiment you can get it's brief overview ("Brief" tab on the right side of the window) or **export measurement data** to csv ("Full" tab on the right side of the window, then press "Export to csv"). The data is exported separately for each part of the experiment (ticket).
    In lower left part of the window, you can **load the experiment** to [repeat](#signal-editing-window) it or export the experiment plan as a single ticket.
    ![Cell History Window](assets/history.png)
- "New experiment" - opens the window for creating an experiment.
Allows you to create a new experiment with a cell. It is made up of preset signals, it is possible to add your own type of signal, for this you need to press the "New Experiment" button. To add a signal to the experiment, select the signal and click twice with the left mouse button, or click the "Add to Plan" button.
On the right is a column with the experimental plan, where the sequence of signals is described. If necessary, you can edit the parameters of the signal, move it relative to the rest, or delete it. After setting the parameters, you must enter the name of the experiment.
###### Signal editing window:

![Signal Edit Window](assets/new_exp.png)
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


<!-- 
### Инференс нейросети


### Демо нейросети -->