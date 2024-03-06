from PIL import ImageFont
import os
import pathlib
import logging

class FontFactory:

    def __init__(self, font_dir=None, font_map=None):
        self.logger = logging.getLogger('maginkdash')
        self.default_size = 48 
        
        if font_dir is None:
            currPath = str(pathlib.Path(__file__).parent.absolute())
            self.font_dir = os.path.join(currPath, "font")
        else:
            self.font_dir = font_dir
        
        if font_map is None:
            # Just use the file names as the alias
            self.font_map = {file: file for file in os.listdir(self.font_dir) if file.endswith(".ttf")}
        else:
            self.font_map = font_map
        
        # example:
        # font_map = {
        #         "light": "Lexend-Light.ttf", 
        #         "regular": "Lexend-Regular.ttf", 
        #         "bold": "Lexend-Bold.ttf",
        #         "extrabold": "Lexend-ExtraBold.ttf",
        #         "weather": "weathericons-regular-webfont.ttf"
        # }
    
    def get(self, name, size=None):
        if size is None:
            size = self.default_size

        if name not in self.font_map.keys():
            raise ValueError(f"Font name not in defined list. Valid values are: {self.font_map.values()}")
        
        font_file = os.path.join(self.font_dir, self.font_map[name])

        return Font(font_file, size)

class Font:
    """
    An abstraction over PIL's ImageFont to allow easier interrogation & reuse of calculated height.
    """

    def __init__(self, file, size):
        self.logger = logging.getLogger('maginkdash')
        
        f = ImageFont.truetype(file, size)
        self._font = f
        self._height = f.getbbox("lq")[3] # max height for a line of this size, not its actual height

    def width(self, text):
        return self._font.getbbox(text)[2]

    def height(self, text=None):
        if text==None:
            return self._height
        else:
            return self._font.getbbox(text)[3]
    
    def size(self, text):
        return self.width(text), self.height(text)

    def font(self):
        return self._font