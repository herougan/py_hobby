import random
import math
# External
import matplotlib
import matplotlib.pyplot as plt
import imageio
import numpy as np
# Local
from util import Bus, Passenger, Stop
from util import solve_acc, create_passenger, t_deduct, true_dist, get_closest, bus_plot, clean_plot, plot_gif, \
    alight_or_board, calculate_clumping

loop_distance = 10
v_0 = 50

buses = []
n_bus = 3
_type_flip = 0
for i in range(n_bus):
    if _type_flip:
        buses.append(Bus('exp', v_0, loop_distance / n_bus * i))
    else:
        buses.append(Bus('norm', v_0, loop_distance / n_bus * i))
    _type_flip = not _type_flip
stops = []
n_stop = 10
for i in range(n_stop):
    if _type_flip:
        # For now, they are equally spread out
        stops.append(Stop('exp', loop_distance / n_stop * i))
    else:
        stops.append(Stop('norm', loop_distance / n_stop * i))
    _type_flip = not _type_flip

passengers = []
n_passenger = 10
for i in range(n_passenger):
    __c_stop = random.randint(0, n_stop - 1)
    __f_stop = random.randint(0, n_stop - 1)
    while __f_stop == __c_stop:
        __f_stop = random.randint(0, n_stop - 1)
    # Spawn passenger
    __p = Passenger(stops[__c_stop], stops[__f_stop], 0, 0)  # todo make passenger
    stops[__c_stop].add_p(__p)  # Combine into 1 statement
    passengers.append(__p)

passengers_gone = []
for pas in passengers:
    for stop in stops:
        for bus in buses:
            if pas.is_next_stop(stop) or pas.is_next_bus(bus):
                pass

