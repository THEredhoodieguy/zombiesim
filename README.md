# zombiesim
A simulator for watching humans run away from zombies

In order to run the files in the zombie simulator, Random, Math, and Pygame must all be imported. In addition to this, the code provided has been written for Python 3.0 and higher.

# Running the simulator

Pipenv has been added as a dependency manager for the project, you can install it with pip for python3

> pip3 install pipenv

Once pip env has been installed, navigate to the repository and start up the shell

> pipenv shell

Then you can run the gui file to start the simulator, this will start the simulator in a 100x100 box with 500 humans and 3 zombies

> python3 zombiesim_gui

Alternatively, you can run the simulator with custom variables by importing the zombiesim_gui file to a live python3 session

> grid = Grid(x, y, h, z)

x and y will specify the size of the grid, h will specify the number of humans, and z will specify the number of zombies
