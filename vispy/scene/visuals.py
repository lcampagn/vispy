# -*- coding: utf-8 -*-
# Copyright (c) Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
"""
The classes in scene.visuals are visuals that may be added to a scenegraph
using the methods and properties defined in `vispy.scene.Node` such as name,
visible, parent, children, etc...

These classes are automatically generated by mixing `vispy.scene.Node` with
the Visual classes found in `vispy.visuals`.

For developing custom visuals, it is recommended to subclass from
`vispy.visuals.Visual` rather than `vispy.scene.Node`.
"""
import re
import weakref

from .. import visuals
from .node import Node
from ..visuals.filters import Alpha, PickingFilter


class VisualNode(Node):
    _next_id = 1
    _visual_ids = weakref.WeakValueDictionary()

    def __init__(self, parent=None, name=None):
        Node.__init__(self, parent=parent, name=name,
                      transforms=self.transforms)
        self.interactive = False
        self._opacity_filter = Alpha()
        self.attach(self._opacity_filter)

        self._id = VisualNode._next_id
        VisualNode._visual_ids[self._id] = self
        VisualNode._next_id += 1
        self._picking_filter = PickingFilter(id_=self._id)
        self.attach(self._picking_filter)

    def _update_opacity(self):
        self._opacity_filter.alpha = self._opacity
        self.update()

    def _set_clipper(self, node, clipper):
        """Assign a clipper that is inherited from a parent node.

        If *clipper* is None, then remove any clippers for *node*.
        """
        if node in self._clippers:
            self.detach(self._clippers.pop(node))
        if clipper is not None:
            self.attach(clipper)
            self._clippers[node] = clipper

    @property
    def picking(self):
        """Boolean that determines whether this node (and its children) are
        drawn in picking mode.
        """
        return self._picking

    @picking.setter
    def picking(self, p):
        for c in self.children:
            c.picking = p
        if self._picking == p:
            return
        self._picking = p
        self._picking_filter.enabled = p
        self.update_gl_state(blend=not p)

    @property
    def interactive(self):
        """Whether this widget should be allowed to accept mouse and touch
        events.
        """
        return self._interactive

    @interactive.setter
    def interactive(self, i):
        self._interactive = i

    def draw(self):
        if self.picking and not self.interactive:
            return
        self._visual_superclass.draw(self)


def create_visual_node(subclass):
    # Create a new subclass of Node.

    # Decide on new class name
    clsname = subclass.__name__
    if not (clsname.endswith('Visual') and
            issubclass(subclass, visuals.BaseVisual)):
        raise RuntimeError('Class "%s" must end with Visual, and must '
                           'subclass BaseVisual' % clsname)
    clsname = clsname[:-6]

    # Generate new docstring based on visual docstring
    try:
        doc = generate_docstring(subclass, clsname)
    except Exception:
        # If parsing fails, just return the original Visual docstring
        doc = subclass.__doc__

    # New __init__ method
    def __init__(self, *args, **kwargs):
        parent = kwargs.pop('parent', None)
        name = kwargs.pop('name', None)
        self.name = name  # to allow __str__ before Node.__init__
        self._visual_superclass = subclass

        subclass.__init__(self, *args, **kwargs)
        self.unfreeze()
        VisualNode.__init__(self, parent=parent, name=name)
        self.freeze()

    # Create new class
    cls = type(clsname, (VisualNode, subclass),
               {'__init__': __init__, '__doc__': doc})

    return cls


