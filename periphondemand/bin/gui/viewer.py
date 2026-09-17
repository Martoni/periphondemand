#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:     Viewer.py
# Purpose:  Non blocking Tkinter window that draws the block diagram of a POD
#           project (see schematic.py). It runs in its own thread so the POD
#           console stays usable. The console pushes read-only snapshots; the
#           thread only redraws them.
#
# Author:   Fabien Marteau <fabien.marteau@armadeus.com>
#
# Licence:  GPLv3 or newer
# ----------------------------------------------------------------------------
""" Tkinter block diagram viewer.

Commands from the console (in the main thread) are queued and polled from the
viewer thread:
    open_viewer(snapshot) / viewer.refresh(snapshot) / viewer.close()
Tkinter is only touched from the thread that created the widgets.
"""

import queue
import sys
import threading
import time
import tkinter as tk

from periphondemand.bin.gui.schematic import BAND_H
from periphondemand.bin.gui.schematic import FONT_SIZE
from periphondemand.bin.gui.schematic import HEADER_H
from periphondemand.bin.gui.schematic import DIR_IN

# ---------------------------------------------------------------------------
# colors
# ---------------------------------------------------------------------------
BLOCK_COMMON = "#ffffff"
BLOCK_PLATFORM = "#d0e4f0"

CLASS_COLORS = {
    "master": "#cfe2f3",
    "slave": "#d9ead3",
    "clk_rst": "#fff2cc",
    "gls": "#f3f3f3",
    "intercon": "#e6d9f0",
}
CLASS_DEFAULT = "#eeeeee"

PIN_DOT = "#222222"
PIN_DISABLED = "#bdbdbd"
WIRE_PIN = "#5a5a5a"
WIRE_BUS = "#1f77b4"
WIRE_BUS_LABEL = "#0b5394"
HIGHLIGHT = "#e02020"

MIN_ZOOM = 0.25
MAX_ZOOM = 4.0

VIEWER = None


