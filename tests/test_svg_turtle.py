from pathlib import Path

import pytest
from cairosvg import svg2png
from space_tracer import LiveImage, LiveImageDiffer, LivePainter
from svgwrite import Drawing

from svg_turtle import SvgTurtle


class LiveSvg(LiveImage):
    def __init__(self, svg: str):
        self.svg = svg

    def convert_to_png(self) -> bytes:
        original_png = svg2png(self.svg)
        return original_png

    # This override can be removed after bug is fixed:
    # https://github.com/donkirkby/live-py-plugin/issues/360
    def convert_to_painter(self) -> LivePainter:
        painter = super().convert_to_painter()
        # noinspection PyUnresolvedReferences
        image = painter.image
        if 'A' not in image.getbands():
            image.putalpha(120)
        return painter


@pytest.fixture(scope='session')
def session_image_differ():
    """ Track all images compared in a session. """
    diffs_path = Path(__file__).parent / 'image_diffs'
    differ = LiveImageDiffer(diffs_path)
    yield differ
    differ.remove_common_prefix()


@pytest.fixture
def image_differ(request, session_image_differ):
    """ Pass the current request to the session image differ. """
    session_image_differ.request = request
    yield session_image_differ


def test_line(image_differ):
    expected = Drawing(size=(300, 200))
    expected.add(expected.line((150.5, 100.5),
                               (250.5, 100.5),
                               stroke='#000000',
                               stroke_linecap='round'))
    expected_svg = LiveSvg(expected.tostring())

    t = SvgTurtle(300, 200)
    t.forward(100)
    svg = LiveSvg(t.to_svg())

    image_differ.assert_equal(svg, expected_svg)


def test_init_bgcolor(image_differ):
    expected = Drawing(size=(300, 200))
    expected.add(expected.rect(fill='#808080', size=('100%', '100%')))
    expected_svg = LiveSvg(expected.tostring())

    t = SvgTurtle(300, 200)
    t.getscreen().bgcolor('grey50')
    svg = LiveSvg(t.to_svg())

    image_differ.assert_equal(svg, expected_svg)


def test_fill(image_differ):
    expected = Drawing(size=(300, 200))
    expected.add(expected.polygon(points=[(150.5, 100.5),
                                          (200.5, 100.5),
                                          (200.5, 150.5),
                                          (150.5, 150.5)],
                                  fill='#0000ff'))
    expected.add(expected.polyline(points=[(150.5, 100.5),
                                           (200.5, 100.5),
                                           (200.5, 150.5),
                                           (150.5, 150.5),
                                           (150.5, 100.5)],
                                   stroke='#000000',
                                   fill='none',
                                   stroke_linecap='round'))
    expected_svg = LiveSvg(expected.tostring())

    t = SvgTurtle(300, 200)
    t.fillcolor('blue')
    t.begin_fill()
    for _ in range(4):
        t.forward(50)
        t.right(90)
    t.end_fill()

    svg = LiveSvg(t.to_svg())

    image_differ.assert_equal(svg, expected_svg)


def test_dot(image_differ):
    expected = Drawing(size=(300, 200))
    expected.add(expected.line((150.5, 100.5),
                               (150.5, 100.5),
                               stroke_width=20,
                               stroke_linecap='round',
                               stroke='#000000'))
    expected_svg = LiveSvg(expected.tostring())

    t = SvgTurtle(300, 200)
    t.dot(20)

    svg = LiveSvg(t.to_svg())

    image_differ.assert_equal(svg, expected_svg)


def test_colormode(image_differ):
    expected = Drawing(size=(300, 200))
    expected.add(expected.line((150.5, 100.5),
                               (150.5, 100.5),
                               stroke_width=20,
                               stroke_linecap='round',
                               stroke='#007FFF'))
    expected_svg = LiveSvg(expected.tostring())

    t = SvgTurtle(300, 200)
    t.getscreen().colormode(255)
    t.dot(20, (0, 127, 255))

    svg = LiveSvg(t.to_svg())

    image_differ.assert_equal(svg, expected_svg)


def test_save_as(tmp_path):
    expected = SvgTurtle(300, 200)
    expected.forward(100)
    header = '<?xml version="1.0" encoding="utf-8" ?>\n'
    expected_svg = header + expected.to_svg()

    svg_path = tmp_path / 'example.svg'
    t = SvgTurtle(300, 200)
    t.forward(100)
    t.save_as(svg_path)

    assert svg_path.read_text() == expected_svg


def test_stamp(image_differ):
    expected = Drawing(size=(300, 200))
    expected.add(expected.polygon(points=[(150.5, 100.5),
                                          (145.5, 91.5),
                                          (150.5, 93.5),
                                          (155.5, 91.5)],
                                  stroke='black',
                                  stroke_width=1,
                                  fill='#0000ff'))
    expected_svg = LiveSvg(expected.tostring())

    t = SvgTurtle(300, 200)
    t.fillcolor('blue')
    t.right(90)
    t.stamp()

    svg = LiveSvg(t.to_svg())

    image_differ.assert_equal(svg, expected_svg)


def test_write(image_differ):
    expected = Drawing(size=(300, 200))
    expected.add(expected.text('Hello, World!',
                               insert=(149.5, 96.9),
                               text_anchor='start',
                               style='font-family: Arial; font-size: 13.2;'))
    expected_svg = LiveSvg(expected.tostring())

    t = SvgTurtle(300, 200)
    t.write('Hello, World!')

    svg = LiveSvg(t.to_svg())

    image_differ.assert_equal(svg, expected_svg)


def test_undo(image_differ):
    expected = Drawing(size=(300, 200))
    expected.add(expected.line((150.5, 100.5),
                               (200.5, 100.5),
                               stroke='#000000',
                               stroke_linecap='round'))
    expected_svg = LiveSvg(expected.tostring())

    t = SvgTurtle(300, 200)
    t.forward(50)
    t.right(90)
    t.pensize(5)
    t.forward(20)
    t.pensize(6)
    t.undo()
    t.undo()
    svg = LiveSvg(t.to_svg())

    image_differ.assert_equal(svg, expected_svg)


def test_input():
    t = SvgTurtle()

    text = t.getscreen().textinput('my title', 'my prompt')
    number = t.getscreen().numinput('my title', 'my prompt')

    assert text is None
    assert number is None


def test_click():
    t = SvgTurtle()

    t.getscreen().onclick(lambda x, y: None)
    t.onclick(lambda x, y: None)
    # noinspection PyTypeChecker
    t.onclick(None)


def test_listen():
    t = SvgTurtle()
    t.getscreen().listen()


@pytest.mark.parametrize(
    'colour_in,colour_out',
    [((0.1, 0.2, 0.3), (0.1, 0.2, 0.3)),
     ('gray100', 'white'),
     ('black', 'black'),
     ('pink', 'pink')])
def test_get_colour(colour_in, colour_out):
    t = SvgTurtle()
    t.pencolor(colour_in)

    c = t.pencolor()

    assert c == colour_out


# noinspection PyUnresolvedReferences
def test_exits():
    """ All the exit methods do nothing. """
    t = SvgTurtle()

    t.getscreen().mainloop()
    t.getscreen().done()
    t.getscreen().bye()
    t.getscreen().exitonclick()
