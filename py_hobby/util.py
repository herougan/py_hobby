import math
import random


import matplotlib.pyplot as plt
import imageio as io
import os


# ===================================
# Classes
# ===================================

class Bus:

    def __init__(self, type, velocity, position):
        self.type = type
        self.v = velocity
        self.s = position
        self.is_stop = 0
        self.stop_time = 0
        self.p = []

    def __str__(self):
        if self.is_stop == 0:
            _str = "{t} Bus: Now at {s} km, with passengers {p}".format(t=self.type, s=self.s, p=self.p)
        elif self.is_stop == 1:
            _str = "{t} Bus: Stopped at {s} km, with passengers {p}".format(t=self.type, s=self.s, p=self.p)
        else:
            _str = "{t} Bus: Stopping, at {s} km, with passengers {p}".format(t=self.type, s=self.s, p=self.p)
        return _str

    def to_stop(self, stop):
        return any(_p.f_stop == stop for _p in self.p)
        # return not type or type == stop.type

    def remove_p(self, _p):
        self.p = [__p for __p in self.p if not __p == _p]
        self.stop_time += _p.t_a
        return self.p

    def add_p(self, _p):
        self.p.append(_p)
        self.stop_time += _p.t_b
        return self.p

    def add_stop_time(self, t):
        self.stop_time += t
        return self.stop_time

    def set_stop_time(self, t):
        self.stop_time = t

    def move(self, t):
        self.s += self.v * t
        return 0

    def stop(self, d, to_stop_time):
        self.move(d / self.v)
        self.add_stop_time(to_stop_time)
        return d / self.v


class Passenger:

    def __init__(self, c, f, b, a):
        self.c_stop = c
        self.f_stop = f
        self.t_a = a
        self.t_b = b
        self.type = f.type

    def __str__(self):
        return "Passenger: From {c} km to {f} km".format(c=self.c_stop.s, f=self.f_stop.s)

    def is_next_stop(self, stop):
        return self.f_stop == stop

    def is_pick_stop(self, stop):
        return self.c_stop == stop

    def is_next_bus(self, bus):
        return self.type == bus.type or bus.type == "norm"


class Stop:

    def __init__(self, type, s):
        self.type = type
        self.s = s
        self.p = []

    def __str__(self):
        return f'{self.type} Stop at #{self.s} km: contains {self.p} passengers'

    def remove_p(self, _p):
        self.p = [__p for __p in self.p if not __p == _p]
        return self.p

    def add_p(self, _p):
        self.p.append(_p)
        return self.p


# ===================================
# Functions
# ===================================

def solve_acc(dist, velocity):
    """Requires: Acceleration Time t_a
    BROKEN"""
    acc = 0
    a = 1
    t_a = 1
    dist = velocity * t_a + 0.5 * a * t_a ** 2
    # sol1 = (-b-cmath.sqrt(d))/(2*a)
    # sol2 = (-b+cmath.sqrt(d))/(2*a)
    return acc


def create_passenger(stops, b_t, a_t):
    """Passenger Creator: passenger"""
    n_stop = len(stops)
    # Get random location and destination
    _c = random.randint(0, n_stop - 1)
    _f = random.randint(0, n_stop - 1)
    while _f == _c:
        _f = random.randint(0, n_stop - 1)
    # Make passenger
    _p = Passenger(stops[_c], stops[_f], b_t, a_t)
    # Add to stop
    stops[_c].add_p(_p)
    return _p


def t_deduct(_bus, _dt):
    """Deducts delta time from stop time"""
    if _dt > _bus.stop_time:
        _dt -= _bus.stop_time
        _bus.set_stop_time(0)
    else:
        _bus.add_stop_time(-_dt)
        _dt = 0
    return _dt


def true_dist(bus, stop, loop):
    """Returns forward distance between bus and stop"""
    if stop.s >= bus.s:
        return stop.s - bus.s
    else:
        return loop - (bus.s - stop.s)


def get_closest(bus, stops, loop):
    """Get next forward-closest stop"""
    _c_d = math.inf
    next = None
    for stop in stops:
        # __ prefix should be reserved
        ___c_d = true_dist(bus, stop, loop)
        if ___c_d < _c_d:
            _c_d = ___c_d
            next = stop
    return next


def alight_or_board(bus, stop):
    """Alight first or board once only"""

    # Alight passengers first
    for _p in bus.p:
        if _p.is_next_stop(stop):
            bus.remove_p(_p)
            return len(bus.p)

    # Board passengers
    for _p in stop.p:
        if _p.is_next_bus(bus):
            bus.add_p(_p)
            stop.remove_p(_p)
            return len(bus.p)


