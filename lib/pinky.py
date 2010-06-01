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

"""An SVG loader for rapid game prototyping in Python.

Pinky tries to make it easy to use Inkscape as a game editor, without
getting in your way.

See: U{http://github.com/elemel/pinky}
"""

from itertools import chain
import math
import re
from xml.dom import minidom

class ParseError(Exception):
    """A parse error."""
    pass

class Color(object):
    """An RGB color with integer components in the [0, 255] range."""

    # http://www.w3.org/TR/SVG/types.html#ColorKeywords
    _color_keywords = dict(
        aliceblue=(240, 248, 255),
        antiquewhite=(250, 235, 215),
        aqua=(0, 255, 255),
        aquamarine=(127, 255, 212),
        azure=(240, 255, 255),
        beige=(245, 245, 220),
        bisque=(255, 228, 196),
        black=(0, 0, 0),
        blanchedalmond=(255, 235, 205),
        blue=(0, 0, 255),
        blueviolet=(138, 43, 226),
        brown=(165, 42, 42),
        burlywood=(222, 184, 135),
        cadetblue=(95, 158, 160),
        chartreuse=(127, 255, 0),
        chocolate=(210, 105, 30),
        coral=(255, 127, 80),
        cornflowerblue=(100, 149, 237),
        cornsilk=(255, 248, 220),
        crimson=(220, 20, 60),
        cyan=(0, 255, 255),
        darkblue=(0, 0, 139),
        darkcyan=(0, 139, 139),
        darkgoldenrod=(184, 134, 11),
        darkgray=(169, 169, 169),
        darkgreen=(0, 100, 0),
        darkgrey=(169, 169, 169),
        darkkhaki=(189, 183, 107),
        darkmagenta=(139, 0, 139),
        darkolivegreen=(85, 107, 47),
        darkorange=(255, 140, 0),
        darkorchid=(153, 50, 204),
        darkred=(139, 0, 0),
        darksalmon=(233, 150, 122),
        darkseagreen=(143, 188, 143),
        darkslateblue=(72, 61, 139),
        darkslategray=(47, 79, 79),
        darkslategrey=(47, 79, 79),
        darkturquoise=(0, 206, 209),
        darkviolet=(148, 0, 211),
        deeppink=(255, 20, 147),
        deepskyblue=(0, 191, 255),
        dimgray=(105, 105, 105),
        dimgrey=(105, 105, 105),
        dodgerblue=(30, 144, 255),
        firebrick=(178, 34, 34),
        floralwhite=(255, 250, 240),
        forestgreen=(34, 139, 34),
        fuchsia=(255, 0, 255),
        gainsboro=(220, 220, 220),
        ghostwhite=(248, 248, 255),
        gold=(255, 215, 0),
        goldenrod=(218, 165, 32),
        gray=(128, 128, 128),
        grey=(128, 128, 128),
        green=(0, 128, 0),
        greenyellow=(173, 255, 47),
        honeydew=(240, 255, 240),
        hotpink=(255, 105, 180),
        indianred=(205, 92, 92),
        indigo=(75, 0, 130),
        ivory=(255, 255, 240),
        khaki=(240, 230, 140),
        lavender=(230, 230, 250),
        lavenderblush=(255, 240, 245),
        lawngreen=(124, 252, 0),
        lemonchiffon=(255, 250, 205),
        lightblue=(173, 216, 230),
        lightcoral=(240, 128, 128),
        lightcyan=(224, 255, 255),
        lightgoldenrodyellow=(250, 250, 210),
        lightgray=(211, 211, 211),
        lightgreen=(144, 238, 144),
        lightgrey=(211, 211, 211),
        lightpink=(255, 182, 193),
        lightsalmon=(255, 160, 122),
        lightseagreen=(32, 178, 170),
        lightskyblue=(135, 206, 250),
        lightslategray=(119, 136, 153),
        lightslategrey=(119, 136, 153),
        lightsteelblue=(176, 196, 222),
        lightyellow=(255, 255, 224),
        lime=(0, 255, 0),
        limegreen=(50, 205, 50),
        linen=(250, 240, 230),
        magenta=(255, 0, 255),
        maroon=(128, 0, 0),
        mediumaquamarine=(102, 205, 170),
        mediumblue=(0, 0, 205),
        mediumorchid=(186, 85, 211),
        mediumpurple=(147, 112, 219),
        mediumseagreen=(60, 179, 113),
        mediumslateblue=(123, 104, 238),
        mediumspringgreen=(0, 250, 154),
        mediumturquoise=(72, 209, 204),
        mediumvioletred=(199, 21, 133),
        midnightblue=(25, 25, 112),
        mintcream=(245, 255, 250),
        mistyrose=(255, 228, 225),
        moccasin=(255, 228, 181),
        navajowhite=(255, 222, 173),
        navy=(0, 0, 128),
        oldlace=(253, 245, 230),
        olive=(128, 128, 0),
        olivedrab=(107, 142, 35),
        orange=(255, 165, 0),
        orangered=(255, 69, 0),
        orchid=(218, 112, 214),
        palegoldenrod=(238, 232, 170),
        palegreen=(152, 251, 152),
        paleturquoise=(175, 238, 238),
        palevioletred=(219, 112, 147),
        papayawhip=(255, 239, 213),
        peachpuff=(255, 218, 185),
        peru=(205, 133, 63),
        pink=(255, 192, 203),
        plum=(221, 160, 221),
        powderblue=(176, 224, 230),
        purple=(128, 0, 128),
        red=(255, 0, 0),
        rosybrown=(188, 143, 143),
        royalblue=(65, 105, 225),
        saddlebrown=(139, 69, 19),
        salmon=(250, 128, 114),
        sandybrown=(244, 164, 96),
        seagreen=(46, 139, 87),
        seashell=(255, 245, 238),
        sienna=(160, 82, 45),
        silver=(192, 192, 192),
        skyblue=(135, 206, 235),
        slateblue=(106, 90, 205),
        slategray=(112, 128, 144),
        slategrey=(112, 128, 144),
        snow=(255, 250, 250),
        springgreen=(0, 255, 127),
        steelblue=(70, 130, 180),
        tan=(210, 180, 140),
        teal=(0, 128, 128),
        thistle=(216, 191, 216),
        tomato=(255, 99, 71),
        turquoise=(64, 224, 208),
        violet=(238, 130, 238),
        wheat=(245, 222, 179),
        white=(255, 255, 255),
        whitesmoke=(245, 245, 245),
        yellow=(255, 255, 0),
        yellowgreen=(154, 205, 50),
    )

    def __init__(self, red=0, green=0, blue=0):
        self.red = red
        self.green = green
        self.blue = blue

    def __iter__(self):
        yield self.red
        yield self.green
        yield self.blue

    def __str__(self):
        return '#%02x%02x%02x' % (self.red, self.green, self.blue)

    def __repr__(self):
        return 'Color(%i, %i, %i)' % (self.red, self.green, self.blue)

    @classmethod
    def parse(cls, color_str):
        lower_color_str = color_str.lower()
        if lower_color_str == 'none':
            return None
        if lower_color_str in cls._color_keywords:
            red, green, blue = cls._color_keywords[lower_color_str]
        elif len(color_str) == 4 and color_str[0] == '#':
            red = int(color_str[1], 16) * 17
            green = int(color_str[2], 16) * 17
            blue = int(color_str[3], 16) * 17
        elif len(color_str) == 7 and color_str[0] == '#':
            red = int(color_str[1:3], 16)
            green = int(color_str[3:5], 16)
            blue = int(color_str[5:7], 16)
        else:
            raise ParseError('invalid color: ' + color_str)
        return cls(red, green, blue)

    @property
    def float_components(self):
        red = float(self.red) / 255.0
        green = float(self.green) / 255.0
        blue = float(self.blue) / 255.0
        return red, green, blue

