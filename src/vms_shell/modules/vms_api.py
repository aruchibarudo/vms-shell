from uuid import uuid4, UUID
from collections.abc import Iterable
import logging
import requests
from . import pool
from time import sleep
import sys

if sys.platform == 'win32':
  from pyreadline3 import Readline
  readline = Readline()
else:
  import readline
  
def http_exception(func):
  def wrapper(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except requests.exceptions.RequestException as exc:
      logging.error(str(exc))
    
  return wrapper


class VMS():

  def __init__(self, username: str, vms_api: str, name: str=None, logger=None) -> None:
    self.logger = logger or logging.getLogger(__name__)
    self.name = name
    self.username = username
    self.http_timeout = 3
    self.pool_id = None
    self.http = requests.Session()
    self.http.headers['Content-type'] = 'application/json'
    #self.http.cookies.set(domain='techpark.local', name='username', value=username)
    self.vms_api = vms_api
    self.pool = pool.TVMPool(owner=username)
    self.pools = {}
    self.login()
    self.pool_list()
    
    if self.name:
      self.pool_select(name=self.name)

  
  @http_exception
  def login(self):
    params = {
      'username': self.username
    }
    
    self.logger.debug(f'Login as {self.username}')
    
    response = self.http.post(f'{self.vms_api}/login', params=params)
    status = response.json().get('status')
    detail = response.json().get('detail')
    self.logger.info(f'{detail}: {status}')

    
  @http_exception
  def pool_create(self, name: str=None):
    params = {
      'owner': self.username,
      'name': name
    }
    
    pool_id = uuid4()
    self.logger.debug(f'Create pool {pool_id}')
    self.pool.state = pool.PoolState.CREATE
    
    if name:
      self.pool.vm_name_prefix = name
    
    response = self.http.post(f'{self.vms_api}/pool', params=params)
    data = response.json().get('data')
    pool_id = data.get('id')
    self.pool_id = pool_id
    self.pool = pool.TVMPool(**data)
    
    logging.debug(f'Pool {pool_id} created: {data}')
    return self.pool_id
    
  
  @http_exception
  def pool_list(self):
    response = self.http.get(f'{self.vms_api}/pool/all', timeout=self.http_timeout)
    _res = response.json().get('data')
    self.pools = _res.get('pools')
    return _res
    

  @http_exception    
  def pool_select(self, name: str):
    self.pool_id = self.pools.get(name)
    self.logger.debug(f'Select pool {name}/{self.pool_id}')
    response = self.http.get(f'{self.vms_api}/pool/{name}', timeout=self.http_timeout)
    _res = response.json()
    
    if _res.get('status') == 'OK':
      self.pool = pool.TVMPool(**_res.get('data'))
      self.logger.debug(f'Selected pool {name}')
    else:
      self.logger.debug(f'Pool {name} not found')
      
    return _res.get('status') == 'OK'
    
    
  @http_exception    
  def pool_delete(self):
    self.logger.debug(f'Delete pool {self.pool_id}')
    response = self.http.delete(f'{self.vms_api}/pool/{self.pool_id}', timeout=self.http_timeout)
    _res = response.json()
    
    if _res.get('status') == 'OK':
      self.pool = pool.TVMPool(owner=self.username)
      self.logger.debug(f'Pool {self.pool_id} deleted')
      self.pool_id = None
    else:
      self.logger.debug(f'Can not delete pool {self.pool_id}')
      
    return _res.get('status') == 'OK'
  
  
  @http_exception
  def pool_get(self):
    self.logger.debug(f'Show pool {self.pool_id}')
    response = self.http.get(f'{self.vms_api}/pool/{self.pool_id}', timeout=self.http_timeout)
    _res = response.json()
    
    if(_res.get('status') == 'OK'):
      self.pool = pool.TVMPool(**_res.get('data'))
      self.logger.debug(f'Pool {self.pool_id} OK: {_res}')
    else:
      self.logger.debug(f'Pool {self.pool_id} ERROR: {_res}')
    

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
    
  def get_next_index(self) -> int:
    _idxs = []
    
    for _vm in self.pool.items:
      _idxs.append(int(_vm.name.removeprefix(self.pool.vm_name_prefix)))
    
    return max(_idxs) + 1 if _idxs else 1

    
  def vm_add(self, type: str, os: str, qty: int=1):
    
    if type == 'small':
      _config = pool.TVMSmall()
    elif type == 'medium':
      _config = pool.TVMMedium()
    elif type == 'large':
      _config = pool.TVMLarge()
      
    _vm = pool.TVM(
      type = type,
      name = f'{self.pool.vm_name_prefix}{self.get_next_index():02}',
      os = os,
      state = 'NEW',
      config = _config
    )
    
    self.pool.items.append(_vm)
    
  
  def vm_rm(self, name: str):
    _vm = []
    
    for item in self.pool.items:
    
      if str(item.name) != name:
        _vm.append(item)
      else:
        print(f'Deleted {name}')
        
    self.pool.items = _vm
    

  @http_exception
  def pool_apply(self):
    self.pool.state = pool.PoolState.APPLY
    response = self.http.post(f'{self.vms_api}/pool/apply', data=self.pool.json(), timeout=self.http_timeout)
    
    if(response.status_code >= 400):
      print('Error')
      print(response.text)
      print(self.pool.json())
    else:
      _res = response.json()
      self.logger.debug(f'Apply result: {_res}')
      self.pool = pool.TVMPool(**_res.get('data'))
      
  
  @http_exception
  def pool_plan(self):
    self.pool.state = pool.PoolState.PLAN
    response = self.http.post(f'{self.vms_api}/pool/plan', data=self.pool.json(), timeout=self.http_timeout)
    
    if(response.status_code >= 400):
      print('Error')
      print(response.text)
      print(self.pool.json())
    else:
      _res = response.json()
      self.pool = pool.TVMPool(**_res.get('data'))
      
      
  @http_exception
  def pool_destroy(self):
    self.pool.state = pool.PoolState.DESTROY
    response = self.http.post(f'{self.vms_api}/pool/destroy', data=self.pool.json(), timeout=self.http_timeout)
    
    if(response.status_code >= 400):
      print('Error')
      print(response.text)
      print(self.pool.json())
    else:
      _res = response.json()
      self.pool = pool.TVMPool(**_res.get('data'))
      
    
  @http_exception
  def update_state(self):
    response = self.http.get(f'{self.vms_api}/pool/state', timeout=self.http_timeout)

    if(response.status_code >= 400):
      print('Error')
      print(response.text)
      print(self.pool.json())
    else:
      _res = response.json()
      self.pool = pool.TVMPool(**_res.get('data'))

  
  @http_exception
  def get_state(self, pool_id: UUID, task_id: UUID, prompt: str=None, buffer: str=''):
    time_to_sleep = 5
    
    while True:
      _task_id = task_id
      response = self.http.get(f'{self.vms_api}/tasks/{_task_id}', timeout=self.http_timeout)
      #print("Wake up! I was slept for {0}s".format(time_to_sleep))

      if(response.status_code >= 400):
        logging.error('Error')
        logging.error(response.text)
        logging.debug(self.pool.json())
        
        if response.status_code == 500:
          logging.error('Status can not by updated, stop polling status!')
          return
        
      else:
        _res = pool.VMSTaskResult(**response.json())
        logging.debug(_res)
        new_state = _res.state
        new_task_name = self.pool.state_note
        
        for task in _res.tasks:

          if task.state == 'PROGRESS':
            new_state = 'PROGRESS'
            new_task_name = task.name
        
        if self.pool.state != pool.PoolState(new_state) or self.pool.state_note != new_task_name:
          
          if new_state == 'SUCCESS':
            new_task_name = _res.state_note
            
          print()
          print(f'State changed (pool {_res.pool_name}): {new_task_name}: {self.pool.state.value} -> {new_state}')
          self.pool.state = pool.PoolState(new_state)
          self.pool.state_note = new_task_name
          
          if prompt:
            print(prompt, readline.get_line_buffer(), sep='', end='', flush=True)
        
        if new_state in ('FAILURE', 'SUCCESS'):
          return
        
      sleep(time_to_sleep)
