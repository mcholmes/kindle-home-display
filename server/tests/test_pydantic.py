from dataclasses import field
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, field_validator, Field, ConfigDict, computed_field, SkipValidation

from datetime import date, datetime, timedelta
from time import sleep
from typing import Optional

from PIL import Image

@dataclass
class MyDataclass:
    field1: int
    field2: datetime = field(init=False,default=datetime.now())
    field3: datetime = field(init=False)

    def __post_init__(self):
        self.field3 = self.field2

    def run(self):
        print(self.field2, self.field3)

def test_MyDataclass():
    t = MyDataclass(field1=1)
    t.run()
    sleep(2)
    t.run()


class MyBaseModel(BaseModel):
    class Config:
        extra='forbid'
        arbitrary_types_allowed=True

    field1: datetime = Field(init=False,default=datetime.now())
    image_width: int = 1
    image: Image = Field(init=False,default=None,validate_default=False)

    def model_post_init(self, __context) -> None:
        self.image = Image.new("RGB", (self.image_width, self.image_width), "white")

def test_myBaseModel():
    t = MyBaseModel()
    print(t.image)

test_myBaseModel()
# test_MyDataclass()