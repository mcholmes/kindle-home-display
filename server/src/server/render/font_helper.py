from __future__ import annotations

import logging
import os
import pathlib

from PIL import ImageDraw, ImageFont

logger = logging.getLogger(__name__)
class FontFactory:

    def __init__(self, draw: ImageDraw, font_dir: str | None = None, font_map: dict[str] | None = None):
        self.default_size = 48

        if font_dir is None:
            current_path = str(pathlib.Path(__file__).parent.absolute())
            self.font_dir = os.path.join(current_path, "font")
        else:
            self.font_dir = font_dir

        if font_map is None:
            # Just use the file names as the alias
            self.font_map = {file: file for file in os.listdir(self.font_dir) if file.endswith(".ttf")}
        else:
            self.font_map = font_map

        self.draw = draw

        # example:
        # font_map = {
        #         "light": "Lexend-Light.ttf",
        #         "regular": "Lexend-Regular.ttf",
        #         "bold": "Lexend-Bold.ttf",
        #         "extrabold": "Lexend-ExtraBold.ttf",
        #         "weather": "weathericons-regular-webfont.ttf"
        # }

    def get(self, name: str, size: int | None = None):
        if size is None:
            size = self.default_size

        if name not in self.font_map:
            err = f"Font name not in defined list. Valid values are: {self.font_map.values()}"
            raise ValueError(err)

        font_file = os.path.join(self.font_dir, self.font_map[name])

        return Font(self.draw, font_file, size)

class Font:
    """
    An abstraction over PIL's ImageFont.
    - Allows easier interrogation & reuse of calculated height.
    - Allows fonts to draw themselves, rather than passing around ImageFonts.
    """

    def __init__(self, draw: ImageDraw, file: str, size: int):

        self._draw = draw

        f = ImageFont.truetype(file, size)
        self._font = f
        self._height = f.getbbox("lq")[3] # max height for a line of this size, not its actual height

    def width(self, text: str) -> int:
        return self._font.getbbox(text)[2]

    def height(self, text: str | None = None) -> int:
        if text is None:
            return self._height

        return self._font.getbbox(text)[3]

    def size(self, text: str) -> int:
        return self.width(text), self.height(text)

    def write(self, position: tuple, text: str, colour: str = "black", anchor: str | None = None) -> None:
        self._draw.text(position, text, font=self._font, fill=colour, anchor=anchor)

    def image_font(self) -> ImageFont:
        return self._font
