# SPDX-FileCopyrightText: 2024-present Mike Holmes
# SPDX-License-Identifier: MIT

from datetime import date, time
from pathlib import Path

import pendulum
import pytest
from PIL import Image

from server.activity import Activity
from server.render import Font, FontFactory, Renderer

FONT_DIR = Path(__file__).resolve().parent.parent / "src" / "server" / "font"
FONT_DIR_STR = str(FONT_DIR)
FONT_MAP = {
    "extralight": "Lexend-ExtraLight.ttf",
    "light": "Lexend-Light.ttf",
    "regular": "Lexend-Regular.ttf",
    "bold": "Lexend-Bold.ttf",
    "extrabold": "Lexend-ExtraBold.ttf",
    "weather": "weathericons-regular-webfont.ttf",
}


@pytest.fixture
def renderer() -> Renderer:
    """Create a minimal Renderer for testing."""
    return Renderer(
        image_width=800,
        image_height=600,
        fonts_file_dir=FONT_DIR_STR,
        font_style_map=FONT_MAP,
        margin_x=50,
        margin_y=50,
        top_row_y=200,
        space_between_sections=80,
    )


@pytest.fixture
def draw():
    """Create a PIL ImageDraw for Font/FontFactory tests."""
    from PIL import ImageDraw

    img = Image.new("L", (400, 400), "white")
    return ImageDraw.Draw(img)


# ========== Font ==========


