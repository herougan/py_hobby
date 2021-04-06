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

# ===================================
# Primary Settings
# ===================================

# Verbosity
graph = True  # Unused
gif = True  # Unused
# Timestep
duration = 0.1  # Length of each frame in .gif (s)
dt = 120 / 60 / 60  # Length of each time step (h)
max_ts = 2500  # Number of steps
# .gif
to_plot = True  # Plotting enabled or disabled, .gif creation
ts_per_frame = 1  # Number of frames per plot image
# Others
name = "bus_plot"  # File name
folder_name = "img/"  # Folder name
order = 1  # #order avg

# ---------------------------
# Comments
# ---------------------------

# Only two type of stops, express and normal. Need to change to ALL, 1, 2, 3...
# No acceleration included!
# The stops should be of random type
# Graph all everything! (3d plot)
# Gif out everything! (3d plot animate)
# Heavy traffic simulation
# Use adjacency graph to easily create complicated streets
# Different bus properties for each type
## Metrics
# Travel time PER between-stops, Wait time PER stop, How long it is close to another bus?
# Bus clumping
## Colouring
# Generalise number of types and number of colours: _c = bus_colours[bus_datum['type']], type_name = type_str['type']
## Passenger AI
# Passengers might want to skip normal buses for express buses
# Passengers may be able to predict distance and make their decisions

# ---------------------------
# Questions
# ---------------------------

# What kind of statistics can we gleam
# What kind of timeseries do we want to generate
# What kind of plots do we want to generate


# ---------------------------
# Bugs
# ---------------------------

# -

# ===================================
# Constants
# ===================================

# All units are in h and km
n_bus = 2
n_stop = 4
# Movement Constants
v_0 = 50
v_max = 50
# UNUSED --------
a_0 = 5  # Default Acceleration, stopping is instantaneous
da_0 = 6  # Default Decelerration
t_a = 10  # Acceleration Time
# UNUSED --------
# Passenger Constants
p_board_t = 10 / 60 / 60  # Time for passenger to board
p_alight_t = 10 / 60 / 60  # Time for passenger to alight
stop_t = 30 / 60 / 60  # Time required to stop and move off
p_t = 100 / 60 / 60  # Passenger interval
stop_distance = 0.5
loop_distance = 10
# Temp constants
_p_t = 0
# Loop variables


# Future work
n_stop_type = 2
type_str = ["norm", "exp"]
stop_type = range(n_stop_type)

# ===================================
# Variable processing
# ===================================

# .gif
t_frames = int(math.ceil(max_ts / ts_per_frame))
# Others
name = folder_name + str(max_ts) + "s_" + str(ts_per_frame) + "fps_" + str(int(dt * 60 * 60)) + "sec_" + name

# ===================================
# Plot data
# ===================================

bus_data = []
for i in range(n_bus):
    bus_data.append({
        's': [],
        'n_p': [],  # Number of passengers
        'd': [],  # Total distance travelled
        't': "",  # Type
    })
stop_data = []
for i in range(n_stop):
    stop_data.append({
        's': [],
        'n_p': [],  # Number of passengers
        't': "",  # Type
    })
stat_data = {
    'n_p': [],  # Number of passengers
    'c': [],  # Clumping coefficient
    'd': [],  # Total distance travelled
    't_wait': [],  # Avg time for pas. waiting for bus
    't_travel': [],  # Avg time for pas. waiting while in this bus
}
passenger_data = {
    'w_t': [],  # Waiting for bus
    'd_t': [],  # Waiting while in the bus
    't': "",
}
p_list = []

# ===================================
# Setup
# ===================================


# ---------------------------
# Buses
# ---------------------------


buses = []
_type_flip = 0
for i in range(n_bus):
    if _type_flip:
        buses.append(Bus('exp', v_0, loop_distance / n_bus * i))
        bus_data[i]['t'] = 'exp'
    else:
        buses.append(Bus('norm', v_0, loop_distance / n_bus * i))
        bus_data[i]['t'] = 'norm'
    _type_flip = not _type_flip

# ---------------------------
# Bus Stops
# ---------------------------

stops = []
for i in range(n_stop):
    if _type_flip:
        # For now, they are equally spread out
        stops.append(Stop('exp', loop_distance / n_stop * i))
        stop_data[i]['t'] = 'exp'
    else:
        stops.append(Stop('norm', loop_distance / n_stop * i))
        stop_data[i]['t'] = 'norm'
    _type_flip = not _type_flip

