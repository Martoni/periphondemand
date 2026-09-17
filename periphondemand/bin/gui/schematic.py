#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Schematic.py
# Purpose:  Build a block diagram model (snapshot) of a POD project so the
#           graphical viewer can render it like an electronic schematic.
#
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
#
# Licence:  GPLv3 or newer
# ----------------------------------------------------------------------------
""" Build a schematic snapshot of a POD project for the graphical viewer.

The snapshot contains everything needed to draw the block diagram without
touching the live POD objects again: each instance is a block, its interfaces
and connected pins become rows, and the connections become edges (pin wires
and bus wires). A simple layered layout (longest path + barycenter ordering)
positions the blocks, and an orthogonal grid router draws the wires that avoid
running through the blocks.
"""

import math
from collections import defaultdict

from periphondemand.bin.core.platform import Platform
from periphondemand.bin.utils.poderror import PodError

# ---------------------------------------------------------------------------
# drawing metrics (pixels, used by the Tk viewer)
# ---------------------------------------------------------------------------
FONT_SIZE = 9
CHAR_W = 0.62
ROW_H = 15          # height of one port / pin row
HEADER_H = 20       # height of the block title bar
BAND_H = 14         # height of an interface header bar
MARGIN = 8          # inner margin of a block
PIN_STUB = 10       # wire stub length outside a block
COL_GAP = 55        # horizontal gap between two columns (levels)
ROW_GAP = 26        # vertical gap between two blocks on the same level
BAND_GAP = 2        # gap between two interface bands
CELL = 12           # routing grid cell size (pixels)
BUS_STUB = 30       # distance between a bus trunk and the slave interface
BUS_WIDTH = 3       # width of a bus stub / master link
BUS_SPINE_WIDTH = 9 # width of the thick bus trunk line
BEND_COST = 6       # extra cost of a direction change in the detour router
DETOUR_LIMIT = 6000     # max expansions of a single detour search
DETOUR_TOTAL = 120000   # max expansions shared by all detours of one route

# routing grid, set once per _route() call (routing is synchronous)
_GRID = {}

DIR_IN = "in"


def _text_width(text, font_size=FONT_SIZE):
    """ Estimate the pixel width of a monospace text. """
    return int(round(len(text) * CHAR_W * font_size))


def pin_side(direction):
    """ Inputs and inouts are drawn on the left, outputs on the right. """
    if direction in (DIR_IN, "inout"):
        return DIR_IN     # left
    return "out"          # right


# ---------------------------------------------------------------------------
# plain data classes (no live project references)
# ---------------------------------------------------------------------------
class Row(object):
    """ One row of a block: a port (collapsed) or a single connected pin. """
    def __init__(self, key, label, direction):
        self.key = key            # (instance, interface, port, num or None)
        self.label = label
        self.direction = direction
        self.side = pin_side(direction)
        self.x = 0
        self.y = 0


class Port(object):
    """ A port of an interface, holding its rendered rows. """
    def __init__(self, name, size, direction, collapsed=True):
        self.name = name
        self.size = size
        self.direction = direction
        self.collapsed = collapsed
        self.rows = []            # list of Row


class Interface(object):
    """ An interface of an instance, rendered as a band with rows. """
    def __init__(self, name, interface_class, bus_name):
        self.name = name
        self.interface_class = interface_class
        self.bus_name = bus_name
        self.ports = []           # list of Port
        self.rows = []            # flat list of Row
        self.leftrows = []
        self.rightrows = []
        self.x = self.y = self.w = self.h = 0


class Instance(object):
    """ An instance of a component, rendered as a block. """
    def __init__(self, instancename, component, is_platform):
        self.instancename = instancename
        self.component = component
        self.is_platform = is_platform
        self.interfaces = []      # list of Interface
        self.level = 0
        self.order = 0
        self.x = 0
        self.y = 0
        self.rect_x = 0
        self.w = 0
        self.h = 0
        self.right_room = 0

    @property
    def center_y(self):
        return self.y + self.h / 2


class Edge(object):
    """ A wire between two anchors. """
    def __init__(self, kind, k1, k2, bus_name=None):
        self.kind = kind          # 'pin' or 'bus'
        self.key = None
        self.k1 = k1
        self.k2 = k2
        self.bus_name = bus_name
        self.width = None          # explicit line width, or None = default
        self.points = []          # list of (x, y)
        self.label = (0, 0)       # position of the bus label, or None


