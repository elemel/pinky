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

def parse_style(style_str):
    lines = (l.strip() for l in style_str.split(';'))
    pairs = (l.split(':') for l in lines if l)
    return dict((k.strip(), v.strip()) for k, v in pairs)

class Matrix(object):
    def __init__(self, *args):
        if not args:
            self.abcdef = 1.0, 0.0, 0.0, 1.0, 0.0, 0.0
        elif len(args) == 6:
            self.abcdef = args
        elif len(args) == 1 and isinstance(args[0], basestring):
            matrix = self._parse(args[0])
            self.abcdef = matrix.abcdef
        else:
            raise ValueError('invalid arguments for matrix initializer')

    @classmethod
    def _parse(cls, transform_list_str):
        matrix = Matrix()
        for transform_str in transform_list_str.replace(',', ' ').split(')')[:-1]:
            name, args = transform_str.strip().split('(')
            name = name.rstrip()
            args = map(float, args.split())
            if name == 'matrix':
                matrix *= cls(*args)
            elif name == 'translate':
                matrix *= cls.from_translate(*args)
            elif name == 'scale':
                matrix *= cls.from_scale(*args)
            elif name == 'rotate':
                matrix *= cls.from_rotate_deg(*args)
            elif name == 'skewX':
                matrix *= cls.from_skew_x_deg(*args)
            elif name == 'skewY':
                matrix *= cls.from_skew_y_deg(*args)
            else:
                raise ParseError('invalid transform: ' + name)
        return matrix

    def __str__(self):
        return 'matrix(%g %g %g %g %g %g)' % self.abcdef

    def __repr__(self):
        return 'Matrix(%r, %r, %r, %r, %r, %r)' % self.abcdef

    def __mul__(self, other):
        if isinstance(other, Matrix):
            a1, b1, c1, d1, e1, f1 = self.abcdef
            a2, b2, c2, d2, e2, f2 = other.abcdef
            a3 = a1 * a2 + c1 * b2
            b3 = b1 * a2 + d1 * b2
            c3 = a1 * c2 + c1 * d2
            d3 = b1 * c2 + d1 * d2
            e3 = a1 * e2 + c1 * f2 + e1
            f3 = b1 * e2 + d1 * f2 + f1
            return Matrix(a3, b3, c3, d3, e3, f3)
        else:
            return NotImplemented

    def transform(self, shape):
        if isinstance(shape, tuple):
            a, b, c, d, e, f = self.abcdef
            x, y = shape
            return a * x + c * y + e, b * x + d * y + f
        elif isinstance(shape, Shape):
            return shape.transform(self)
        else:
            raise TypeError('invalid shape type')

    @classmethod
    def from_translate(cls, tx, ty=0.0):
        return cls(1.0, 0.0, 0.0, 1.0, tx, ty)

    @classmethod
    def from_scale(cls, sx, sy=None):
        if sy is None:
            sy = sx
        return cls(sx, 0.0, 0.0, sy, 0.0, 0.0)
    
    @classmethod
    def from_rotate_deg(cls, angle, *args):
        if args:
            cx, cy = args
            return (cls.from_translate(cx, cy) * cls.from_rotate_deg(angle) *
                    cls.from_translate(-cx, -cy))
        angle = angle * math.pi / 180.0
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)
        return cls(cos_angle, sin_angle, -sin_angle, cos_angle, 0.0, 0.0)

    @classmethod
    def from_skew_x_deg(cls, angle):
        angle = angle * math.pi / 180.0
        return cls(1.0, 0.0, math.tan(angle), 1.0, 0.0, 0.0)

    @classmethod
    def from_skew_y_deg(cls, angle):
        angle = angle * math.pi / 180.0
        return cls(1.0, math.tan(angle), 0.0, 1.0, 0.0, 0.0)

    @classmethod
    def from_flip_x(cls):
        return cls(-1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    @classmethod
    def from_flip_y(cls):
        return cls(1.0, 0.0, 0.0, -1.0, 0.0, 0.0)

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

    def __nonzero__(self):
        return self.min_x <= self.max_x and self.min_y <= self.max_y

    def __repr__(self):
        return ('Envelope(min_x=%r, min_y=%r, max_x=%r, max_y=%r)' %
                (self.min_x, self.min_y, self.max_x, self.max_y))

    def add(self, shape):
        envelope = shape.envelope
        self.min_x = min(self.min_x, envelope.min_x)
        self.min_y = min(self.min_y, envelope.min_y)
        self.max_x = max(self.max_x, envelope.max_x)
        self.max_y = max(self.max_y, envelope.max_y)

    @property
    def envelope(self):
        return self

    @property
    def width(self):
        return self.max_x - self.min_x

    @property
    def height(self):
        return self.max_y - self.min_y

    @property
    def area(self):
        return self.width * self.height

    @property
    def centroid(self):
        cx = 0.5 * (self.min_x + self.max_x)
        cy = 0.5 * (self.min_y + self.max_y)
        return cx, cy

class Point(Shape):
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

    def transform(self, matrix):
        x1, y1 = matrix.transform(self.p1)
        x2, y2 = matrix.transform(self.p2)
        return Line(x1, y1, x2, y2)

    @property
    def p1(self):
        return self.x1, self.y1

    @property
    def p2(self):
        return self.x2, self.y2

    @property
    def area(self):
        return 0.0

    @property
    def centroid(self):
        cx = 0.5 * (self.x1 + self.x2)
        cy = 0.5 * (self.y1 + self.y2)
        return cx, cy

    @property
    def envelope(self):
        min_x = min(self.x1, self.x2)
        min_y = min(self.y1, self.y2)
        max_x = max(self.x1, self.x2)
        max_y = max(self.y1, self.y2)
        return Envelope(min_x, min_y, max_x, max_y)

class Polyline(Shape):
    def __init__(self, points):
        self.points = list(points)

    def __repr__(self):
        return 'Polyline(%r)' % self.points

    def transform(self, matrix):
        return Polyline(matrix.transform(p) for p in self.points)

    @property
    def area(self):
        return 0.0

    @property
    def envelope(self):
        xs, ys = zip(*self.points)
        return Envelope(min(xs), min(ys), max(xs), max(ys))

class Polygon(Shape):
    def __init__(self, points):
        self.points = list(points)

    def __repr__(self):
        return 'Polygon(%r)' % self.points

    def transform(self, matrix):
        return Polygon(matrix.transform(p) for p in self.points)

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
        return Envelope(min(xs), min(ys), max(xs), max(ys))

    def repair(self, epsilon=0.0):
        def eq(p1, p2):
            x1, y1 = p1
            x2, y2 = p2
            squared_distance = (x2 - x1) ** 2 + (y2 - y1) ** 2
            return squared_distance <= epsilon ** 2
        if len(self.points) >= 2 and eq(self.points[0], self.points[-1]):
            self.points.pop()
        if self.area < 0.0:
            self.points.reverse()

class Circle(Shape):
    def __init__(self, cx, cy, r):
        self.cx, self.cy = cx, cy
        self.r = r

    def __repr__(self):
        return 'Circle(cx=%r, cy=%r, r=%r)' % (self.cx, self.cy, self.r)

    def transform(self, matrix):
        cx, cy = matrix.transform((self.cx, self.cy))
        px, py = matrix.transform((self.cx + self.r, self.cy))
        r = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        return Circle(cx, cy, r)

    @property
    def centroid(self):
        return self.cx, self.cy

    @property
    def envelope(self):
        return Envelope(self.cx - self.r, self.cy - self.r,
                        self.cx + self.r, self.cy + self.r)

class Rect(Shape):
    def __init__(self, x, y, width, height, rx, ry):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rx = rx
        self.ry = ry

class Group(Shape):
    def __init__(self, shapes=[]):
        self.shapes = list(shapes)

    def __len__(self):
        return len(self.shapes)

    def __iter__(self):
        return iter(self.shapes)

    def transform(self, matrix):
        return Group(s.transform(matrix) for s in self)

    @property
    def envelope(self):
        envelope = Envelope()
        for shape in self:
            envelope.add(shape)
        return envelope

    @property
    def area(self):
        return sum(s.area for s in self)

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

    def transform(self, matrix):
        return Group(self.linearize()).transform(matrix)

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

class Element(object):
    def __init__(self):
        self.matrix = Matrix()
        self.attributes = {}
        self.children = []
        self.shapes = []

    def get_envelope(self, matrix):
        envelope = Envelope()
        matrix = matrix * self.matrix
        for shape in self.shapes:
            transformed_shape = matrix.transform(shape)
            envelope.add(transformed_shape)
        for child in self.children:
            child_envelope = child.get_envelope(matrix)
            envelope.add(child_envelope)
        return envelope

    @property
    def envelope(self):
        return self.get_envelope(Matrix())

class Document(object):
    def __init__(self, file):
        xml_document = minidom.parse(file)
        xml_element = xml_document.getElementsByTagName('svg')[0]
        self.elements = {}
        self.root = self._parse_element(xml_element)

    def _parse_element(self, xml_element):
        pinky_element = Element()
        pinky_element.matrix = Matrix(xml_element.getAttribute('transform'))
        if xml_element.hasAttribute('id'):
            id = xml_element.getAttribute('id')
            self.elements[id] = pinky_element
            pinky_element.attributes['id'] = id
        if xml_element.hasAttribute('inkscape:label'):
            pinky_element.attributes['label'] = xml_element.getAttribute('inkscape:label')
        if xml_element.hasAttribute('style'):
            pinky_element.attributes['style'] = xml_element.getAttribute('style')
        if xml_element.nodeName == 'path':
            self._parse_path_element(xml_element, pinky_element)
        elif xml_element.nodeName == 'rect':
            self._parse_rect_element(xml_element, pinky_element)
        for xml_child in xml_element.childNodes:
            if xml_child.nodeType == xml_child.ELEMENT_NODE:
                if xml_child.nodeName == 'title':
                    pinky_element.attributes['title'] = self._parse_element_text(xml_child)
                elif xml_child.nodeName == 'desc':
                    pinky_element.attributes['desc'] = self._parse_element_text(xml_child)
                elif xml_child.nodeName == 'sodipodi:namedview':
                    if xml_child.hasAttribute('pagecolor'):
                        pinky_element.attributes['pagecolor'] = xml_child.getAttribute('pagecolor')
                else:
                    child = self._parse_element(xml_child)
                    pinky_element.children.append(child)
        return pinky_element
    
    def _parse_path_element(self, xml_element, pinky_element):
        if xml_element.getAttribute('sodipodi:type') == 'arc':
            return self._parse_arc_element(xml_element, pinky_element)
        path = Path(xml_element.getAttribute('d'))
        pinky_element.shapes.append(path)
    
    def _parse_arc_element(self, xml_element, pinky_element):
        cx = float(xml_element.getAttribute('sodipodi:cx') or '0')
        cy = float(xml_element.getAttribute('sodipodi:cy') or '0')
        rx = float(xml_element.getAttribute('sodipodi:rx'))
        ry = float(xml_element.getAttribute('sodipodi:ry'))
        circle = Circle(cx, cy, (rx + ry) / 2.0)
        pinky_element.shapes.append(circle)
    
    def _parse_rect_element(self, xml_element, pinky_element):
        x = float(xml_element.getAttribute('x') or '0')
        y = float(xml_element.getAttribute('y') or '0')
        width = float(xml_element.getAttribute('width'))
        height = float(xml_element.getAttribute('height'))
        points = [(x, y), (x + width, y),
                  (x + width, y + height), (x, y + height)]
        polygon = Polygon(points)
        pinky_element.shapes.append(polygon)

    def _parse_element_text(self, xml_element):
        text = ''.join(child.nodeValue for child in xml_element.childNodes
                       if child.nodeType == child.TEXT_NODE)
        text = ' '.join(text.split())
        return text
