# The MIT License
#
# Copyright (c) 2010 Mikael Lind
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import math
import re
from xml.dom import minidom

class ParseError(Exception):
    pass

def squared_distance(p1, p2):
    """return the squared distance of two points"""
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    return dx ** 2 + dy ** 2

def distance(p1, p2):
    """return the distance of two points"""
    return math.sqrt(squared_distance(p1, p2))

class Document(object):
    def __init__(self, file, flatten=('style', 'desc'), index='id'):
        document = minidom.parse(file)
        svg_element = document.getElementsByTagName('svg')[0]
        self.root = parse_element(svg_element, None)
        self.elements = {}
        if flatten:
            for attr in flatten:
                self.flatten(attr)
        self.reindex(index)

    def flatten(self, attr):
        self.root._flatten(attr)

    def reindex(self, attr='id'):
        self.elements.clear()
        if id is not None:
            self.root._reindex(self, attr)

class Element(object):
    def __init__(self):
        self.parent = None
        self.children = []
        self.transform = Transform()
        self.shapes = []
        self.attributes = {}

    def _flatten(self, attr):
        value = self.attributes.pop(attr, None)
        if value is not None:
            attributes = parse_style(value)
            self.attributes.update(attributes)
        for child in self.children:
            child._flatten(attr)

    def _reindex(self, document, attr):
        value = self.attributes.get(attr)
        if value:
            document.elements[value] = self
        for child in self.children:
            child._reindex(document, attr)

class Shape(object):
    @property
    def envelope(self):
        raise NotImplementedError()

    @property
    def area(self):
        raise NotImplementedError()

    @property
    def centroid(self):
        raise NotImplementedError()

class Envelope(Shape):
    def __init__(self, min_x=float('inf'), min_y=float('inf'),
                 max_x=float('-inf'), max_y=float('-inf')):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def add(self, shape):
        envelope = shape.envelope
        self.min_x = min(self.min_x, envelope.min_x)
        self.min_y = min(self.min_x, envelope.min_x)
        self.max_x = max(self.max_x, envelope.max_x)
        self.max_y = max(self.max_y, envelope.max_y)

    def __nonzero__(self):
        return self.min_x <= self.max_x and self.min_y <= self.max_y

    @property
    def envelope(self):
        return self

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def height(self):
        return self.y2 - self.y1

    @property
    def area(self):
        return self.width * self.height

    @property
    def x(self):
        return 0.5 * (self.x1 + self.x2)

    @property
    def y(self):
        return 0.5 * (self.y1 + self.y2)

    @property
    def centroid(self):
        return self.x, self.y

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def envelope(self):
        return Envelope(self.x, self.y, self.x, self.y)

    @property
    def area(self):
        return 0.0

    @property
    def centroid(self):
        return self.x, self.y

class Line(Shape):
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2

    def __repr__(self):
        return ('Line(x1=%r, y1=%r, x2=%r, y2=%r)' %
                (self.x1, self.y1, self.x2, self.y2))

    def __rmul__(self, transform):
        x1, y1 = transform * (self.x1, self.y1)
        x2, y2 = transform * (self.x2, self.y2)
        return Line(x1, y1, x2, y2)

    @property
    def area(self):
        return 0.0

    @property
    def envelope(self):
        return (min(self.x1, self.x2), min(self.y1, self.y2),
                max(self.x1, self.x2), max(self.y1, self.y2))

class Polyline(Shape):
    def __init__(self, points):
        self.points = list(points)

    def __repr__(self):
        return 'Polyline(%r)' % self.points

    def __rmul__(self, transform):
        return Polyline(transform * p for p in self.points)

    @property
    def area(self):
        return 0.0

    @property
    def envelope(self):
        xs, ys = zip(*self.points)
        return min(xs), min(ys), max(xs), max(ys)

class Polygon(Shape):
    def __init__(self, points):
        self.points = list(points)

    def __repr__(self):
        return 'Polygon(%r)' % self.points

    def __rmul__(self, transform):
        return Polygon(transform * p for p in self.points)

    @property
    def area(self):
        # http://mathworld.wolfram.com/PolygonArea.html
        area = 0.0
        for i in xrange(len(self.points)):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i + 1) % len(self.points)]
            area += x1 * y2 - x2 * y1
        return area / 2.0

    @property
    def envelope(self):
        xs, ys = zip(*self.points)
        return min(xs), min(ys), max(xs), max(ys)

    def repair(self, epsilon=0.0):
        if (len(self.points) >= 2 and
            squared_distance(self.points[0], self.points[-1]) < epsilon ** 2):
            self.points.pop()
        if self.area < 0.0:
            self.points.reverse()

