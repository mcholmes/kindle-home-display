#!/usr/bin/env python3
"""
Utility script to generate a dashboard image once.

Useful for testing or running as a cron job.

Usage:
    python generate_image.py
    
Environment variables:
    - TODOIST_API_KEY: Your Todoist API key
    - OPENWEATHERMAP_API_KEY: Your OpenWeatherMap API key
    - CONFIG_DIR: Directory containing config.toml (default: current dir)
"""

import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from server.app import App
from server.config import AppConfig


def main():
    """Generate dashboard image once."""
    try:
        # Load configuration
        config_dir = Path(os.environ.get("CONFIG_DIR", "."))
        config = AppConfig.from_dir(config_dir)
        
        # Setup basic logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        # Create app and generate image
        app = App(config)
        app.generate_image_and_save()
        
        output_path = Path(config.server.server_dir) / config.server.image_name
        print(f"✅ Dashboard image generated: {output_path}")
        
    except Exception as e:
        print(f"❌ Failed to generate image: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()