class Snapshot(object):
    """ Complete drawing model of a project. """
    def __init__(self):
        self.title = ""
        self.instances = []       # list of Instance
        self.edges = []           # list of Edge
        self.pin_rows = {}        # row key -> Row
        self.bus_anchors = {}     # (instance, interface) -> (x, y, side)
        self.w = 0
        self.h = 0
        self._pin_pairs = set()

    @property
    def pin_edges(self):
        return [e for e in self.edges if e.kind == "pin"]

    @property
    def bus_edges(self):
        return [e for e in self.edges if e.kind == "bus"]


def _port_label(port, num=None):
    """ Label of a row: port name or port[n] for a connected pin. """
    if num is None:
        try:
            size = int(port.size)
        except (TypeError, ValueError):
            size = 1
        if size > 1:
            return str(port.name) + "[%d]" % size
        return str(port.name)
    if str(port.size) == "1":
        return str(port.name)
    return "%s[%s]" % (port.name, num)


# ---------------------------------------------------------------------------
# building the snapshot from a live project
# ---------------------------------------------------------------------------
def build_snapshot(project):
    """ Build a Snapshot from a POD project object. """
    platforms = [comp for comp in project.instances if comp.is_platform()]
    if (not project.instances) or (not platforms):
        raise PodError("Nothing to display: the project has no instance", 1)
    snap = Snapshot()
    snap.title = "POD schematic - " + project.name

    instances_by_name = {}
    for comp in project.instances:
        inst = Instance(comp.instancename, comp.name,
                        comp.is_platform() or
                        isinstance(comp, Platform))
        snap.instances.append(inst)
        instances_by_name[inst.instancename] = inst

    # ---- pass 1 : create interfaces, ports and rows -----------------------
    for comp in project.instances:
        inst = instances_by_name[comp.instancename]
        for iface in comp.interfaces:
            idoc = Interface(iface.name, iface.interface_class,
                             iface.bus_name)
            inst.interfaces.append(idoc)
            unconnected = 0
            for port in iface.ports:
                pdoc = Port(port.name, port.size, port.direction,
                            collapsed=True)
                connected_pins = {}
                for pin in port.pins:
                    if pin.num is not None and pin.connections:
                        connected_pins[pin.num] = pin
                if connected_pins:
                    pdoc.collapsed = False
                    for num in sorted(connected_pins,
                                      key=lambda n: int(n)):
                        key = (inst.instancename, idoc.name,
                               port.name, str(num))
                        row = Row(key, _port_label(port, num),
                                  port.direction)
                        pdoc.rows.append(row)
                        idoc.rows.append(row)
                        snap.pin_rows[key] = row
                else:
                    unconnected += 1
                idoc.ports.append(pdoc)
            if unconnected:
                key = (inst.instancename, idoc.name, None, None)
                label = "%d unconnected port%s" % \
                    (unconnected, "s" if unconnected > 1 else "")
                row = Row(key, label, DIR_IN)
                idoc.rows.append(row)
                snap.pin_rows[key] = row

    # ---- pass 2 : edges ---------------------------------------------------
    for comp in project.instances:
        for iface in comp.interfaces:
            # bus connections : master interface -> slave interface
            if iface.interface_class == "master":
                for slave in iface.slaves:
                    k1 = (comp.instancename, iface.name)
                    k2 = (slave.instancename, slave.interfacename)
                    edge = Edge("bus", k1, k2, bus_name=iface.bus_name)
                    edge.key = (k1[0], k1[1], k2[0], k2[1])
                    snap.edges.append(edge)
            # pin connections
            for port in iface.ports:
                for pin in port.pins:
                    if pin.num is None:
                        continue
                    k1 = (comp.instancename, iface.name,
                          port.name, str(pin.num))
                    for connection in pin.connections:
                        k2 = (connection["instance_dest"],
                              connection["interface_dest"],
                              connection["port_dest"],
                              connection["pin_dest"])
                        if k1 not in snap.pin_rows or \
                                k2 not in snap.pin_rows:
                            continue
                        # keep only one edge per pair
                        pair = frozenset((k1, k2))
                        if pair in snap._pin_pairs:      # noqa: SLF001
                            continue
                        snap._pin_pairs.add(pair)        # noqa: SLF001
                        edge = Edge("pin", list(pair)[0], list(pair)[1])
                        edge.key = tuple(sorted((k1, k2)))
                        snap.edges.append(edge)

    _layout(snap)
    _route(snap)

    snap.w = max((i.rect_x + i.w + i.right_room for i in snap.instances),
                 default=0)
    snap.h = max((i.y + i.h for i in snap.instances), default=0)
    for edge in snap.edges:
        for px, py in edge.points:
            snap.w = max(snap.w, px)
            snap.h = max(snap.h, py)
    snap.w += 20
    snap.h += 20
    return snap