# Error Safety
if n_stop < 3 or p_t < 0 and n_stop_type <= type_str:
    print("These settings will not do!")
    exit

# ===================================
# Begin loop
# ===================================

for i in range(max_ts):

    # ---------------------------
    # Passengers
    # ---------------------------

    # Add Passengers
    _p_t += dt
    if _p_t > p_t:
        _n = math.floor(_p_t / p_t)
        _p_t -= p_t * _n
        # Spawn passenger
        p_list.append(create_passenger(stops, p_board_t, p_alight_t))

    # ---------------------------
    # Operate Bus
    # ---------------------------

    # Check bus status
    for j, bus in enumerate(buses):

        # Get next stop
        delta_t = dt
        next = get_closest(bus, stops, loop_distance)

        # ========================================
        #               Bus States
        # ----------------------------------------
        #
        #        [[Time Steps = delta_t]]
        #
        #   <Moving>:
        #       Check if will stop => <Stopping>
        #                         /=> con't <Moving>
        #   <Stopping?:
        #       Check if within stopping distance => <Stop>
        #                                        /=> con't <Stopping>
        #
        #            [While Stopped]
        #
        #       Loop: If something to do:
        #           <Board> =>
        #               Wait to board
        #           <Alight> =>
        #               Wait to alight
        #           If there is no more time, return.
        #
        #       If there is nothing left to do:
        #           Leave => <Moving>
        #
        #                 [End]
        #
        #   <Moving> or <Stopping>:
        #      Bus Moves
        #
        # *Something to do: To board or alight passengers
        # ========================================

        # Check if bus is stopping at next stop
        _is_stop = bus.is_stop
        if _is_stop == 0:
            # Check if express or not
            if bus.type == "norm" or bus.type == next.type:
                # Check if need for alighting or boarding
                if any(p for p in bus.p if p.is_next_stop(next)) or \
                        any(p for p in next.p if p.is_next_bus(bus)):
                    _is_stop = 2
                # Check if passenger needs to stop
                if bus.to_stop(next):
                    _is_stop = 2
        # If bus is stopping, and also in range
        if _is_stop == 2 and (bus.v * delta_t) >= true_dist(bus, next, loop_distance):
            delta_t -= bus.stop(true_dist(bus, next, loop_distance), stop_t)
            _is_stop = 1

        # If bus is stopped
        if _is_stop == 1:
            if bus.stop_time:
                delta_t = t_deduct(bus, delta_t)
            # If there is spare time, and there are passengers to alight or disembark
            while delta_t and \
                    (any(p for p in bus.p if p.is_next_stop(next)) or \
                     any(p for p in next.p if p.is_next_bus(bus))):
                alight_or_board(bus, next)
                delta_t = t_deduct(bus, delta_t)

        # If bus is ready to move off
        if not bus.stop_time and _is_stop == 1 and not \
                (any(p for p in bus.p if p.is_next_stop(next)) or \
                 any(p for p in next.p if p.is_next_bus(bus))):
            _is_stop = 0

        # If bus is moving
        if not _is_stop == 1:
            # Move bus
            delta_t = bus.move(delta_t)

        # Check if looped
        bus.s -= loop_distance * math.floor(bus.s / loop_distance)
        bus.is_stop = _is_stop

        # ---------------------------
        # Retrieve stats
        # ---------------------------

        # Retrieve Bus stats
        bus_data[j]['s'].append(bus.s)
        bus_data[j]['n_p'].append(len(bus.p))

    # Retrieve Stop stats (Outside bus loop)
    for k in range(n_stop):
        stop_data[k]['s'].append(stops[k].s)  # Stops can't move, but it's more organised this way, I think.
        stop_data[k]['n_p'].append(len(stops[k].p))

    stat_data['n_p'].append(len(p_list))
    stat_data['c'].append(str(calculate_clumping(buses, order)))
    # ---------------------------
    # Save Image
    # ---------------------------

    if not i % ts_per_frame and to_plot:
        bus_plot(name, bus_data, stop_data, stat_data, int(i / ts_per_frame), t_frames, i * dt, loop_distance)

if to_plot:
    clean_plot()
    plot_gif(name, duration)

# ===================================
# Credits
# ===================================
# Alice Ngiam
# 2021 5 Apr