def parse_style(style_str):
    """Parse a CSS attribute list into a dictionary."""
    lines = (l.strip() for l in style_str.split(';'))
    pairs = (l.split(':') for l in lines if l)
    return dict((k.strip(), v.strip()) for k, v in pairs)

class Matrix(object):
    """A transformation matrix."""

    def __init__(self, a=1.0, b=0.0, c=0.0, d=1.0, e=0.0, f=0.0):
        """Initialize a matrix from the given components."""
        assert all(isinstance(x, float) for x in (a, b, c, d, e, f))
        self.abcdef = a, b, c, d, e, f

    @classmethod
    def parse(cls, transform_list_str):
        matrix = Matrix()
        for transform_str in transform_list_str.replace(',', ' ').split(')')[:-1]:
            name, args = transform_str.strip().split('(')
            name = name.rstrip()
            args = map(float, args.split())
            if name == 'matrix':
                matrix *= cls(*args)
            elif name == 'translate':
                matrix *= cls.create_translate(*args)
            elif name == 'scale':
                matrix *= cls.create_scale(*args)
            elif name == 'rotate':
                matrix *= cls.create_rotate(*args)
            elif name == 'skewX':
                matrix *= cls.create_skew_x(*args)
            elif name == 'skewY':
                matrix *= cls.create_skew_y(*args)
            else:
                raise ParseError('invalid transform: ' + name)
        return matrix

    def __str__(self):
        """Get an SVG representation of the matrix."""
        return 'matrix(%g %g %g %g %g %g)' % self.abcdef

    def __repr__(self):
        """Get a Python representation of the matrix."""
        return 'Matrix(%r, %r, %r, %r, %r, %r)' % self.abcdef

    def __mul__(self, other):
        """Multiply with another matrix."""
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

    def transform_point(self, x, y):
        """Get a transformed copy of a point."""
        a, b, c, d, e, f = self.abcdef
        return a * x + c * y + e, b * x + d * y + f

    def transform_shape(self, shape):
        """Get a transformed copy of a shape."""
        return shape.transform(self)

    @classmethod
    def create_translate(cls, tx, ty=0.0):
        """Create a translation matrix."""
        return cls(1.0, 0.0, 0.0, 1.0, tx, ty)

    @classmethod
    def create_scale(cls, sx, sy=None):
        """Create a scale matrix."""
        if sy is None:
            sy = sx
        return cls(sx, 0.0, 0.0, sy, 0.0, 0.0)
    
    @classmethod
    def create_rotate(cls, angle, cx=None, cy=None):
        """Create a rotation matrix."""
        if cx is not None and cy is not None:
            return (cls.create_translate(cx, cy) * cls.create_rotate(angle) *
                    cls.create_translate(-cx, -cy))
        angle_rad = angle * math.pi / 180.0
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        return cls(cos_angle, sin_angle, -sin_angle, cos_angle, 0.0, 0.0)

    @classmethod
    def create_skew_x(cls, angle):
        """Create a horizontal skew matrix."""
        angle_rad = angle * math.pi / 180.0
        return cls(1.0, 0.0, math.tan(angle_rad), 1.0, 0.0, 0.0)

    @classmethod
    def create_skew_y(cls, angle):
        """Create a vertical skew matrix."""
        angle_rad = angle * math.pi / 180.0
        return cls(1.0, math.tan(angle_rad), 0.0, 1.0, 0.0, 0.0)

    @classmethod
    def create_flip_x(cls):
        """Create a horizontal flip matrix."""
        return cls(-1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

    @classmethod
    def create_flip_y(cls):
        """Create a vertical flip matrix."""
        return cls(1.0, 0.0, 0.0, -1.0, 0.0, 0.0)

class Shape(object):
    """The base class for shapes."""

    @property
    def bounding_box(self):
        """The bounding box of the shape."""
        raise NotImplementedError()

    @property
    def area(self):
        """The area of the shape."""
        raise NotImplementedError()

    @property
    def centroid(self):
        """The mass center of the shape."""
        raise NotImplementedError()

    def transform(self, matrix):
        """Get a transformed copy of the shape."""
        raise NotImplementedError()

    def get_bounding_box(self, matrix):
        """Get the bounding box of the shape after applying the given
        transformation matrix."""
        return self.transform(matrix).bounding_box

class BoundingBox(Shape):
    """An axis-aligned rectangle for representing shape boundaries.

    See: U{http://www.w3.org/TR/SVG/coords.html#ObjectBoundingBox}
    """

    def __init__(self, min_x=float('inf'), min_y=float('inf'),
                 max_x=float('-inf'), max_y=float('-inf')):
        """Initialize a bounding box from the given minima and maxima."""
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

    def __nonzero__(self):
        """Is the bounding box non-empty?"""
        return self.min_x <= self.max_x and self.min_y <= self.max_y

    def __repr__(self):
        return ('BoundingBox(min_x=%r, min_y=%r, max_x=%r, max_y=%r)' %
                (self.min_x, self.min_y, self.max_x, self.max_y))

    def add_point(self, x, y, matrix=None):
        """Expand the bounding box to contain the given point."""
        if matrix is not None:
            x, y = matrix.transform_point(x, y)
        self.min_x = min(self.min_x, x)
        self.min_y = min(self.min_y, y)
        self.max_x = max(self.max_x, x)
        self.max_y = max(self.max_y, y)

    def add_shape(self, shape, matrix=None):
        """Expand the bounding box to contain the given shape."""
        if isinstance(shape, tuple):
            if matrix is None:
                x, y = shape
            else:
                x, y = matrix.transform_point(shape)
            self.min_x = min(self.min_x, x)
            self.min_y = min(self.min_y, y)
            self.max_x = max(self.max_x, x)
            self.max_y = max(self.max_y, y)
        else:
            if matrix is None:
                bounding_box = shape.bounding_box
            else:
                bounding_box = shape.get_bounding_box(matrix)
            self.min_x = min(self.min_x, bounding_box.min_x)
            self.min_y = min(self.min_y, bounding_box.min_y)
            self.max_x = max(self.max_x, bounding_box.max_x)
            self.max_y = max(self.max_y, bounding_box.max_y)

    def intersects(self, other):
        """Do the two bounding boxes intersect?"""
        return (self.min_x < other.max_x and other.min_x < self.max_x and
                self.min_y < other.max_y and other.min_y < self.max_y)

    @property
    def bounding_box(self):
        """The bounding box itself."""
        return self

    @property
    def width(self):
        """The width of the bounding box."""
        return self.max_x - self.min_x

    @property
    def height(self):
        """The height of the bounding box."""
        return self.max_y - self.min_y

    @property
    def area(self):
        return self.width * self.height

    @property
    def centroid(self):
        cx = 0.5 * (self.min_x + self.max_x)
        cy = 0.5 * (self.min_y + self.max_y)
        return cx, cy

    @classmethod
    def from_points(cls, points, matrix=None):
        bounding_box = cls()
        for x, y in points:
            bounding_box.add_point(x, y, matrix)
        return bounding_box

    @classmethod
    def from_shapes(cls, shapes, matrix=None):
        bounding_box = cls()
        for shape in shapes:
            bounding_box.add_shape(shape, matrix)
        return bounding_box

class Line(Shape):
    """A line."""

    def __init__(self, x1, y1, x2, y2):
        """Initialize a line from two points."""
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2

    def __repr__(self):
        return ('Line(x1=%r, y1=%r, x2=%r, y2=%r)' %
                (self.x1, self.y1, self.x2, self.y2))

    def transform(self, matrix):
        x1, y1 = matrix.transform_point(self.x1, self.y1)
        x2, y2 = matrix.transform_point(self.x2, self.y2)
        return Line(x1, y1, x2, y2)

    @property
    def p1(self):
        """The first point."""
        return self.x1, self.y1

    @property
    def p2(self):
        """The second point."""
        return self.x2, self.y2

    @property
    def area(self):
        """The area of a line is always zero."""
        return 0.0

    @property
    def centroid(self):
        """The center point of the line."""
        cx = 0.5 * (self.x1 + self.x2)
        cy = 0.5 * (self.y1 + self.y2)
        return cx, cy

    @property
    def bounding_box(self):
        min_x = min(self.x1, self.x2)
        min_y = min(self.y1, self.y2)
        max_x = max(self.x1, self.x2)
        max_y = max(self.y1, self.y2)
        return BoundingBox(min_x, min_y, max_x, max_y)

class Polyline(Shape):
    """A line strip."""

    def __init__(self, points):
        self.points = list(points)

    def __repr__(self):
        return 'Polyline(%r)' % self.points

    def transform(self, matrix):
        return Polyline(matrix.transform_point(x, y) for x, y in self.points)

    @property
    def area(self):
        return 0.0

    @property
    def bounding_box(self):
        xs, ys = zip(*self.points)
        return BoundingBox(min(xs), min(ys), max(xs), max(ys))

class Polygon(Shape):
    """A polygon."""

    def __init__(self, points):
        self.points = list(points)

    def __repr__(self):
        return 'Polygon(%r)' % self.points

    def transform(self, matrix):
        return Polygon(matrix.transform_point(x, y) for x, y in self.points)

    @property
    def area(self):
        """The area of the polygon.

        See: U{http://mathworld.wolfram.com/PolygonArea.html}
        """
        area = 0.0
        for i in xrange(len(self.points)):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i + 1) % len(self.points)]
            area += x1 * y2 - x2 * y1
        return area / 2.0

    @property
    def bounding_box(self):
        xs, ys = zip(*self.points)
        return BoundingBox(min(xs), min(ys), max(xs), max(ys))

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
    """A circle."""

    def __init__(self, cx, cy, r):
        """Initialize a circle from the given center point and radius."""
        self.cx, self.cy = cx, cy
        self.r = r

    def __repr__(self):
        return 'Circle(cx=%r, cy=%r, r=%r)' % (self.cx, self.cy, self.r)

    def transform(self, matrix):
        """Get a transformed copy of the circle.

        The given transform should only translate, scale, and rotate the
        circle. The absolute values of the x scale and y scale should be equal.
        """
        cx, cy = matrix.transform_point(self.cx, self.cy)
        px, py = matrix.transform_point(self.cx + self.r, self.cy)
        r = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        return Circle(cx, cy, r)

    @property
    def centroid(self):
        return self.cx, self.cy

    @property
    def bounding_box(self):
        return BoundingBox(self.cx - self.r, self.cy - self.r,
                           self.cx + self.r, self.cy + self.r)

