from uuid import uuid4, UUID
from collections.abc import Iterable
import logging
import requests
from . import pool
import json


class VMS():

  def __init__(self, username: str, vms_api: str, pool_id: str=None, logger=None) -> None:
    self.logger = logger or logging.getLogger(__name__)
    self.pool_id = pool_id
    self.username = username
    self.http = requests.Session()
    self.http.headers['Content-type'] = 'application/json'
    self.vms_api = vms_api
    self.pool = pool.TVMPool(owner=username)

  
  def pool_create(self):
    params = {
      'owner': self.username
    }
    
    pool_id = uuid4()
    self.logger.debug(f'Create pool {pool_id}')
    response = self.http.post(f'{self.vms_api}/pool', params=params)
    data = response.json().get('data')
    pool_id = data.get('id')
    self.pool_id = pool_id
    logging.debug(f'Pool {pool_id} created: {data}')
    return self.pool_id
    
  
  def pool_list(self):
    response = self.http.get(f'{self.vms_api}/pool/all')
    _res = response.json()
    return _res.get('data')
    
    
  def pool_connect(self, pool_id: UUID):
    self.pool_id = pool_id
    self.logger.debug(f'Connect to pool {pool_id}')
    response = self.http.get(f'{self.vms_api}/pool/{pool_id}')
    _res = response.json()
    
    if _res.get('status') == 'OK':
      self.pool = pool.TVMPool(**_res.get('data'))
      self.logger.debug(f'Connected to pool {pool_id}')
    else:
      self.logger.debug(f'Pool {pool_id} not found')
      
    return _res.get('status') == 'OK'
    
    
  def pool_get(self):
    self.logger.debug(f'Show pool {self.pool_id}')
    response = self.http.get(f'{self.vms_api}/pool')
    _res = response.json()
    
    if(_res.get('status') == 'OK'):
      self.pool = pool.TVMPool(**_res.get('data'))
      self.logger.debug(f'Pool {self.pool_id} OK: {_res}')
    else:
      self.logger.debug(f'Pool {self.pool_id} ERROR: {_res}')
    
    if len(self.pool.items) > 0:
      
      for item in self.pool.items:
        yield {
          'id': str(item.id),
          'name': item.name,
          'os': item.os.value,
          'cpu': item.config.CPU,
          'memory': item.config.MEMORY,
          'disk': item.config.DISK
        }
        
    else:  
      return []
    

  def pool_show(self):
    self.logger.debug(f'Show pool {self.pool_id}')
    
    if isinstance(self.pool.items, Iterable):
      
      for item in self.pool.items:
        yield {
          'id': str(item.id),
          'name': item.name,
          'os': item.os.value,
          'cpu': item.config.CPU,
          'memory': item.config.MEMORY,
          'disk': item.config.DISK
        }
        
    else:  
      return []
    
  def vm_add(self, type: str, os: str, qty: int=1):
    
    if type == 'small':
      _config = pool.TVMSmall()
    elif type == 'medium':
      _config = pool.TVMMedium()
    elif type == 'large':
      _config = pool.TVMLarge()

    _vm = pool.TVM(
      type = type,
      name = f'{self.pool.vm_name_prefix}{(len(self.pool.items) + 1)}',
      os = os,
      state = 'NEW',
      config = _config
    )
    
    self.pool.items.append(_vm)
    
  
  def vm_rm(self, id: UUID):
    _vm = []
    
    for item in self.pool.items:
    
      if str(item.id) != id:
        _vm.append(item)
      else:
        print(f'Deleted {id}')
        
    self.pool.items = _vm
    

  def pool_apply(self):
    response = self.http.post(f'{self.vms_api}/pool/apply', data=self.pool.json())
    
    if(response.status_code >= 400):
      print('Error')
      print(response.text)
      print(self.pool.json())
    else:
      _res = response.json()
      self.pool = pool.TVMPool(**_res.get('data'))
      
  
  def pool_plan(self):
    response = self.http.post(f'{self.vms_api}/pool/plan', data=self.pool.json())
    
    if(response.status_code >= 400):
      print('Error')
      print(response.text)
      print(self.pool.json())
    else:
      _res = response.json()
      self.pool = pool.TVMPool(**_res.get('data'))
      
      
  def pool_destroy(self):
    response = self.http.post(f'{self.vms_api}/pool/destroy', data=self.pool.json())
    
    if(response.status_code >= 400):
      print('Error')
      print(response.text)
      print(self.pool.json())
    else:
      _res = response.json()
      self.pool = pool.TVMPool(**_res.get('data'))