def _directed_edges(snap, instances_by_name):
    """ Return directed edges as (source instance, dest instance). """
    order = {name: idx for idx, name in enumerate(instances_by_name)}
    d_edges = []
    for edge in snap.edges:
        if edge.kind == "bus":
            d_edges.append((edge.k1[0], edge.k2[0]))
            continue
        r1 = snap.pin_rows.get(edge.k1)
        r2 = snap.pin_rows.get(edge.k2)
        if r1 is None or r2 is None:
            continue
        d1, d2 = r1.direction, r2.direction
        inst1, inst2 = r1.key[0], r2.key[0]
        if d1 == "out" and d2 in (DIR_IN, "inout"):
            d_edges.append((inst1, inst2))
        elif d2 == "out" and d1 in (DIR_IN, "inout"):
            d_edges.append((inst2, inst1))
        else:
            if order[inst1] <= order[inst2]:
                d_edges.append((inst1, inst2))
            else:
                d_edges.append((inst2, inst1))
    return d_edges


def _layout(snap):
    """ Compute block levels (columns), ordering and geometry. """
    instances_by_name = {i.instancename: i for i in snap.instances}
    d_edges = _directed_edges(snap, instances_by_name)

    levels = dict((name, 0) for name in instances_by_name)
    platforms = set(name for name, i in instances_by_name.items()
                    if i.is_platform)

    # longest path layering (platform stays on level 0)
    maxiter = len(instances_by_name) + 2
    for _ in range(maxiter):
        changed = False
        for source, dest in d_edges:
            if dest in platforms:
                continue
            if levels[source] + 1 > levels[dest]:
                levels[dest] = levels[source] + 1
                changed = True
        if not changed:
            break

    for inst in snap.instances:
        inst.level = levels[inst.instancename]

    max_level = max(levels.values())

    # barycenter ordering inside each level
    for _ in range(4):
        groups = dict((lvl, []) for lvl in range(max_level + 1))
        for inst in snap.instances:
            groups[inst.level].append(inst)
        for lvl in range(1, max_level + 1):
            for inst in groups[lvl]:
                up_pos = []
                for u, v in d_edges:
                    if v == inst.instancename and levels[u] == lvl - 1:
                        group = groups[levels[u]]
                        pos = [i for i, node in enumerate(group)
                               if node.instancename == u]
                        if pos:
                            up_pos.append(pos[0])
                degree = sum(1 for e in d_edges
                             if inst.instancename in e)
                if up_pos:
                    bary = float(sum(up_pos)) / len(up_pos)
                else:
                    bary = -1.0
                inst._bary = bary            # noqa: SLF001
                inst._degree = degree        # noqa: SLF001
            groups[lvl].sort(key=lambda n: (
                n._bary, -n._degree, n.instancename))      # noqa: SLF001
            for idx, inst in enumerate(groups[lvl]):
                inst.order = idx

    # measure blocks
    for inst in snap.instances:
        _measure(inst)

    # place blocks column by column (each column = a level)
    max_widths = {}
    for lvl in range(max_level + 1):
        blocks = [i for i in snap.instances if i.level == lvl]
        max_widths[lvl] = max((i.w + i.right_room for i in blocks),
                              default=0)

    x_cursor = MARGIN
    for lvl in range(max_level + 1):
        blocks = sorted([i for i in snap.instances if i.level == lvl],
                        key=lambda i: i.order)
        col_x = x_cursor
        y_cursor = MARGIN
        for inst in blocks:
            inst.x = col_x
            inst.y = y_cursor
            y_cursor += inst.h + ROW_GAP
        if blocks:
            x_cursor += max_widths[lvl] + COL_GAP

    _fill_geometry(snap)