class SchematicViewer(threading.Thread):
    """ The viewer window, running in a dedicated thread. """

    def __init__(self, title):
        threading.Thread.__init__(self)
        self.daemon = True
        self._title = title
        self._snapshot = None
        self._queue = queue.Queue()
        self._root = None
        self._canvas = None
        self._status = None
        self._zoom = 1.0
        self._pin_map = {}
        self._edge_map = {}
        self._edge_style = {}
        self._hl_pin_ids = []
        self._hl_edge_ids = []
        self._dragging = False
        self._press = (0, 0)
        self._window_closed = True
        self.startup_error = None

    # ---- console thread interface ----------------------------------------
    def set_snapshot(self, snapshot):
        self._snapshot = snapshot

    def refresh(self, snapshot):
        self._snapshot = snapshot
        if self._root is not None:
            if self._window_closed:
                self._reopen()
            else:
                self._queue.put("refresh")

    def close(self):
        """ Close the window (the Tk interpreter is kept so that a later
            'view' can reopen the window cheaply and without the
            Tcl_AsyncDelete abort triggered by several interpreters).
        """
        self._queue.put("close")

    def _reopen(self):
        if self._root is not None:
            self._window_closed = False
            self._queue.put("reopen")

    # ---- viewer thread ----------------------------------------------------
    def run(self):
        try:
            self._root = tk.Tk()
        except tk.TclError as error:
            self.startup_error = str(error)
            return
        self._root.title(self._title)
        self._root.geometry("1000x700")
        self._build_widgets()
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._redraw()
        self._window_closed = False
        # fit once the window is realized and its size is known
        self._root.after(60, self._fit_view)
        self._poll()
        try:
            self._root.mainloop()
        except tk.TclError:
            pass

    def _build_widgets(self):
        toolbar = tk.Frame(self._root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        for text, command in (("Fit", self._fit_view),
                              ("Zoom +", self._zoom_in),
                              ("Zoom -", self._zoom_out),
                              ("Refresh", self._redraw),
                              ("Close", self._on_close)):
            button = tk.Button(toolbar, text=text, command=command,
                               relief=tk.RAISED)
            button.pack(side=tk.LEFT, padx=2, pady=2)
        label = tk.Label(toolbar, text="click on a pin to highlight its wires",
                         fg="#777777")
        label.pack(side=tk.RIGHT, padx=8)

        body = tk.Frame(self._root)
        body.pack(fill=tk.BOTH, expand=True)
        hbar = tk.Scrollbar(body, orient=tk.HORIZONTAL)
        vbar = tk.Scrollbar(body, orient=tk.VERTICAL)
        canvas = tk.Canvas(body, background="#fcfcfc",
                           xscrollcommand=hbar.set,
                           yscrollcommand=vbar.set,
                           highlightthickness=0)
        hbar.config(command=canvas.xview)
        vbar.config(command=canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._canvas = canvas
        self._bind(canvas)

        status = tk.Label(self._root, text="", anchor=tk.W, bd=1,
                          relief=tk.SUNKEN)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        self._status = status

    def _bind(self, canvas):
        canvas.bind("<ButtonPress-1>", self._on_press)
        canvas.bind("<B1-Motion>", self._on_drag)
        canvas.bind("<ButtonRelease-1>", self._on_release)
        for button in ("2", "3"):
            canvas.bind("<ButtonPress-%s>" % button, self._on_pan)
            canvas.bind("<B%s-Motion>" % button, self._on_pan_drag)
        canvas.bind("<Button-4>", self._on_wheel)
        canvas.bind("<Button-5>", self._on_wheel)
        canvas.bind("<MouseWheel>", self._on_wheel)

    # ---- redraw -----------------------------------------------------------
    def _redraw(self):
        canvas = self._canvas
        snapshot = self._snapshot
        if snapshot is None:
            canvas.configure(scrollregion=(0, 0, 1, 1))
            return
        # remember the canvas centre so zoom keeps the viewport position
        try:
            cw = canvas.winfo_width()
            ch = canvas.winfo_height()
        except tk.TclError:
            cw, ch = 800, 600
        if cw < 2:
            cw, ch = 800, 600
        cx = canvas.canvasx(cw // 2)
        cy = canvas.canvasy(ch // 2)

        canvas.delete("all")
        self._pin_map = {}
        self._edge_map = {}
        self._edge_style = {}
        self._hl_pin_ids = []
        self._hl_edge_ids = []
        zoom = self._zoom
        small = ("TkFixedFont", max(1, int(round(8 * zoom))))
        font = ("TkFixedFont", max(1, int(round(FONT_SIZE * zoom))))

        for inst in snapshot.instances:
            self._draw_instance(canvas, inst, zoom, font, small)
        for edge in snapshot.edges:
            self._draw_edge(canvas, edge, zoom, small)

        canvas.configure(scrollregion=canvas.bbox("all"))
        region = canvas.bbox("all")
        if region:
            x0, y0, x1, y1 = region
            if (x1 - x0) > cw or (y1 - y0) > ch:
                canvas.xview_moveto((cx - cw / 2) / float(x1 - x0))
                canvas.yview_moveto((cy - ch / 2) / float(y1 - y0))

    def _draw_instance(self, canvas, inst, zoom, font, small):
        x0 = inst.rect_x * zoom
        y0 = inst.y * zoom
        x1 = (inst.rect_x + inst.w) * zoom
        y1 = (inst.y + inst.h) * zoom
        fill = BLOCK_PLATFORM if inst.is_platform else BLOCK_COMMON
        canvas.create_rectangle(x0, y0, x1, y1, fill=fill,
                                outline="#333333",
                                width=max(1, int(round(zoom))))
        canvas.create_text((inst.rect_x + inst.w / 2) * zoom,
                           (inst.y + HEADER_H / 2) * zoom,
                           text=inst.instancename, font=font,
                           fill="#000000")
        for idoc in inst.interfaces:
            bx0 = idoc.x * zoom
            by0 = idoc.y * zoom
            bx1 = (idoc.x + idoc.w) * zoom
            by1 = (idoc.y + BAND_H) * zoom
            color = CLASS_COLORS.get(idoc.interface_class, CLASS_DEFAULT)
            canvas.create_rectangle(bx0, by0, bx1, by1, fill=color,
                                    outline="#888888",
                                    width=max(1, int(round(zoom / 2))))
            header = idoc.name
            if idoc.interface_class:
                header += " [%s]" % idoc.interface_class
            if idoc.bus_name:
                header += " (%s)" % idoc.bus_name
            canvas.create_text((idoc.x + idoc.w / 2) * zoom,
                               (idoc.y + BAND_H / 2) * zoom,
                               text=header, font=small, fill="#333333")
            for row in idoc.rows:
                self._draw_row(canvas, row, zoom, small)

    def _draw_row(self, canvas, row, zoom, small):
        x = row.x * zoom
        y = row.y * zoom
        radius = max(2, int(round(2.5 * zoom)))
        color = PIN_DISABLED if row.key[3] is None else PIN_DOT
        dot = canvas.create_oval(x - radius, y - radius, x + radius,
                                 y + radius, fill=color, outline="")
        self._pin_map[dot] = row.key
        label_color = "#777777" if row.key[3] is None else "#222222"
        if row.side == DIR_IN:
            text = canvas.create_text(x - 4 * zoom, y, text=row.label,
                                      font=small, anchor="e",
                                      fill=label_color)
        else:
            text = canvas.create_text(x + 4 * zoom, y, text=row.label,
                                      font=small, anchor="w",
                                      fill=label_color)
        self._pin_map[text] = row.key

    def _draw_edge(self, canvas, edge, zoom, small):
        coords = []
        for px, py in edge.points:
            coords.append(px * zoom)
            coords.append(py * zoom)
        if not coords:
            return
        if edge.kind == "bus":
            width = max(2, int(round((edge.width or 3) * zoom)))
            color = WIRE_BUS
        else:
            width = max(1, int(round(zoom)))
            color = WIRE_PIN
        item = canvas.create_line(*coords, fill=color, width=width,
                                  capstyle=tk.ROUND, joinstyle=tk.ROUND)
        endpoints = set((edge.k1, edge.k2))
        self._edge_map[item] = (edge, endpoints)
        self._edge_style[item] = (color, width)
        if edge.kind == "bus" and edge.bus_name and edge.label is not None:
            lx, ly = edge.label
            label = canvas.create_text(lx * zoom, ly * zoom,
                                       text=edge.bus_name, font=small,
                                       fill=WIRE_BUS_LABEL)
            self._edge_map[label] = (edge, endpoints)

    # ---- interaction ------------------------------------------------------
    def _on_press(self, event):
        self._press = (event.x, event.y)
        self._dragging = False
        self._canvas.scan_mark(event.x, event.y)

    def _on_drag(self, event):
        dx = abs(event.x - self._press[0])
        dy = abs(event.y - self._press[1])
        if dx > 5 or dy > 5:
            self._dragging = True
        if self._dragging:
            self._canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_release(self, event):
        if self._dragging:
            self._dragging = False
            return
        self._select(event.x, event.y)

    def _on_pan(self, event):
        self._canvas.scan_mark(event.x, event.y)

    def _on_pan_drag(self, event):
        self._canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_wheel(self, event):
        delta = getattr(event, "delta", 0)
        if event.num == 4 or delta > 0:
            self._zoom_by(1.15)
        elif event.num == 5 or delta < 0:
            self._zoom_by(1 / 1.15)

    def _select(self, x, y):
        canvas = self._canvas
        # event coordinates are in the canvas *window* screen space while
        # the find_* queries use the *canvas* coordinate space
        x = canvas.canvasx(x)
        y = canvas.canvasy(y)
        items = canvas.find_closest(x, y)
        if not items:
            self._clear_highlight()
            return
        item = items[0]
        if item in self._pin_map:
            self._highlight_pin(item)
        elif item in self._edge_map:
            edge, _ = self._edge_map[item]
            self._highlight_edge(edge)
        else:
            self._clear_highlight()

    def _highlight_pin(self, item):
        key = self._pin_map[item]
        self._clear_highlight()
        for iid, rowkey in self._pin_map.items():
            if rowkey == key:
                try:
                    self._canvas.itemconfig(iid, fill=HIGHLIGHT)
                    self._hl_pin_ids.append(iid)
                except tk.TclError:
                    pass
        for eid, (edge, endpoints) in self._edge_map.items():
            if key in endpoints:
                _, width = self._edge_style.get(eid, (WIRE_PIN, 1))
                try:
                    self._canvas.itemconfig(eid, fill=HIGHLIGHT,
                                            width=max(3, width + 1))
                    self._hl_edge_ids.append(eid)
                except tk.TclError:
                    pass
        self._status_update(key)

    def _highlight_edge(self, edge):
        self._clear_highlight()
        for eid, (an_edge, _) in self._edge_map.items():
            if an_edge is edge:
                try:
                    self._canvas.itemconfig(eid, fill=HIGHLIGHT)
                    self._hl_edge_ids.append(eid)
                except tk.TclError:
                    pass
        if self._status is not None:
            if edge.kind == "bus":
                label = "%s.%s <-> %s.%s" % (edge.k1[0], edge.k1[1],
                                             edge.k2[0], edge.k2[1])
            else:
                label = self._key_to_text(edge.k1) + " <-> " + \
                    self._key_to_text(edge.k2)
            self._status.config(text=label)

    def _clear_highlight(self):
        for iid in self._hl_edge_ids:
            edge, _ = self._edge_map.get(iid, (None, None))
            if edge is not None:
                color, width = self._edge_style.get(iid,
                                                    (WIRE_PIN, 1))
                try:
                    self._canvas.itemconfig(iid, fill=color, width=width)
                except tk.TclError:
                    pass
        self._hl_edge_ids = []
        for iid in self._hl_pin_ids:
            key = self._pin_map.get(iid)
            color = PIN_DISABLED if key is not None and \
                key[3] is None else PIN_DOT
            try:
                self._canvas.itemconfig(iid, fill=color)
            except tk.TclError:
                pass
        self._hl_pin_ids = []
        if self._status is not None:
            self._status.config(text="")

    def _status_update(self, key):
        if self._status is not None:
            self._status.config(text=self._key_to_text(key))

    @staticmethod
    def _key_to_text(key):
        inst, iface, port, num = key
        if num is None:
            return "%s.%s.%s" % (inst, iface, port)
        return "%s.%s.%s.%s" % (inst, iface, port, num)

    # ---- zoom / fit ------------------------------------------------------
    def _zoom_by(self, factor):
        self._zoom = max(MIN_ZOOM, min(MAX_ZOOM, self._zoom * factor))
        self._redraw()

    def _zoom_in(self):
        self._zoom_by(1.3)

    def _zoom_out(self):
        self._zoom_by(1 / 1.3)

    def _fit_view(self):
        canvas = self._canvas
        region = canvas.bbox("all")
        if not region:
            return
        x0, y0, x1, y1 = region
        bw = x1 - x0
        bh = y1 - y0
        if bw <= 0 or bh <= 0:
            return
        try:
            cw = canvas.winfo_width()
            ch = canvas.winfo_height()
        except tk.TclError:
            cw, ch = 800, 600
        if cw < 2 or ch < 2:
            cw, ch = 800, 600
        zoom = min(cw / bw, ch / bh)
        self._zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        self._redraw()

    # ---- polling ----------------------------------------------------------
    def _poll(self):
        if self._root is None:
            return
        try:
            while True:
                command = self._queue.get_nowait()
                if command == "refresh":
                    self._redraw()
                elif command == "reopen":
                    try:
                        self._root.deiconify()
                        self._redraw()
                        self._root.after(60, self._fit_view)
                    except tk.TclError:
                        pass
                elif command == "close":
                    self._on_close()
        except queue.Empty:
            pass
        try:
            self._root.after(80, self._poll)
        except tk.TclError:
            pass

    def _on_close(self):
        """ Hide the window instead of destroying the Tk interpreter: the
            interpreter lives for the whole process so that repeated
            open/close cycles do not build a pile of interpreters that would
            abort at interpreter shutdown (Tcl_AsyncDelete).
        """
        self._window_closed = True
        try:
            self._root.withdraw()
        except tk.TclError:
            pass


def open_viewer(snapshot):
    """ Open (or refresh) the schematic viewer window with the given snapshot.
        Returns the viewer, or None if the GUI cannot be started.
    """
    global VIEWER
    if VIEWER is not None and VIEWER.is_alive():
        VIEWER.refresh(snapshot)
        return VIEWER
    viewer = SchematicViewer(snapshot.title)
    viewer.set_snapshot(snapshot)
    VIEWER = viewer
    viewer.start()
    time.sleep(0.05)
    if viewer.startup_error:
        sys.stdout.write("Unable to open the graphical viewer: %s\n" %
                         viewer.startup_error)
        VIEWER = None
        return None
    return viewer


def close_viewer():
    """ Ask the viewer window to close (if any). The Tk interpreter and its
        thread are kept alive so that a later 'view' reopens the same window.
    """
    global VIEWER
    if VIEWER is not None:
        VIEWER.close()