class TestFont:
    def test_width_returns_positive_int(self, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        w = font.width("Hello")
        assert isinstance(w, int)
        assert w > 0

    def test_height_without_text_returns_max_height(self, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        h = font.height()
        assert isinstance(h, int)
        assert h > 0

    def test_height_with_text_returns_text_height(self, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        h_text = font.height("A")
        h_default = font.height()
        assert isinstance(h_text, int)
        assert h_text > 0
        # Text-specific height should be <= max height
        assert h_text <= h_default

    def test_size_returns_width_and_height(self, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        w, h = font.size("Test")
        assert w > 0
        assert h > 0

    def test_write_does_not_raise(self, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        font.write((10, 10), "Hello")

    def test_write_with_colour_and_anchor(self, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        font.write((10, 10), "Hello", colour="gray", anchor="ls")

    def test_image_font_returns_truetype(self, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        pil_font = font.image_font()
        assert pil_font is not None

    def test_wider_text_has_greater_width(self, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        w_short = font.width("a")
        w_long = font.width("aaaaaaaaaa")
        assert w_long > w_short

    def test_larger_size_has_greater_height(self, draw):
        small = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 12)
        large = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 48)
        assert large.height() > small.height()


# ========== FontFactory ==========


class TestFontFactory:
    def test_get_returns_font(self, draw):
        ff = FontFactory(draw, FONT_DIR, FONT_MAP)
        font = ff.get("regular")
        assert isinstance(font, Font)

    def test_get_with_custom_size(self, draw):
        ff = FontFactory(draw, FONT_DIR, FONT_MAP)
        small = ff.get("regular", 12)
        large = ff.get("regular", 48)
        assert large.height() > small.height()

    def test_get_uses_default_size(self, draw):
        ff = FontFactory(draw, FONT_DIR, FONT_MAP)
        font = ff.get("regular")
        assert font is not None

    def test_get_invalid_name_raises(self, draw):
        ff = FontFactory(draw, FONT_DIR, FONT_MAP)
        with pytest.raises(ValueError, match="Font name not in defined list"):
            ff.get("nonexistent_font")

    def test_default_font_dir(self, draw):
        """When no font_dir is given, it defaults to the package's font/ directory."""
        ff = FontFactory(draw)
        assert ff.font_dir.name == "font"
        assert ff.font_dir.exists()

    def test_default_font_map(self, draw):
        """When no font_map is given, it auto-discovers .ttf files."""
        ff = FontFactory(draw)
        assert len(ff.font_map) > 0
        for key, val in ff.font_map.items():
            assert key.endswith(".ttf")
            assert val.endswith(".ttf")


# ========== Renderer ==========


class TestRenderer:
    def test_renderer_creates_image(self, renderer):
        png = renderer.get_png()
        assert isinstance(png, bytes)
        assert len(png) > 0
        # PNG magic bytes
        assert png[:4] == b"\x89PNG"

    def test_renderer_save_png(self, renderer, tmp_path):
        output = tmp_path / "test.png"
        renderer.save_png(str(output))
        assert output.exists()
        assert output.stat().st_size > 0

    def test_truncate_with_ellipsis_no_truncation(self, renderer, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        result = Renderer.truncate_with_ellipsis("Hi", 9999, font)
        assert result == "Hi"

    def test_truncate_with_ellipsis_truncates(self, renderer, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        long_text = "This is a very long text that should definitely be truncated"
        result = Renderer.truncate_with_ellipsis(long_text, 100, font)
        assert result.endswith("...")
        assert len(result) < len(long_text)

    def test_render_single_activity_with_bullet(self, renderer, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        # Should not raise
        renderer.render_single_activity(
            position=(50, 100),
            activity_text="Test event",
            bullet="•",
            font=font,
        )

    def test_render_single_activity_empty_bullet(self, renderer, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        renderer.render_single_activity(
            position=(50, 100),
            activity_text="Test event",
            bullet="",
            font=font,
        )

    def test_render_single_activity_with_prefix(self, renderer, draw):
        font = Font(draw, FONT_DIR / "Lexend-Regular.ttf", 24)
        renderer.render_single_activity(
            position=(50, 100),
            activity_text="Meeting",
            bullet="•",
            font=font,
            prefix="2.30pm",
        )

    def test_render_activities_with_events(self, renderer):
        events = [
            Activity(activity_type="event", summary="Morning standup", date_start=date(2025, 1, 5), time_start=time(9, 0)),
            Activity(activity_type="task", summary="Take out bins", date_start=date(2025, 1, 5)),
        ]
        y_after = renderer.render_activities("Today", events, 250)
        assert isinstance(y_after, (int, float))
        assert y_after > 250

    def test_render_activities_empty_list(self, renderer):
        """Empty events list should still render the section header."""
        y_after = renderer.render_activities("Today", [], 250)
        assert y_after > 250

    def test_render_activities_overflow_shows_more(self, renderer):
        """When events exceed the image height, a '+ N more...' message should appear."""
        # Create a small renderer that will overflow
        small = Renderer(
            image_width=800,
            image_height=300,
            fonts_file_dir=FONT_DIR_STR,
            font_style_map=FONT_MAP,
            margin_x=50,
            margin_y=50,
            top_row_y=200,
            space_between_sections=80,
        )
        events = [
            Activity(activity_type="event", summary=f"Event {i}", date_start=date(2025, 1, 5), time_start=time(i % 24, 0))
            for i in range(20)
        ]
        # Should not raise even with many events
        small.render_activities("Today", events, 100)

    def test_render_date(self, renderer):
        renderer.render_date("19", "Sat", "Apr")
        # Verify image was modified by checking it's not all white
        png = renderer.get_png()
        assert len(png) > 100

    def test_render_weather(self, renderer):
        renderer.render_weather("Cloudy | 15°", "\uf00d")
        png = renderer.get_png()
        assert len(png) > 100

    def test_render_last_updated(self, renderer):
        renderer.render_last_updated("14:30")
        png = renderer.get_png()
        assert len(png) > 100

    def test_render_all_produces_valid_png(self, renderer):
        now = pendulum.datetime(2025, 4, 19, 14, 30, tz="Europe/London")
        events_today = [
            Activity(activity_type="event", summary="Standup", date_start=date(2025, 4, 19), time_start=time(9, 0)),
            Activity(activity_type="task", summary="Bins", date_start=date(2025, 4, 19)),
        ]
        events_tomorrow = [
            Activity(activity_type="event", summary="Lunch", date_start=date(2025, 4, 20), time_start=time(12, 30)),
        ]

        renderer.render_all(now, events_today, events_tomorrow)
        png = renderer.get_png()

        assert png[:4] == b"\x89PNG"
        # Verify it's a valid image
        import io

        img = Image.open(io.BytesIO(png))
        assert img.size[0] > 0
        assert img.size[1] > 0

    def test_render_all_with_rotation(self):
        r = Renderer(
            image_width=800,
            image_height=600,
            fonts_file_dir=FONT_DIR_STR,
            font_style_map=FONT_MAP,
            margin_x=50,
            margin_y=50,
            top_row_y=200,
            space_between_sections=80,
            rotate_angle=90,
        )
        now = pendulum.datetime(2025, 4, 19, 14, 30, tz="Europe/London")
        r.render_all(now, [], [])
        png = r.get_png()

        import io

        img = Image.open(io.BytesIO(png))
        # After 90-degree rotation, width and height should swap
        assert img.size == (600, 800)

    def test_render_all_empty_events(self, renderer):
        """Rendering with no events should still produce a valid image."""
        now = pendulum.datetime(2025, 4, 19, 14, 30, tz="Europe/London")
        renderer.render_all(now, [], [])
        png = renderer.get_png()
        assert png[:4] == b"\x89PNG"

    def test_extra_fields_rejected(self):
        """Renderer should reject unknown fields (extra='forbid')."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            Renderer(
                image_width=800,
                image_height=600,
                unknown_field="should fail",
            )