def _measure(inst):
    """ Compute block size from its content. """
    name_width = _text_width(inst.instancename)
    max_left = 0
    max_right = 0
    content_w = name_width
    height = HEADER_H
    first = True
    for idoc in inst.interfaces:
        if not first:
            height += BAND_GAP
        first = False
        idoc.leftrows = [r for r in idoc.rows if r.side == DIR_IN]
        idoc.rightrows = [r for r in idoc.rows if r.side == "out"]
        header = idoc.name
        if idoc.interface_class:
            header += " [%s]" % idoc.interface_class
        if idoc.bus_name:
            header += " (%s)" % idoc.bus_name
        header_w = _text_width(header)
        content_w = max(content_w, header_w)
        for row in idoc.leftrows:
            max_left = max(max_left, _text_width(row.label) + PIN_STUB)
        for row in idoc.rightrows:
            max_right = max(max_right, _text_width(row.label) + PIN_STUB)
        nrows = max(len(idoc.leftrows), len(idoc.rightrows))
        idoc.h = BAND_H + nrows * ROW_H
        height += idoc.h
    inst.w = content_w + 2 * MARGIN
    inst.h = height + MARGIN
    inst.left_room = max_left
    inst.right_room = max_right


def _fill_geometry(snap):
    """ Compute the precise position of every element in each block. """
    for inst in snap.instances:
        rect_x = inst.x + inst.left_room
        rect_y = inst.y
        inst.rect_x = rect_x
        y_cursor = rect_y + HEADER_H
        for idoc in inst.interfaces:
            idoc.x = rect_x
            idoc.y = y_cursor
            idoc.w = inst.w
            nrows = max(len(idoc.leftrows), len(idoc.rightrows))
            rows_h = nrows * ROW_H
            content_top = y_cursor + BAND_H
            for row in idoc.leftrows:
                row.y = content_top + (idoc.leftrows.index(row) + 0.5) * ROW_H
                row.x = rect_x
            for row in idoc.rightrows:
                row.y = content_top + (idoc.rightrows.index(row) + 0.5) * ROW_H
                row.x = rect_x + inst.w
            idoc.h = BAND_H + rows_h
            if idoc.interface_class == "master":
                snap.bus_anchors[(inst.instancename, idoc.name)] = \
                    (rect_x + inst.w, y_cursor + BAND_H / 2, "out")
            elif idoc.interface_class == "slave":
                snap.bus_anchors[(inst.instancename, idoc.name)] = \
                    (rect_x, y_cursor + BAND_H / 2, DIR_IN)
            y_cursor += idoc.h + BAND_GAP