class Rect(Shape):
    """An axis-aligned rectangle with rounded corners."""

    def __init__(self, x, y, width, height, rx, ry):
        """Initialize a rectangle from the given position, dimensions, and
        corner radii.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rx = rx
        self.ry = ry

    def __repr__(self):
        return ('Rect(x=%r, y=%r, width=%r, height=%r, rx=%r, ry=%r)' %
                (self.x, self.y, self.width, self.height, self.rx, self.ry))

    @property
    def centroid(self):
        return self.x + 0.5 * self.width, self.y + 0.5 * self.height

    @property
    def bounding_box(self):
        return BoundingBox(self.x, self.y, self.x + self.width,
                           self.y + self.height)

class Command(object):
    """The base class for path commands."""

    __slots__ = ()

    def __init__(self, *args):
        """Initialize a command from the given arguments."""
        for name, value in zip(self.__slots__, args):
            setattr(self, name, value)

    def __str__(self):
        """Get an SVG representation of the command."""
        return '%s %s' % (self.letter,
                          ' '.join('%g' % getattr(self, s)
                                   for s in self.__slots__))
 
    def __repr__(self):
        """Get a Python representation of the command."""
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join('%s=%r' % (s, getattr(self, s))
                                     for s in self.__slots__))

    def transform(self, matrix):
        """Get a transformed copy of the command."""
        control_points = [matrix.transform_point(x, y)
                          for x, y in self.control_points]
        return self.__class__(*chain(*control_points))

    @property
    def endpoint(self):
        """The endpoint of the command."""
        return (self.x, self.y) if self.__slots__ else None

    @property
    def control_points(self):
        """The control points of the command."""
        args = [getattr(self, s) for s in self.__slots__]
        return zip(args[::2], args[1::2])

class Moveto(Command):
    """A moveto command."""

    letter = 'M'
    __slots__ = 'x', 'y'

class Closepath(Command):
    """A closepath command."""

    letter = 'Z'
    __slots__ = ()

class Lineto(Command):
    """A lineto command."""

    letter = 'L'
    __slots__ = 'x', 'y'

class Curveto(Command):
    """A curveto command."""

    letter = 'C'
    __slots__ = 'x1', 'y1', 'x2', 'y2', 'x', 'y'

class SmoothCurveto(Command):
    """A smooth curveto command."""

    letter = 'S'
    __slots__ = 'x2', 'y2', 'x', 'y'

class QuadraticBezierCurveto(Command):
    """A quadratic Bezier curveto command."""

    letter = 'Q'
    __slots__ = 'x1', 'y1', 'x', 'y'

class SmoothQuadraticBezierCurveto(Command):
    """A smooth quadratic Bezier curveto command."""

    letter = 'T'
    __slots__ = 'x', 'y'

class EllipticalArc(Command):
    """An elliptical arc command."""

    letter = 'A'
    __slots__ = 'rx', 'ry', 'rotation', 'large', 'sweep', 'x', 'y'

    # TODO: Proper implementation.
    def transform(self, matrix):
        rx = self.rx
        ry = self.ry
        rotation = self.rotation
        large = self.large
        sweep = self.sweep
        x, y = matrix.transform_point(self.x, self.y)
        return EllipticalArc(rx, ry, rotation, large, sweep, x, y)

    # TODO: Proper implementation.
    @property
    def control_points(self):
        return [(self.x, self.y)]

class Subpath(Shape):
    """A subpath."""

    def __init__(self, commands):
        self.commands = list(commands)
        assert all(isinstance(c, Command) for c in self.commands)

    def transform(self, matrix):
        return Subpath(c.transform(matrix) for c in self.commands)

    def get_basic_shape(self):
        """Convert the subpath to a basic shape."""
        if self.closed:
            return Polygon(c.endpoint for c in self.commands[:-1])
        elif len(self.commands) == 2:
            x1, y1 = self.commands[0].endpoint
            x2, y2 = self.commands[1].endpoint
            return Line(x1, y1, x2, y2)
        else:
            return Polyline(c.endpoint for c in self.commands)

    @property
    def closed(self):
        return self.commands and self.commands[-1].endpoint is None

class Path(Shape):
    """A path."""

    _scanner = re.Scanner([
        ('[MmZzLlHhVvCcSsQqTtAa]', (lambda s, t: t)),
        ('[-+0-9.Ee]+', (lambda s, t: float(t))),
        ('[, \t\r\n]+', None),
    ])

    _arg_counts = dict(M=2, Z=0, L=2, H=1, V=1, C=6, S=4, Q=4, T=2, A=7,
                       m=2, z=0, l=2, h=1, v=1, c=6, s=4, q=4, t=2, a=7)
 
    _command_classes = dict(M=Moveto, Z=Closepath, L=Lineto, C=Curveto,
                            S=SmoothCurveto, Q=QuadraticBezierCurveto,
                            T=SmoothQuadraticBezierCurveto, A=EllipticalArc)

    def __init__(self, subpaths):
        self.subpaths = list(subpaths)
        assert all(isinstance(s, Subpath) for s in self.subpaths)

    def __str__(self):
        """Get an SVG representation of the path."""
        return ' '.join(str(c) for c in self.commands)

    def transform(self, matrix):
        return Path(s.transform(matrix) for s in self.subpaths)

    @property
    def bounding_box(self):
        control_points = (c.control_points for c in self.commands)
        return BoundingBox.from_points(chain(*control_points))

    @property
    def commands(self):
        commands = (s.commands for s in self.subpaths)
        return chain(*commands)

    @classmethod
    def parse(cls, path_str):
        command_tuples = cls._parse_commands(path_str)
        command_tuples = cls._split_polycommands(command_tuples)
        command_tuples = cls._to_absolute_commands(command_tuples)
        commands = []
        for command_tuple in command_tuples:
            name, args = command_tuple[0], command_tuple[1:]
            command_class = cls._command_classes[name]
            command = command_class(*args)
            commands.append(command)
        subpaths = cls._split_subpaths(commands)
        return Path(Subpath(s) for s in subpaths)

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

    @classmethod
    def _split_subpaths(self, commands):
        subpath = []
        for command in commands:
            if subpath and isinstance(command, Moveto):
                yield subpath
                subpath = []
            subpath.append(command)
        if subpath:
            yield subpath

    def get_basic_shapes(self):
        """Convert the path to basic shapes."""
        return [s.get_basic_shape() for s in self.subpaths]

class Element(object):
    """An element."""

    def __init__(self):
        """Initialize an element."""

        self.matrix = Matrix()
        """The local transformation matrix of the element."""

        self.attributes = {}
        """The direct attributes of the element."""

        self.children = []
        """The children of the element in the element tree."""

        self.shapes = []
        """The shapes immediately attached to the element."""

    def get_bounding_box(self, matrix):
        """Get the bounding box of the element after applying the given
        transformation matrix."""
        matrix = matrix * self.matrix
        bounding_box = BoundingBox.from_shapes(self.shapes, matrix)
        for child in self.children:
            child_bounding_box = child.get_bounding_box(matrix)
            bounding_box.add_shape(child_bounding_box)
        return bounding_box

    @property
    def bounding_box(self):
        """The bounding box of the element."""
        return self.get_bounding_box(Matrix())

class Document(object):
    """A document."""

    def __init__(self, file):
        """Initialize a document from the given SVG file."""
        xml_document = minidom.parse(file)
        xml_element = xml_document.getElementsByTagName('svg')[0]
        self.elements = {}
        self.root = self._parse_element(xml_element)

    def _parse_element(self, xml_element):
        pinky_element = Element()
        pinky_element.matrix = Matrix.parse(xml_element.getAttribute('transform'))
        if xml_element.hasAttribute('id'):
            id = xml_element.getAttribute('id')
            self.elements[id] = pinky_element
            pinky_element.attributes['id'] = id
        if xml_element.hasAttribute('inkscape:label'):
            pinky_element.attributes['label'] = xml_element.getAttribute('inkscape:label')
        if xml_element.hasAttribute('style'):
            pinky_element.attributes['style'] = xml_element.getAttribute('style')
        if xml_element.hasAttribute('fill'):
            pinky_element.attributes['fill'] = xml_element.getAttribute('fill')
        if xml_element.hasAttribute('stroke'):
            pinky_element.attributes['stroke'] = xml_element.getAttribute('stroke')
        if xml_element.nodeName == 'path':
            self._parse_path_element(xml_element, pinky_element)
        elif xml_element.nodeName == 'rect':
            self._parse_rect_element(xml_element, pinky_element)
        elif xml_element.nodeName == 'circle':
            self._parse_circle_element(xml_element, pinky_element)
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
        path = Path.parse(xml_element.getAttribute('d'))
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

    def _parse_circle_element(self, xml_element, pinky_element):
        cx = float(xml_element.getAttribute('cx') or '0')
        cy = float(xml_element.getAttribute('cy') or '0')
        r = float(xml_element.getAttribute('r'))
        circle = Circle(cx, cy, r)
        pinky_element.shapes.append(circle)

    def _parse_element_text(self, xml_element):
        text = ''.join(child.nodeValue for child in xml_element.childNodes
                       if child.nodeType == child.TEXT_NODE)
        text = ' '.join(text.split())
        return text