def generate_docstring(subclass, clsname):
    # Generate a Visual+Node docstring by modifying the Visual's docstring
    # to include information about Node inheritance and extra init args.

    sc_doc = subclass.__doc__
    if sc_doc is None:
        sc_doc = ""

    # find locations within docstring to insert new parameters
    lines = sc_doc.split("\n")

    # discard blank lines at start
    while lines and lines[0].strip() == '':
        lines.pop(0)

    i = 0
    params_started = False
    param_indent = None
    first_blank = None
    param_end = None
    while i < len(lines):
        line = lines[i]
        # ignore blank lines and '------' lines
        if re.search(r'\w', line):
            indent = len(line) - len(line.lstrip())
            # If Params section has already started, check for end of params
            # (that is where we will insert new params)
            if params_started:
                if indent < param_indent:
                    break
                elif indent == param_indent:
                    # might be end of parameters block..
                    if re.match(r'\s*[a-zA-Z0-9_]+\s*:\s*\S+', line) is None:
                        break
                param_end = i + 1

            # Check for beginning of params section
            elif re.match(r'\s*Parameters\s*', line):
                params_started = True
                param_indent = indent
                if first_blank is None:
                    first_blank = i

        # Check for first blank line
        # (this is where the Node inheritance description will be
        # inserted)
        elif first_blank is None and line.strip() == '':
            first_blank = i

        i += 1
        if i == len(lines) and param_end is None:
            # reached end of docstring; insert here
            param_end = i

    # If original docstring has no params heading, we need to generate it.
    if not params_started:
        lines.extend(["", "    Parameters", "    ----------"])
        param_end = len(lines)
        if first_blank is None:
            first_blank = param_end - 3
        params_started = True

    # build class and parameter description strings
    class_desc = ("\n    This class inherits from visuals.%sVisual and "
                  "scene.Node, allowing the visual to be placed inside a "
                  "scenegraph.\n" % (clsname))
    parm_doc = ("    parent : Node\n"
                "        The parent node to assign to this node (optional).\n"
                "    name : string\n"
                "        A name for this node, used primarily for debugging\n"
                "        (optional).")

    # assemble all docstring parts
    lines = (lines[:first_blank] +
             [class_desc] +
             lines[first_blank:param_end] +
             [parm_doc] +
             lines[param_end:])

    doc = '\n'.join(lines)
    return doc

# This is _not_ automated to help with auto-completion of IDEs,
# python REPL and IPython.
# Explicitly initializing these members allow IDEs to lookup
# and provide auto-completion. One problem is the fact that
# Docstrings are _not_ looked up correctly by IDEs, since they
# are attached programatically in the create_visual_node call.
# However, help(vispy.scene.FooVisual) still works

Arrow = create_visual_node(visuals.ArrowVisual)
Axis = create_visual_node(visuals.AxisVisual)
Box = create_visual_node(visuals.BoxVisual)
ColorBar = create_visual_node(visuals.ColorBarVisual)
Compound = create_visual_node(visuals.CompoundVisual)
Cube = create_visual_node(visuals.CubeVisual)
Ellipse = create_visual_node(visuals.EllipseVisual)
Graph = create_visual_node(visuals.GraphVisual)
GridLines = create_visual_node(visuals.GridLinesVisual)
GridMesh = create_visual_node(visuals.GridMeshVisual)
Histogram = create_visual_node(visuals.HistogramVisual)
Image = create_visual_node(visuals.ImageVisual)
InfiniteLine = create_visual_node(visuals.InfiniteLineVisual)
Isocurve = create_visual_node(visuals.IsocurveVisual)
Isoline = create_visual_node(visuals.IsolineVisual)
Isosurface = create_visual_node(visuals.IsosurfaceVisual)
Line = create_visual_node(visuals.LineVisual)
LinearRegion = create_visual_node(visuals.LinearRegionVisual)
LinePlot = create_visual_node(visuals.LinePlotVisual)
Markers = create_visual_node(visuals.MarkersVisual)
Mesh = create_visual_node(visuals.MeshVisual)
Plane = create_visual_node(visuals.PlaneVisual)
Polygon = create_visual_node(visuals.PolygonVisual)
Rectangle = create_visual_node(visuals.RectangleVisual)
RegularPolygon = create_visual_node(visuals.RegularPolygonVisual)
ScrollingLines = create_visual_node(visuals.ScrollingLinesVisual)
Spectrogram = create_visual_node(visuals.SpectrogramVisual)
Sphere = create_visual_node(visuals.SphereVisual)
SurfacePlot = create_visual_node(visuals.SurfacePlotVisual)
Text = create_visual_node(visuals.TextVisual)
Tube = create_visual_node(visuals.TubeVisual)
# Visual = create_visual_node(visuals.Visual)  # Should not be created
Volume = create_visual_node(visuals.VolumeVisual)
XYZAxis = create_visual_node(visuals.XYZAxisVisual)

__all__ = [name for (name, obj) in globals().items()
           if isinstance(obj, type) and issubclass(obj, VisualNode)]