# ---------------------------------------------------------------------------
# orthogonal routing on a coarse grid (wires avoid the blocks)
# ---------------------------------------------------------------------------
def _route(snap):
    """ Route every edge with a grid based shortest path. """
    # grid extents from the blocks bounding box
    min_x = min((i.rect_x for i in snap.instances), default=0)
    min_y = min((i.y for i in snap.instances), default=0)
    max_x = max((i.rect_x + i.w for i in snap.instances), default=0)
    max_y = max((i.y + i.h for i in snap.instances), default=0)
    pad = 3 * CELL
    min_x -= pad
    min_y -= pad
    max_x += pad
    max_y += pad
    cols = int(math.ceil((max_x - min_x) / CELL)) + 1
    rows = int(math.ceil((max_y - min_y) / CELL)) + 1

    blocked = set()
    pad_cells = 1
    for inst in snap.instances:
        x0 = int(math.floor((inst.rect_x - pad_cells * CELL - min_x) / CELL))
        y0 = int(math.floor((inst.y - pad_cells * CELL - min_y) / CELL))
        x1 = int(math.ceil((inst.rect_x + inst.w + pad_cells * CELL
                            - min_x) / CELL))
        y1 = int(math.ceil((inst.y + inst.h + pad_cells * CELL - min_y)
                           / CELL))
        for cy in range(max(0, y0), min(rows, y1 + 1)):
            for cx in range(max(0, x0), min(cols, x1 + 1)):
                blocked.add((cx, cy))

    # soft grid: cells whose center lies inside a block (no pad), used to
    # accept straight, L-shaped and river segments that only graze a block
    blocked0 = set()
    for inst in snap.instances:
        x0 = int(math.ceil((inst.rect_x - min_x) / CELL - 0.5))
        x1 = int(math.floor((inst.rect_x + inst.w - min_x) / CELL - 0.5))
        y0 = int(math.ceil((inst.y - min_y) / CELL - 0.5))
        y1 = int(math.floor((inst.y + inst.h - min_y) / CELL - 0.5))
        for cy in range(max(0, y0), min(rows, y1 + 1)):
            for cx in range(max(0, x0), min(cols, x1 + 1)):
                blocked0.add((cx, cy))

    # pin edges are routed one by one, bus edges are grouped per master
    # interface and drawn as a single thick trunk with short stubs
    pin_edges = [edge for edge in snap.edges if edge.kind != "bus"]
    bus_edges = [edge for edge in snap.edges if edge.kind == "bus"]

    def pin_anchor(key):
        row = snap.pin_rows[key]
        return row.x, row.y

    # global routing state: grid parameters, taken cells per signal, label
    # clear-zone list, and the shared detour budget
    global _GRID
    _GRID = {"x0": min_x, "y0": min_y, "cols": cols, "rows": rows,
             "cell": CELL, "detour_left": DETOUR_TOTAL}
    taken = {}
    label_boxes = []

    bus_edges_out = []
    bus_groups = defaultdict(list)
    for edge in bus_edges:
        bus_groups[edge.k1].append(edge)
    rects = [(i.rect_x, i.y, i.w, i.h) for i in snap.instances]

    for k1, group in bus_groups.items():
        signal = ("bus", group[0].bus_name, k1)
        xm, ym, _ = snap.bus_anchors[k1]
        anchors = [snap.bus_anchors[edge.k2] for edge in group]
        y_top = min([ym] + [a[1] for a in anchors])
        y_bottom = max([ym] + [a[1] for a in anchors])

        def spine_free(x):
            cx = int(math.floor((x - min_x) / CELL))
            for cy in range(int(math.floor((y_top - min_y) / CELL)),
                            int(math.floor((y_bottom - min_y) / CELL)) + 1):
                if (cx, cy) in blocked:
                    return False
                if taken.get((cx, cy), signal) != signal:
                    return False
            return True

        x_spine = min((a[0] for a in anchors)) - BUS_STUB
        for delta in (0,) + tuple(n * CELL for n in range(1, 4) for _ in
                                  (-1, 1)):
            candidate = x_spine + delta
            if spine_free(candidate):
                x_spine = candidate
                break

        # the thick trunk
        spine = Edge("bus", k1, group[-1].k2,
                     bus_name=group[0].bus_name)
        spine.width = BUS_SPINE_WIDTH
        spine.points = [(x_spine, y_top), (x_spine, y_bottom)]
        _occupy_cells(spine.points, taken, signal)
        bus_edges_out.append(spine)

        # master link, routed around the blocks
        link = Edge("bus", k1, group[-1].k2,
                    bus_name=group[0].bus_name)
        link.width = BUS_WIDTH
        link.label = None
        path = _shortest_path((xm, ym), (x_spine, ym), cols, rows, CELL,
                              min_x, min_y, blocked, blocked0, rects,
                              taken, signal)
        link.points = path if path is not None else [(xm, ym), (x_spine, ym)]
        bus_edges_out.append(link)

        # one routed stub between the trunk and every slave interface
        for edge in group:
            stub = Edge("bus", edge.k1, edge.k2, bus_name=edge.bus_name)
            stub.width = BUS_WIDTH
            stub.label = None
            sx, sy, _ = snap.bus_anchors[edge.k2]
            path = _shortest_path((sx, sy), (x_spine, sy), cols, rows,
                                  CELL, min_x, min_y, blocked, blocked0,
                                  rects, taken, signal)
            stub.points = path if path is not None else [(sx, sy),
                                                         (x_spine, sy)]
            bus_edges_out.append(stub)

        # place the bus name label in a gap free of any wire
        if group[0].bus_name:
            spine.label = _find_label_spot(
                group[0].bus_name, x_spine, y_top, y_bottom,
                taken, signal, label_boxes)

    for edge in pin_edges:
        start = pin_anchor(edge.k1)
        end = pin_anchor(edge.k2)
        signal = ("pin", edge.k1, edge.k2)
        path = _shortest_path(start, end, cols, rows, CELL,
                              min_x, min_y, blocked, blocked0, rects,
                              taken, signal)
        if path is None:
            continue
        edge.points = path

    # buses are drawn first (behind the pin wires)
    snap.edges = bus_edges_out + pin_edges