class Circle(Shape):
    def __init__(self, cx, cy, r):
        self.cx, self.cy = cx, cy
        self.r = r

    def __repr__(self):
        return 'Circle(cx=%r, cy=%r, r=%r)' % (self.cx, self.cy, self.r)

    def __rmul__(self, transform):
        cx, cy = transform * (self.cx, self.cy)
        px, py = transform * (self.cx + self.r, self.cy)
        r = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        return Circle(cx, cy, r)

    @property
    def centroid(self):
        return self.cx, self.cy

    @property
    def envelope(self):
        return (self.cx - self.r, self.cy - self.r,
                self.cx + self.r, self.cy + self.r)

class Rect(Shape):
    def __init__(self, x, y, width, height, rx, ry):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rx = rx
        self.ry = ry

class Path(Shape):
    _scanner = re.Scanner([
        ('[MmZzLlHhVvCcSsQqTtAa]', (lambda s, t: t)),
        ('[-+0-9.Ee]+', (lambda s, t: float(t))),
        ('[, \t\r\n]+', None),
    ])

    _arg_counts = dict(M=2, Z=0, L=2, H=1, V=1, C=6, S=4, Q=4, T=2, A=7,
                       m=2, z=0, l=2, h=1, v=1, c=6, s=4, q=4, t=2, a=7)

    def __init__(self, arg):
        if isinstance(arg, basestring):
            commands = self._parse_commands(arg)
            commands = self._split_polycommands(commands)
            commands = self._to_absolute_commands(commands)
            self.commands = list(commands)
        else:
            self.commands = list(arg)

    @classmethod
    def _parse_commands(cls, path_str):
        tokens, remainder = cls._scanner.scan(path_str)
        if remainder:
            raise ParseError('could not tokenize path: ' + remainder)
        command = []
        for token in tokens:
            if isinstance(token, basestring):
                if command:
                    yield tuple(command)
                    del command[:]
            else:
                if not command:
                    raise ParseError('argument before first command')
                if command[0] in 'Aa':
                    arg_index = (len(command) - 1) % 7
                    if arg_index in (0, 1):
                        token = abs(token)
                    elif arg_index in (3, 4):
                        token = bool(token)
            command.append(token)
        if command:
            yield tuple(command)

    @classmethod
    def _split_polycommands(cls, commands):
        for command in commands:
            name = command[0]
            arg_count = cls._arg_counts[name]
            if len(command) - 1 > arg_count:
                for i in xrange(1, len(command), arg_count):
                    if name == 'M' and i > 1:
                        name = 'L'
                    if name == 'm' and i > 1:
                        name = 'l'
                    yield (name,) + command[i:i + arg_count]
            else:
                yield command

    @classmethod
    def _to_absolute_commands(cls, commands):
        mx, my = 0.0, 0.0
        cx, cy = 0.0, 0.0
        for command in commands:
            x, y = cx, cy
            name, args = command[0], command[1:]
            if name == 'M':
                x, y = args
                mx, my = x, y
            elif name == 'm':
                x, y = args
                x += cx
                y += cy
                mx, my = x, y
                command = 'M', x, y
            elif name == 'Z':
                x, y = mx, my
            elif name == 'z':
                x, y = mx, my
                command = 'Z',
            elif name == 'L':
                x, y = args
            elif name == 'l':
                x, y = args
                x += cx
                y += cy
                command = 'L', x, y
            elif name == 'H':
                x, = args
                command = 'L', x, y
            elif name == 'h':
                x, = args
                x += cx
                command = 'L', x, y
            elif name == 'V':
                y, = args
                command = 'L', x, y
            elif name == 'v':
                y, = args
                y += cy
                command = 'L', x, y
            elif name == 'C':
                _, _, _, _, x, y = args
            elif name == 'c':
                x1, y1, x2, y2, x, y = args
                x1 += cx
                y1 += cy
                x2 += cx
                y2 += cy
                x += cx
                y += cy
                command = 'C', x1, y1, x2, y2, x, y
            elif name == 'S':
                _, _, x, y = args
            elif name == 's':
                x2, y2, x, y = args
                x2 += cx
                y2 += cy
                x += cx
                y += cy
                command = 'S', x2, y2, x, y
            elif name == 'Q':
                _, _, x, y = args
            elif name == 'q':
                x1, y1, x, y = args
                x1 += cx
                y1 += cy
                x += cx
                y += cy
                command = 'Q', x1, y1, x, y
            elif name == 'T':
                x, y = args
            elif name == 't':
                x, y = args
                x += cx
                y += cy
                command = 'T', x, y
            elif name == 'A':
                _, _, _, _, _, x, y = args
            elif name == 'a':
                rx, ry, rotation, large, sweep, x, y = args
                x += cx
                y += cy
                command = 'A', rx, ry, rotation, large, sweep, x, y
            else:
                assert False
            cx, cy = x, y
            yield command

    @property
    def subpaths(self):
        commands = []
        for command in self.commands:
            if commands and command[0] in 'Mm':
                yield Path(commands)
                del commands[:]
            commands.append(command)
        if commands:
            yield Path(commands)

    def linearize(self):
        for path in self.subpaths:
            points = []
            closed = False
            for command in path.commands:
                if command[0] == 'Z':
                    closed = True
                else:
                    points.append(command[-2:])
            if closed:
                yield Polygon(points)
            else:
                if len(points) == 2:
                    p1, p2 = points
                    x1, y1 = p1
                    x2, y2 = p2
                    yield Line(x1, y1, x2, y2)
                else:
                    yield Polyline(points)

    def __str__(self):
        return ' '.join(self._format_command(c) for c in self.commands)

    @classmethod
    def _format_command(cls, command):
        name, args = command[0], command[1:]
        parts = [name]
        parts.extend('%g' % arg for arg in args)
        return ' '.join(parts)

