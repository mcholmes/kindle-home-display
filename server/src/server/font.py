from pathlib import Path

from PIL import ImageDraw, ImageFont
from loguru import logger

class Font:
    """
    An abstraction over PIL's ImageFont.
    - Allows easier interrogation & reuse of calculated height.
    - Allows fonts to draw themselves, rather than passing around ImageFonts.
    """

    def __init__(self, draw: ImageDraw, file: Path, size: int):
        self._draw = draw

        f = ImageFont.truetype(str(file), size)
        self._font = f
        self._height = f.getbbox("lq")[
            3
        ]  # max height for a line of this size, not its actual height

    def width(self, text: str) -> int:
        return self._font.getbbox(text)[2]

    def height(self, text: str | None = None) -> int:
        if text is None:
            return self._height

        return self._font.getbbox(text)[3]

    def size(self, text: str) -> tuple[int, int]:
        return self.width(text), self.height(text)

    def write(
        self,
        position: tuple,
        text: str,
        colour: str = "black",
        anchor: str | None = None,
    ) -> None:
        self._draw.text(position, text, font=self._font, fill=colour, anchor=anchor)

    def image_font(self) -> ImageFont:
        return self._font


class FontFactory:
    def __init__(
        self,
        draw: ImageDraw,
        font_dir: Path | None = None,
        font_map: dict[str, str] | None = None,
    ):
        self.default_size = 48

        if font_dir is None:
            current_path = Path(__file__).parent.absolute()
            self.font_dir = current_path / "font"
        else:
            self.font_dir = Path(font_dir)

        if font_map is None:
            # Just use the file names as the alias
            self.font_map = {
                f.name: f.name for f in self.font_dir.iterdir() if f.suffix == ".ttf"
            }
        else:
            self.font_map = font_map

        self.draw = draw

    def get(self, name: str, size: int | None = None) -> Font:
        if size is None:
            size = self.default_size

        if name not in self.font_map:
            err = f"Font name not in defined list. Valid values are: {self.font_map.values()}"
            raise ValueError(err)

        font_file = self.font_dir / self.font_map[name]

        return Font(self.draw, font_file, size)