def _shortest_path(start, end, cols, rows, cell, min_x, min_y, blocked,
                   blocked0=None, rects=(), taken=None, signal=None):
    """ Route a wire with the most rectilinear trajectory available.

    Preferred shapes, in decreasing order:
      1. a single straight line,
      2. an L (one right angle),
      3. a river: two parallels joined by a straight crossing,
      4. a detour (Dijkstra) that penalises direction changes.
    ``blocked`` is the hard grid (blocks grown by one cell); ``blocked0`` is
    the soft grid (block cells only, no padding) used to accept segments that
    only graze a block edge but never cross a block.  ``rects`` lists the
    block boxes: a clean path is rejected when it rides along a block border
    for more than one cell.  ``taken`` maps routed cells to the signal that
    owns them so two different signals never merge on the same run; every
    chosen path is recorded into ``taken``.
    """
    if taken is None:
        taken = {}
    if blocked0 is None:
        blocked0 = blocked

    def free(points):
        return _poly_free(points, cols, rows, cell, min_x, min_y, blocked0,
                          taken, signal) \
            and not _grazes(points, rects, cell)

    if free([start, end]):
        path = [start, end]
    else:
        path = None
        for corner in ((end[0], start[1]), (start[0], end[1])):
            cand = [start, corner, end]
            if free(cand):
                path = cand
                break
        if path is None:
            max_x = min_x + cols * cell
            max_y = min_y + rows * cell
            for cand_y in _ordered_lines(start[1], end[1], min_y, max_y,
                                         cell):
                cand = [start, (start[0], cand_y), (end[0], cand_y), end]
                if free(cand):
                    path = cand
                    break
        if path is None:
            for cand_x in _ordered_lines(start[0], end[0], min_x, max_x,
                                         cell):
                cand = [start, (cand_x, start[1]), (cand_x, end[1]), end]
                if free(cand):
                    path = cand
                    break
        if path is None:
            path = _detour(start, end, cols, rows, cell, min_x, min_y,
                           blocked, taken, signal)
    if path is None:
        # the detour budget was exhausted (very cluttered schematic): fall
        # back to any block-free candidate, even one that rides along a
        # block border, and finally to a plain straight line
        path = [start, end]
        for corner in ((end[0], start[1]), (start[0], end[1])):
            cand = [start, corner, end]
            if _poly_free(cand, cols, rows, cell, min_x, min_y, blocked0,
                          taken, signal):
                path = cand
                break
        if len(path) == 2:
            max_x = min_x + cols * cell
            max_y = min_y + rows * cell
            for cand_y in _ordered_lines(start[1], end[1], min_y, max_y,
                                         cell):
                cand = [start, (start[0], cand_y), (end[0], cand_y), end]
                if _poly_free(cand, cols, rows, cell, min_x, min_y,
                              blocked0, taken, signal):
                    path = cand
                    break
            else:
                for cand_x in _ordered_lines(start[0], end[0], min_x,
                                             max_x, cell):
                    cand = [start, (cand_x, start[1]), (cand_x, end[1]), end]
                    if _poly_free(cand, cols, rows, cell, min_x, min_y,
                                  blocked0, taken, signal):
                        path = cand
                        break

    _occupy_cells(path, taken, signal)
    return path


def _grazes(points, rects, cell):
    """ True if a segment rides along a block border for more than a cell. """
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        for rx, ry, rw, rh in rects:
            if x0 == x1 and (x0 == rx or x0 == rx + rw):
                overlap = min(max(y0, y1), ry + rh) - max(min(y0, y1), ry)
                if overlap > cell:
                    return True
            elif y0 == y1 and (y0 == ry or y0 == ry + rh):
                overlap = min(max(x0, x1), rx + rw) - max(min(x0, x1), rx)
                if overlap > cell:
                    return True
    return False


def _ordered_lines(lo, hi, min_v, max_v, cell):
    """ Candidate lines (pixel abcisses) for a river, closest to the corridor first.

    Returns at most ``RIVER_CANDIDATES`` values (plus the two corridor
    edges) to avoid scanning hundreds of positions on a large grid.
    """
    lo, hi = sorted((lo, hi))
    mid = (lo + hi) / 2.0
    out = []
    seen = set()

    def add(value):
        if min_v <= value <= max_v and value not in seen:
            seen.add(value)
            out.append(value)

    add(lo)
    add(hi)
    k0 = int(math.floor((lo - min_v) / cell))
    k1 = int(math.floor((hi - min_v) / cell))
    lines = [min_v + (k + 0.5) * cell for k in range(k0, k1 + 1)]
    lines.sort(key=lambda v: (abs(v - mid), v))
    for line in lines:
        if len(out) >= 14:
            break
        add(line)
    for k in range(1, 4):
        add(lo - k * cell)
        add(hi + k * cell)
    return out