def get_element_text(xml_element):
    text = ''.join(child.nodeValue for child in xml_element.childNodes
                   if child.nodeType == child.TEXT_NODE)
    text = ' '.join(text.split())
    return text

def parse_element(xml_element, parent):
    pinky_element = Element()
    pinky_element.parent = parent
    pinky_element.transform = Transform(xml_element.getAttribute('transform'))
    if xml_element.hasAttribute('id'):
        pinky_element.attributes['id'] = xml_element.getAttribute('id')
    if xml_element.hasAttribute('inkscape:label'):
        pinky_element.attributes['label'] = xml_element.getAttribute('inkscape:label')
    if xml_element.hasAttribute('style'):
        pinky_element.attributes['style'] = xml_element.getAttribute('style')
    if xml_element.nodeName == 'path':
        parse_path_element(xml_element, pinky_element)
    elif xml_element.nodeName == 'rect':
        parse_rect_element(xml_element, pinky_element)
    for xml_child in xml_element.childNodes:
        if xml_child.nodeType == xml_child.ELEMENT_NODE:
            if xml_child.nodeName == 'title':
                pinky_element.attributes['title'] = get_element_text(xml_child)
            elif xml_child.nodeName == 'desc':
                pinky_element.attributes['desc'] = get_element_text(xml_child)
            elif xml_child.nodeName == 'sodipodi:namedview':
                if xml_child.hasAttribute('pagecolor'):
                    pinky_element.attributes['pagecolor'] = xml_child.getAttribute('pagecolor')
            else:
                child = parse_element(xml_child, pinky_element)
                pinky_element.children.append(child)
    return pinky_element

def parse_path_element(xml_element, pinky_element):
    if xml_element.getAttribute('sodipodi:type') == 'arc':
        return parse_arc_element(xml_element, pinky_element)
    path = Path(xml_element.getAttribute('d'))
    pinky_element.shapes.append(path)

def parse_arc_element(xml_element, pinky_element):
    cx = float(xml_element.getAttribute('sodipodi:cx') or '0')
    cy = float(xml_element.getAttribute('sodipodi:cy') or '0')
    rx = float(xml_element.getAttribute('sodipodi:rx'))
    ry = float(xml_element.getAttribute('sodipodi:ry'))
    circle = Circle(cx, cy, (rx + ry) / 2.0)
    pinky_element.shapes.append(circle)

def parse_rect_element(xml_element, pinky_element):
    x = float(xml_element.getAttribute('x') or '0')
    y = float(xml_element.getAttribute('y') or '0')
    width = float(xml_element.getAttribute('width'))
    height = float(xml_element.getAttribute('height'))
    points = [(x, y), (x + width, y),
              (x + width, y + height), (x, y + height)]
    polygon = Polygon(points)
    pinky_element.shapes.append(polygon)

