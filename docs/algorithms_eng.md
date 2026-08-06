# Algorithms in MemriBoard

## Table of contents

- [Working with algorithms](#working-with-algorithms)
  - [Creating and using an algorithm](#creating-and-using-an-algorithm)
  - [Algorithm editor](#algorithm-editor)
  - [Writing an algorithm](#writing-an-algorithm)
- [Built-in functions](#built-in-functions)
  - [1. Utility functions](#1-utility-functions)
    - [last_resistance](#last_resistance)
    - [set_last_resistance](#set_last_resistanceresistance)
    - [get_ticket_dict](#get_ticket_dictname-path_to_folderoptional--none)
  - [2. Functions that send tickets](#2-functions-that-send-tickets)
    - [send_ticket](#send_ticketname-path_to_folderoptional--none)
    - [send_ticket_dict](#send_ticket_dictticket)
    - [send_experiment](#send_experimentname-path_to_folderoptional--none)
    - [send_experiment_dict](#send_experiment_dictexperiment)
    - [measure_resistance](#measure_resistance)
- [Examples of the algorithms](#examples-of-the-algorithms)
  - [Example with a branch](#example-with-a-branch-example_if)
  - [Example with a cycle](#example-with-a-cycle-example_for_cycle)

## Working with algorithms

### Creating and using an algorithm

You can create an algorithm on the [experiment configuration window](README.md#configuring-your-experiment). Saved algorithms are show in the right part of the window. To add the algorithm to the experiment plan, you need to double-click its name. You also can create a new algorithm. Double-clicking the algorithm in the experiment plan opens [algorithms editor](#algorithm-editor).

___

### Algorithm editor

In the top part of the window, you can enter the name of the algorithm, show [built-in-functions](#built-in-functions), and open this manual. In the bottom right part of the window there are check algorithm button and two save buttons: **Save** button saves changes to the experiment plan, **save to algorithms folder** button saves the algorithm both to the experiment plan and to the `MemriBoard/algorithms` folder. Changing the name of the algorithm saves it to a new file.

Algorithms can call different [tickets](README.md#configuring-your-experiment) based on the current memristor state. Tickets, which are called from algorithm by a link to the file (or by ticket name), are tied to the algorithm file and can be exported via **ticket export** button. By default, the algorithm takes tickets from the `MemriBoard/tickets` folder. If tickets are exported to another folder, you will need to specify this folder in the argument of all functions calling this ticket.

___

### Writing an algorithm

In the central part of the window there is an algorithm editor. The algorithm is written in Python language, which allows for using branches and cycles. You can also import libraries (such as numpy), create variables, functions, etc.

The algorithm must define the **algorithm** function with no arguments. This function is transformed to the ticket generator used in the experiment. Before saving the algorithm, you can press **Check** button which launches the algorithm in the test mode and prints occurred errors to the **Checking output** field.

To interact with the tickets and memristor parameters there are [built-in functions](#built-in-functions), which you can use in the algorithms.

___

## Built-in functions

There are two types of built-in functions which you can use in the algorithms.

### 1. Utility functions

These functions interact with memristor parameters and allow the user to interact with tickets in the algorithm:

___

### `last_resistance()`

Get the last measured resistance of the memristor. The value of this variable is updated automatically after each ticket is finished.

***Returns:***

- **last_resistance** (`float`)

An example of using this function is available in the [example with a branch](#example-with-a-branch-example_if).

___

### `set_last_resistance(resistance)`

Sets the last resistance variable manually. The value of this variable is updated automatically after each ticket is finished. This function doesn't return any values.

***Arguments:***

- **resistance** (`float`): resistance to which the variable is set.

___

### `get_ticket_dict(name, path_to_folder[optional] = None)`

Get ticket as a `dict` object by its name.

***Arguments:***

- **name** (`str`): Ticket name.
- **path_to_folder** (`str | None`, optional): Path to the folder containing the ticket. If this argument is `None`, the standard ticket folder is used (`MemriBoard/tickets`). Defaults to None.

***Returns:***

- **ticket** (`dict`): ticket as a `dict` object.

An example of using this function is available in the [example with a cycle](#example-with-a-cycle-example_for_cycle).

___

### 2. Functions that send tickets

This group of functions send tickets to the measurement board during the algorithm execution. They do not return a value to the user. During the algorithm compilation, they are transformed to generators, so **they should not be used in assign constructions: statements like `x = send_ticket()` or `[send_ticket() for _ in range(5)]` are forbidden. All functions of this type should be written on a separate line of code, for example:

```python
for _ in range(5):
    send_ticket('iv-curve')
```

___

### `send_ticket(name, path_to_folder[optional] = None)`

Send a ticket by its name. You shouldn't use this function for sending an experiment (ticket sequence), use `send_experiment()` for that. This function doesn't return any values.

***Arguments:***

- **name** (`str`): Ticket name.
- **path_to_folder** (`str | None`, optional): Path to the folder containing the ticket. If this argument is `None`, the standard ticket folder is used (`MemriBoard/tickets`). Defaults to None.

___

### `send_ticket_dict(ticket)`

Send a ticket as a `dict` object. This function together with the `get_ticket_dict()` can be used for modifying experiment parameters during its execution. You shouldn't use this function for sending an experiment (ticket sequence), use `send_experiment()` for that. This function doesn't return any values.

***Arguments:***

- **ticket** (`dict`): ticket as a `dict` object.

An example of using this function is available in the [example with a cycle](#example-with-a-cycle-example_for_cycle).

___

### `send_experiment(name, path_to_folder[optional] = None)`

Send an experiment (ticket sequence) by its name. You shouldn't use this function for sending a single ticket, use `send_ticket()` for that. This function doesn't return any values.

***Arguments:***

- **name** (`str`): Experiment name.
- **path_to_folder** (`str | None`, optional): Path to the folder containing the experiment. If this argument is `None`, the standard ticket folder is used (`MemriBoard/tickets`). Defaults to None.

An example of using this function is available in the [example with a branch](#example-with-a-branch-example_if).
___

### `send_experiment_dict(experiment)`

Send an experiment (ticket sequence) as a `dict` object. This function together with the `get_ticket_dict()` can be used for modifying experiment parameters during its execution. You shouldn't use this function for sending a single ticket, use `send_ticket()` for that. This function doesn't return any values.

***Arguments:***

- **experiment** (`dict`): experiment as a `dict` object.

___

### `measure_resistance()`

Measure the memristor resistance. This function sends a ticket used in the app for resistance measurement (it is specified in `settings.ini/gui/measure_ticket`). This function doesn't return any values.

An example of using this function is available in the [example with a branch](#example-with-a-branch-example_if).

___

## Examples of the algorithms

The following two examples are available by default on the [experiment configuration window](README.md#configuring-your-experiment).

### Example with a branch (example_if)

An example of a branching algorithm: it uses `if` statement for sending different tickets depending on last resistance measured.

Algorithm uses experiments as .json files, you need to export them
to some folder via 'Ticket export' button and specify this folder in
'send_experiment' function via 'folder_path' argument. If the experiments
are in the standard 'tickets' folder, the argument may be omitted.

```python
def algorithm():
    # Measuring the resistance
    measure_resistance()
    # Doing an experiment based on measured resistance
    if last_resistance() > 10000:
        # Sending SET experiment
        send_experiment('Experiment_SET')  # Voltage sweep from 0 to -2 V
    else:
        # Sending RESET experiment
        send_experiment('Experiment_RESET')  # Voltage sweep from 0 to +2 V
```

___

### Example with a cycle (example_for_cycle)

An example of the algorithm with `for` cycle and ticket parameter changing.

The algorithm implements double sweep: primary sweep is done in the `iv_curve` ticket, secondary sweep is done via `for` cycle. Secondary voltage sweep is from 1 to 2.5 volts, 5 points.

```python
import numpy as np  # Importing numpy

# Helper function that changes voltage in the ticket
def change_ticket_voltage(ticket, voltage):
    ticket['params']['stop_dir'] = voltage
    ticket['params']['stop_rev'] = voltage
    return ticket


# Main algorithm function
def algorithm():
    # Creating secondary voltage array
    v_array = np.linspace(1, 2.5, 5, dtype=float)
    # Getting ticket as a dict for editing it
    base_ticket = get_ticket_dict('iv-curve')
    # Creating for cycle
    for voltage in v_array:
        # Editing ticket
        ticket = change_ticket_voltage(base_ticket, voltage)
        # Executing ticket
        send_ticket_dict(ticket)
```