def _occupy_cells(points, taken, signal):
    """ Record the cells a polyline runs through, owned by ``signal``. """
    if taken is None:
        return
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if x0 == x1:
            cx = _cell_x(x0)
            cy0 = _cell_y(y0)
            cy1 = _cell_y(y1)
            for cy in range(min(cy0, cy1), max(cy0, cy1) + 1):
                taken.setdefault((cx, cy), signal)
        elif y0 == y1:
            cy = _cell_y(y0)
            cx0 = _cell_x(x0)
            cx1 = _cell_x(x1)
            for cx in range(min(cx0, cx1), max(cx0, cx1) + 1):
                taken.setdefault((cx, cy), signal)


def _cell_x(value):
    """ Grid column of a pixel x (clamped to the grid). """
    grid = _GRID
    index = int(math.floor((value - grid["x0"]) / grid["cell"]))
    return max(0, min(grid["cols"] - 1, index))


def _cell_y(value):
    """ Grid row of a pixel y (clamped to the grid). """
    grid = _GRID
    index = int(math.floor((value - grid["y0"]) / grid["cell"]))
    return max(0, min(grid["rows"] - 1, index))


def _find_label_spot(text, x, y_top, y_bottom, taken, signal, label_boxes):
    """ Seek a corner of empty space for a wire label (clear of every wire). """
    width = _text_width(text) + 8

    def box(cx, cy):
        return (cx - width / 2, cy - 7, cx + width / 2, cy + 7)

    def clear(b):
        if _box_hits_taken(b, taken):
            return False
        for other in label_boxes:
            if _box_overlap(b, other):
                return False
        return True

    mid = (y_top + y_bottom) / 2.0
    for dx in (14, 26, 40, 58, 80):
        for dy in (0, -10, 10, -20, 20, -30, 30, -42, 42):
            spot = (x + dx, mid + dy)
            if clear(box(*spot)):
                label_boxes.append(box(*spot))
                return spot
    return (x + 14, mid)


def _box_overlap(a, b):
    """ True if two axis-aligned boxes overlap. """
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _box_hits_taken(box, taken):
    """ True if a label box touches a wire cell owned by any signal. """
    if not taken:
        return False
    margin = 3
    grid = _GRID
    for (cx, cy) in taken:
        cx0 = grid["x0"] + cx * grid["cell"] - margin
        cx1 = grid["x0"] + (cx + 1) * grid["cell"] + margin
        cy0 = grid["y0"] + cy * grid["cell"] - margin
        cy1 = grid["y0"] + (cy + 1) * grid["cell"] + margin
        if _box_overlap(box, (cx0, cy0, cx1, cy1)):
            return True
    return False


def _segment_free(p0, p1, cols, rows, cell, min_x, min_y, blocked0,
                  exempt=(), taken=None, signal=None):
    """ True if an axis-aligned segment crosses no soft-blocked cell.

    ``exempt`` lists cells that are allowed to be soft-blocked (the pin
    anchors that lie on their own block border).  ``taken`` maps cells to the
    signal that owns them; the segment is rejected when it touches a cell
    owned by a *different* signal.
    """
    x0, y0 = p0
    x1, y1 = p1

    def in_cell(x, y):
        cx = max(0, min(cols - 1, int(math.floor((x - min_x) / cell))))
        cy = max(0, min(rows - 1, int(math.floor((y - min_y) / cell))))
        return cx, cy

    if x0 == x1:
        cx, _ = in_cell(x0, y0)
        _, cy0 = in_cell(x0, y0)
        _, cy1 = in_cell(x0, y1)
        for cy in range(min(cy0, cy1), max(cy0, cy1) + 1):
            c = (cx, cy)
            if c in exempt:
                continue
            if c in blocked0:
                return False
            if taken is not None and taken.get(c, signal) != signal:
                return False
        return True
    if y0 == y1:
        _, cy = in_cell(x0, y0)
        cx0, _ = in_cell(x0, y0)
        cx1, _ = in_cell(x1, y0)
        for cx in range(min(cx0, cx1), max(cx0, cx1) + 1):
            c = (cx, cy)
            if c in exempt:
                continue
            if c in blocked0:
                return False
            if taken is not None and taken.get(c, signal) != signal:
                return False
        return True
    return False