def calculate_clumping(buses, order):
    """Calculate %order average of the inter-distance between buses"""
    avg = 0
    if not len(buses) or not buses:
        return 0
    for bus1 in buses:
        _avg = 0
        for bus2 in buses:
            _avg += abs(bus2.s - bus1.s) ** order
        avg += _avg / (len(buses)-1) ** order
    return avg / (len(buses)-1)


# ===================================
# Plotting
# ===================================


def bus_plot(name, bus_data, stop_data, stat_data, step, total_steps, time, loop):
    """Create geographic plot of buses"""
    # Prepare plot
    fig, ax = plt.subplots()
    plt.title('Bus displacement/time')

    r = loop / (2 * math.pi)
    plt.xlim([0, 3 * r])
    plt.ylim([0, 3 * r])

    # Setup Map
    circle = plt.Circle((1.5 * r, 1.5 * r), r, fill=False)

    ax.set_aspect(1)
    ax.add_artist(circle)

    colour_list = list(set([bus_datum['t'] for bus_datum in bus_data]))
    colours = get_colour_array(len(colour_list))

    c_ratio = 15

    # Draw passenger labels (Buses)
    for i, bus_datum in enumerate(bus_data):
        _a = bus_datum['s'][step] / loop * 2 * math.pi
        _col = colours[colour_list.index(bus_datum['t'])]
        _c = plt.Circle((r * (1.5 + math.cos(_a)), r * (1.5 + math.sin(_a))), r / c_ratio, fill=False, color=_col)
        plt.text(r * (1.5 + 0.75 * math.cos(_a)), r * (1.5 + 0.75 * math.sin(_a)), str(bus_datum['n_p'][step]))
        ax.add_artist(_c)

    # Draw passenger labels (Stops)
    for stop_datum in stop_data:
        _col = colours[colour_list.index(stop_datum['t'])]
        _a = stop_datum['s'][step] / loop * 2 * math.pi
        _c = plt.Circle((r * (1.5 + math.cos(_a)), r * (1.5 + math.sin(_a))), r / c_ratio, fill=False, color=_col)
        plt.text(r * (1.5 + 1.25 * math.cos(_a)), r * (1.5 + 1.25 * math.sin(_a)), str(stop_datum['s'][step]) + "km: " + str(stop_datum['n_p'][step]))
        ax.add_artist(_c)

    # Time, Clumping and n(Passengers) labels
    plt.text(5, 5, str(time)[:5] + " h")
    plt.text(3 * r - 6, 3 * r - 5, str(stat_data['n_p'][step]) + " n(p)")
    plt.text(5, 3 * r - 5, "c=" + str(stat_data['c'][step])[:5])
    for i, t in enumerate(colour_list):
        plt.text(r-5+i, r-5-1, t)
        _col = colours[i]
        _c = plt.Circle((r-5+i, r-5-1), r / c_ratio / 2, fill=True, color=_col)

    # Create file name
    step_digit = "0" * (len(str(total_steps)) - len(str(step)))
    step_digit += str(step)
    file_name = name + f'{step_digit}'

    # Save image
    plt.savefig(file_name)


def clean_plot():
    """Clean all evidence of plotting"""
    plt.close('all')


def plot_gif(name, duration):
    """To be particularly used for bus_plot images but can be used generally. Joins images with similar names into a
    .gif. """
    # https://stackoverflow.com/questions/41228209/making-gif-from-images-using-imageio-in-python

    # Remove .gif if it exists
    gif_name = name + ".gif"
    if os.path.isfile(gif_name):
        os.remove(gif_name)

    # Get .png names
    file_names = sorted((os.path.dirname(name) + "/" + fn for fn in os.listdir(os.path.dirname(name)) if
                         fn.startswith(os.path.basename(name))))

    # Create .gif
    with io.get_writer(gif_name, mode='I', duration=duration) as writer:
        for file_name in file_names:
            # Read
            image = io.imread(file_name)
            # Delete
            os.remove(file_name)
            # Write
            writer.append_data(image)
    writer.close()


def get_colour_array(n):
    """Get an array of colours between Red and Green split into n colours"""
    colours = []
    for i in range(n):
        r = int(255 * i / (n - 1))
        g = int(255 * (1 - i / (n - 1)))
        b = 0
        colours.append('#%02x%02x%02x' % (r, g, b))
    return colours