def parse_style(style_str):
    lines = (l.strip() for l in style_str.split(';'))
    pairs = (l.split(':') for l in lines if l)
    return dict((k.strip(), v.strip()) for k, v in pairs)

def parse_color(color_str):
    if color_str == 'none':
        return None
    elif len(color_str) == 7 and color_str[0] == '#':
        return (int(color_str[1:3], 16), int(color_str[3:5], 16),
                int(color_str[5:7], 16))
    else:
        raise ParseError('invalid color: ' + color_str)

def parse_float_color(color_str):
    color = parse_color(color_str)
    if color is not None:
        red, green, blue = color
        color = float(red) / 255.0, float(green) / 255.0, float(blue) / 255.0
    return color

class Transform(object):
    def __init__(self, *args):
        if not args:
            self.abcdef = 1.0, 0.0, 0.0, 1.0, 0.0, 0.0
        elif len(args) == 6:
            self.abcdef = args
        elif len(args) == 1 and isinstance(args[0], basestring):
            transform = self._parse(args[0])
            self.abcdef = transform.abcdef
        else:
            raise ValueError('invalid arguments for initializer')

    @classmethod
    def _parse(cls, transform_str):
        transform = Transform()
        for part in transform_str.replace(',', ' ').split(')')[:-1]:
            name, args = part.strip().split('(')
            name = name.rstrip()
            args = map(float, args.split())
            if name == 'matrix':
                transform *= cls(*args)
            elif name == 'translate':
                transform *= cls.from_translate(*args)
            elif name == 'scale':
                transform *= cls.from_scale(*args)
            elif name == 'rotate':
                transform *= cls.from_rotate(*args)
            elif name == 'skewX':
                transform *= cls.from_skew_x(*args)
            elif name == 'skewY':
                transform *= cls.from_skew_y(*args)
            else:
                raise ParseError('invalid transform name: ' + name)
        return transform

    def __str__(self):
        return 'matrix(%g %g %g %g %g %g)' % self.abcdef

    def __repr__(self):
        return 'Transform(%r, %r, %r, %r, %r, %r)' % self.abcdef

    def __mul__(self, other):
        if isinstance(other, Transform):
            a1, b1, c1, d1, e1, f1 = self.abcdef
            a2, b2, c2, d2, e2, f2 = other.abcdef
            a3 = a1 * a2 + c1 * b2
            b3 = b1 * a2 + d1 * b2
            c3 = a1 * c2 + c1 * d2
            d3 = b1 * c2 + d1 * d2
            e3 = a1 * e2 + c1 * f2 + e1
            f3 = b1 * e2 + d1 * f2 + f1
            return Transform(a3, b3, c3, d3, e3, f3)
        elif isinstance(other, tuple):
            a, b, c, d, e, f = self.abcdef
            x, y = other
            return a * x + c * y + e, b * x + d * y + f
        else:
            return NotImplemented

    @classmethod
    def from_matrix(cls, a=1.0, b=0.0, c=0.0, d=1.0, e=0.0, f=0.0):
        return cls(a, b, c, d, e, f)

    @classmethod
    def from_translate(cls, tx, ty=0.0):
        return cls.from_matrix(e=tx, f=ty)

    @classmethod
    def from_scale(cls, sx, sy=None):
        if sy is None:
            sy = sx
        return cls.from_matrix(a=sx, d=sy)
    
    @classmethod
    def from_rotate(cls, angle_deg, *args):
        if args:
            cx, cy = args
            return (cls.from_translate(cx, cy) * cls.from_rotate(angle_deg) *
                    cls.from_translate(-cx, -cy))
        angle_rad = angle_deg * math.pi / 180.0
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        return cls.from_matrix(a=cos_angle, b=sin_angle, c=-sin_angle,
                               d=cos_angle)

    @classmethod
    def from_skew_x(cls, angle_deg):
        angle_rad = angle_deg * math.pi / 180.0
        return cls.from_matrix(c=math.tan(angle_rad))

    @classmethod
    def from_skew_y(cls, angle_deg):
        angle_rad = angle_deg * math.pi / 180.0
        return cls.from_matrix(b=math.tan(angle_rad))