def _poly_free(points, cols, rows, cell, min_x, min_y, blocked0,
               taken=None, signal=None):
    """ True if every consecutive segment of the polyline crosses no block. """
    def in_cell(p):
        cx = max(0, min(cols - 1,
                        int(math.floor((p[0] - min_x) / cell))))
        cy = max(0, min(rows - 1,
                        int(math.floor((p[1] - min_y) / cell))))
        return cx, cy

    anchor0 = in_cell(points[0])
    anchor1 = in_cell(points[-1])
    last = len(points) - 2
    for i in range(len(points) - 1):
        exempt = ()
        if i == 0:
            exempt = (anchor0,)
        if i == last:
            exempt += (anchor1,)
        if not _segment_free(points[i], points[i + 1], cols, rows, cell,
                             min_x, min_y, blocked0, exempt, taken, signal):
            return False
    return True


def _detour(start, end, cols, rows, cell, min_x, min_y, blocked,
            taken=None, signal=None):
    """ Bounded A* detour that prefers straight stretches over zig-zags.

    The search is keyed by cell (not entrance direction) and uses the
    Manhattan distance as an admissible heuristic, so it explores a corridor
    rather than the whole grid.  A node budget keeps it responsive even on a
    very cluttered schematic: when the budget is exhausted the routing gives
    up and lets ``_shortest_path`` fall back to a simpler shape.
    """
    import heapq

    def to_cell(point):
        cx = max(0, min(cols - 1,
                        int(math.floor((point[0] - min_x) / cell))))
        cy = max(0, min(rows - 1,
                        int(math.floor((point[1] - min_y) / cell))))
        return cx, cy

    def taken_by_other(c):
        return taken is not None and taken.get(c, signal) != signal

    def nearest_free(cell0):
        if cell0 not in blocked and not taken_by_other(cell0):
            return cell0
        for radius in range(1, 5):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius and abs(dy) == radius:
                        continue
                    cand = (cell0[0] + dx, cell0[1] + dy)
                    if 0 <= cand[0] < cols and 0 <= cand[1] < rows \
                            and cand not in blocked \
                            and not taken_by_other(cand):
                        return cand
        return None

    sc = to_cell(start)
    ec = to_cell(end)
    if sc == ec:
        return [start, end]
    s0 = nearest_free(sc)
    e0 = nearest_free(ec)
    if s0 is None or e0 is None:
        return None

    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    best = {}
    prev = {}

    def taxi(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    budget = max(4000, min(DETOUR_LIMIT, (cols * rows) // 8))
    best[s0] = 0
    heap = [(taxi(s0, e0), 0, s0[0], s0[1], None)]
    goal = None
    expanded = 0
    while heap:
        _, cost, cx, cy, din = heapq.heappop(heap)
        if cost > best.get((cx, cy), float("inf")):
            continue
        if (cx, cy) == e0:
            goal = (cx, cy)
            break
        expanded += 1
        if expanded > budget:
            return None
        block = _GRID.get("detour_left")
        if block is not None:
            block -= 1
            _GRID["detour_left"] = block
            if block <= 0:
                return None
        for dx, dy in dirs:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            if (nx, ny) in blocked or taken_by_other((nx, ny)):
                continue
            ncost = cost + 1
            if din is not None and (dx, dy) != din:
                ncost += BEND_COST
            if best.get((nx, ny), float("inf")) <= ncost:
                continue
            best[(nx, ny)] = ncost
            prev[(nx, ny)] = (cx, cy, din)
            heapq.heappush(heap, (ncost + taxi((nx, ny), e0), ncost,
                                  nx, ny, (dx, dy)))

    if goal is None:
        return None

    cells = []
    node = goal
    while node is not None:
        cells.append(node)
        node = prev[node][:2] if node in prev else None
    cells.reverse()
    points = [start]
    for cx, cy in cells[:-1]:
        points.append((min_x + (cx + 0.5) * cell,
                       min_y + (cy + 0.5) * cell))
    points.append(end)
    return _simplify(points)


def _simplify(points):
    """ Remove collinear intermediate points from a polyline. """
    if len(points) < 3:
        return points
    out = [points[0]]
    for i in range(1, len(points) - 1):
        a, b, c = points[i - 1], points[i], points[i + 1]
        dx1, dy1 = b[0] - a[0], b[1] - a[1]
        dx2, dy2 = c[0] - b[0], c[1] - b[1]
        if not ((dx1 == 0 and dx2 == 0) or (dy1 == 0 and dy2 == 0)):
            out.append(b)
        else:
            continue
    out.append(points[-1])
    return out
