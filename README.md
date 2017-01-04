# zombiesim
A simulator for watching humans run away from zombies

In order to run the files in the zombie simulator, Random, Math, and Pygame must all be imported. In addition to this, the code provided has been written for Python 3.0 and higher.

To create a simulation, open a python interpreter and run the command:
> from zombiesim_gui import *

This will also import all necessary code from zombiesim.py
After importing the gui file, the user can create a simulation with the following command:
> grid = Grid(x, y, h, z)
Where x is the width of the simulation, y is the height, h is the number of humans, and z is the number of zombies