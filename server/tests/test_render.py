
from server.render import Renderer


def test_renderer():
    r = Renderer(
        image_width=2000,
        image_height=2000,
        rotate_angle=0,
        margin_x=100,
        margin_y=200,
        top_row_y=250,
        space_between_sections=50,
        fonts_file_dir="/Users/mike.holmes/projects/kindle-home-display/server/src/server/font"
    )

