from typing import List
from pydantic import BaseModel
import requests

class PrefixItem(BaseModel):
  id: int
  name: str


class PrefixResult(BaseModel):
  result: str
  detail: PrefixItem


class Namer():
  def __init__(self, api_url: str) -> None:
    self.http = requests.Session()
    self.api_url = api_url


  def get_prefix(self) -> str:
    url = f'{self.api_url}/next'
    respone = self.http.post(url)
    _res = PrefixResult(**respone.json())
    if _res.result == 'OK':
      return _res.detail.name
    else:
      return None
  
  
  def park_prefix(self, prefix: str) -> bool:
    url = f'{self.api_url}/lock/{prefix}'
    respone = self.http.put(url)
    if respone.status_code == 200:
      return True
    else:
      respone.raise_for_status()


  def free_prefix(self, prefix: str) -> bool:
    url = f'{self.api_url}/unlock/{prefix}'
    respone = self.http.put(url)
    _res = respone.json()
    if respone.status_code == 200:
      return _res.get('result') == 'OK'
    else:
      respone.raise_for_status()