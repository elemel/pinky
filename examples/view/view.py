from Box2D import *
import math
import pinky
import pyglet
from pyglet.gl import *
import sys

def draw_line(x1, y1, x2, y2, stroke):
    if stroke is not None:
        glColor3f(*stroke)
        glBegin(GL_LINES)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glEnd()

def draw_polygon(vertices, fill, stroke):
    if fill is not None:
        glColor3f(*fill)
        glBegin(GL_POLYGON)
        for x, y in vertices:
            glVertex2f(x, y)
        glEnd()
    if stroke is not None:
        glColor3f(*stroke)
        glBegin(GL_LINE_LOOP)
        for x, y in vertices:
            glVertex2f(x, y)
        glEnd()

def draw_circle(x, y, radius, fill, stroke, vertex_count=32):
    vertices = []
    for i in xrange(vertex_count):
        angle = 2.0 * math.pi * float(i) / float(vertex_count)
        vertex = (x + radius * math.cos(angle),
                  y + radius * math.sin(angle))
        vertices.append(vertex)
    draw_polygon(vertices, fill, stroke)

def draw_rect(x, y, width, height, fill, stroke):
    vertices = []
    vertices.append((x, y))
    vertices.append((x + width, y))
    vertices.append((x + width, y + height))
    vertices.append((x, y + height))
    draw_polygon(vertices, fill, stroke)

class GameEngine(object):
    def __init__(self, document, width, height):
        self.document = document
        self.width = width
        self.height = height
        self.shapes = []
        self.load_shapes(self.document.root, pinky.Matrix())
        self.init_camera()
        page_color_str = self.document.root.attributes.get('pagecolor', 'none')
        page_color = pinky.parse_float_color(page_color_str)
        if page_color is None:
            self.clear_color = 1.0, 1.0, 1.0, 1.0
        else:
            page_red, page_green, page_blue = page_color
            self.clear_color = page_red, page_green, page_blue, 1.0

    def init_camera(self):
        envelope = self.document.root.envelope
        self.camera_x, self.camera_y = envelope.centroid
        scale_x = float(self.width) / envelope.width
        scale_y = float(self.height) / envelope.height
        self.camera_scale = 0.8 * min(scale_x, scale_y)

    def load_shapes(self, element, matrix):
        attributes = dict(element.attributes)
        attributes.update(pinky.parse_style(attributes.pop('style', '')))
        # attributes.update(pinky.parse_style(attributes.pop('desc', '')))
        matrix = matrix * element.matrix
        fill = pinky.parse_float_color(attributes.get('fill', 'none'))
        stroke = pinky.parse_float_color(attributes.get('stroke', 'none'))
        for shape in element.shapes:
            self.add_shape(shape, matrix, fill, stroke)
        for child in element.children:
            self.load_shapes(child, matrix)

    def add_shape(self, shape, matrix, fill, stroke):
        if isinstance(shape, pinky.Path):
            shapes = shape.linearize()
        else:
            shapes = [shape]
        for shape in shapes:
            transformed_shape = matrix.transform(shape)
            self.shapes.append((transformed_shape, fill, stroke))

    def on_draw(self):
        glClearColor(*self.clear_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        glTranslatef(self.width // 2, self.height // 2, 0)
        glScalef(self.camera_scale, self.camera_scale, self.camera_scale)
        glTranslatef(-self.camera_x, -self.camera_y, 0)
        for shape, fill, stroke in self.shapes:
            if isinstance(shape, pinky.Line):
                draw_line(shape.x1, shape.y1, shape.x2, shape.y2, stroke)
            elif isinstance(shape, pinky.Polygon):
                draw_polygon(shape.points, fill, stroke)
            elif isinstance(shape, pinky.Circle):
                draw_circle(shape.cx, shape.cy, shape.r, fill, stroke)
            elif isinstance(shape, pinky.Rect):
                draw_rect(shape.x, shape.y, shape.width, shape.height, fill,
                          stroke)
        glPopMatrix()

class MyWindow(pyglet.window.Window):
    def __init__(self, document, **kwargs):
        super(MyWindow, self).__init__(**kwargs)
        if self.fullscreen:
            self.set_exclusive_mouse()
            self.set_exclusive_keyboard()
        self.game_engine = GameEngine(document, self.width, self.height)

    def on_draw(self):
        self.game_engine.on_draw()

def main():
    if len(sys.argv) != 2:
        sys.stderr.write('usage: python view.py <svg>\n')
        sys.exit(1)
    document = pinky.Document(sys.argv[1])
    document.root.matrix = pinky.Matrix.from_flip_y()
    config = pyglet.gl.Config(double_buffer=True, sample_buffers=1, samples=4,
                              depth_size=8)
    window = MyWindow(document=document, fullscreen=True, config=config)
    pyglet.app.run()

if __name__ == '__main__':
    main()
