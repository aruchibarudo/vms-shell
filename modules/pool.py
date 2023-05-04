from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel
from uuid import uuid4, UUID


class MyEnum(Enum):

  @classmethod
  def has_value(cls, value) -> list:
    return value in cls._value2member_map_

  @classmethod
  def list(cls) -> list:
    return [i.value for i in cls]
  

class TVMTypes(str, MyEnum):
  small = 'small'
  medium = 'medium'
  large = 'large'
  

class TVMOs(str, MyEnum):
  redos73 = 'redos73'
  astra17orel = 'astra17orel'


class TVMConfig(BaseModel):
  CPU = 0
  MEMORY = 0
  DISK = 0


class TVMSmall(TVMConfig):
  CPU = 2
  MEMORY = 4
  DISK = 50


class TVMMedium(TVMConfig):
  CPU = 4
  MEMORY = 8
  DISK = 100
  
  
class TVMLarge(TVMConfig):
  CPU = 8
  MEMORY = 16
  DISK = 200  


class TVM(BaseModel):
  id: UUID = None
  type: TVMTypes
  name: str
  config: TVMConfig
  os: TVMOs
  state: Optional[str] = None


class TVMPool(BaseModel):
  id: UUID = None
  vm_name_prefix: str = 'spb41tp9223-'
  state: str = None
  site: str = "SPB41"
  api_version: str = 'v1'
  items: Union[List[TVM], list] = list()
  owner: str
  description: str = None
  name: str = None
