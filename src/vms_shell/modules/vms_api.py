from uuid import uuid4, UUID
from collections.abc import Iterable
import logging
import requests
from . import pool
from time import sleep
import sys
import threading

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
      print(f'Selected pool {self.pool.name}')

  
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
  def pool_create(self, name: str=None, description: str=None) -> UUID:
    params = {
      'owner': self.username,
      'name': name,
      'description': description
    }
    
    pool_id = uuid4()
    self.logger.debug(f'Create pool {pool_id}')
    self.pool.state = pool.PoolState.CREATE
    response = self.http.post(f'{self.vms_api}/pool', params=params)
    data = response.json().get('data')
    self.pool = pool.TVMPool(**data)
    
    logging.debug(f'Pool {self.pool.id} created: {data}')
    return self.pool.id
    
  
  @http_exception
  def pool_list(self):
    response = self.http.get(f'{self.vms_api}/pool/all', timeout=self.http_timeout)
    _res = response.json().get('data')
    self.pools = _res.get('pools')
    return _res
    

  @http_exception    
  def get_pool(self, name: str):
    _pool_id = self.pools.get(name)
    self.logger.debug(f'Get pool {name}/{_pool_id}')
    response = self.http.get(f'{self.vms_api}/pool/{name}', timeout=self.http_timeout)
    _res = response.json()
    
    if _res.get('status') == 'OK':
      _pool = pool.TVMPool(**_res.get('data'))
      self.logger.debug(f'Pool {name} exists')
      self.logger.debug(_pool)
    else:
      self.logger.debug(f'Pool {name} not found')
      
    return _pool


  @http_exception
  def pool_select(self, name: str):
    _pool_id = self.pools.get(name)

    if _pool_id:
      self.logger.debug(f'Select pool {name}/{_pool_id}')
      response = self.http.get(f'{self.vms_api}/pool/{name}', timeout=self.http_timeout)
      _res = response.json()
      
      if _res.get('status') == 'OK':
        self.pool = pool.TVMPool(**_res.get('data'))
        self.logger.debug(f'Selected pool {self.pool.name}/{self.pool.id}')
      else:
        self.logger.debug(f'Pool {name} not found')
        
      return _res.get('status') == 'OK'
    else:
      self.logger.debug(f'Pool {name} not found')
      return False
      
    
    
  @http_exception    
  def pool_delete(self):
    _pool_id = str(self.pool.id)
    self.logger.debug(f'Delete pool {_pool_id}')
    response = self.http.delete(f'{self.vms_api}/pool/{_pool_id}', timeout=self.http_timeout)
    _res = response.json()
    
    if _res.get('status') == 'OK':
      self.pool = None
      self.logger.debug(f'Pool {_pool_id} deleted')
    else:
      self.logger.debug(f'Can not delete pool {_pool_id}')
      
    return _res.get('status') == 'OK'
  
  
  @http_exception
  def pool_get(self):
    _ppol_id = str(self.pool.id)
    self.logger.debug(f'Show pool {_ppol_id}')
    response = self.http.get(f'{self.vms_api}/pool/{_ppol_id}', timeout=self.http_timeout)
    _res = response.json()
    
    if(_res.get('status') == 'OK'):
      self.pool = pool.TVMPool(**_res.get('data'))
      self.logger.debug(f'Pool {self.pool.id} OK: {_res}')
    else:
      self.logger.debug(f'Pool {self.pool.id} ERROR: {_res}')
    

  def pool_show(self):
    self.logger.debug(f'Show pool {str(self.pool.id)}')
    
    if isinstance(self.pool.items, Iterable):
      
      for item in self.pool.items:
        yield {
          'id': str(item.id),
          'name': item.name,
          'os': item.os.value,
          'cpu': item.config.CPU,
          'memory': item.config.MEMORY,
          'disk': item.config.DISK,
          'notes': item.notes
        }
        
    else:  
      return []
    
  def get_next_index(self) -> int:
    _idxs = []
    
    for _vm in self.pool.items:
      _idxs.append(int(_vm.name.replace(self.pool.name, '')))
    
    return max(_idxs) + 1 if _idxs else 1

    
  def vm_add(self, type: str, os: str, qty: int=1, description: str=None):
    
    if type == 'small':
      _config = pool.TVMSmall()
    elif type == 'medium':
      _config = pool.TVMMedium()
    elif type == 'large':
      _config = pool.TVMLarge()
      
    _vm = pool.TVM(
      type=type,
      name=f'{self.pool.name}{self.get_next_index():02}',
      os=os,
      state='NEW',
      config=_config,
      notes=description
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
    self.pool.state = pool.PoolState.PENDING
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
    self.pool.state = pool.PoolState.PENDING
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
    self.pool.state = pool.PoolState.PENDING
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
  def get_pool_state(self, name: str, prompt: str=None, time_to_sleep: int=5, time_to_live: int=600):
    
    local = threading.local()
    #local.pool_name = name
    local.retry = 0
    local.max_retry = int(time_to_live / time_to_sleep)
    local.pool = self.get_pool(name)
    local.old_pool_state = self.pool.state
    local.old_pool_state_note = self.pool.state_note    
    
    while True:
      local.retry += 1
      self.logger.debug(f'{local.pool.name} Retry {local.retry} of {local.max_retry}')
      
      if local.old_pool_state != local.pool.state or local.old_pool_state_note != local.pool.state_note:
        print()
        print(f'State changed (pool {local.pool.name}): {local.pool.state_note}: {local.old_pool_state.value} -> {local.pool.state.value}')

        if self.pool.id == local.pool.id:
          self.pool_select(local.pool.name)
                    
        if prompt:
          print(prompt, readline.get_line_buffer(), sep='', end='', flush=True)
        
        if local.pool.state in pool.TaskFinished:
          self.logger.debug(f'{local.pool.name} all tasks are finished')
          return
        
      if local.retry >= local.max_retry:
        self.logger.error(f'Fetch status for pool {local.pool.name}/{local.pool.id} timeout reached {time_to_live}s')
        
        if self.pool.id == local.pool.id:
          self.pool_select(local.pool.name)
        
        return
        
      self.logger.debug(f'Sleep for {time_to_sleep}s')
      sleep(time_to_sleep)
      local.old_pool_state = local.pool.state
      local.old_pool_state_note = local.pool.state_note
      local.pool = self.get_pool(name)



  @http_exception
  def get_state(self, pool_id: UUID, task_id: UUID, prompt: str=None):
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
        new_task_name = _res.state_note
        
        for task in _res.tasks:

          if task.state == 'PROGRESS':
            new_state = pool.PoolState.PROGRESS
            new_task_name = task.name
        
        if self.pool.state != new_state or self.pool.state_note != new_task_name:
          
          if new_state in pool.TaskFinished:
            new_task_name = _res.state_note
            
          print()
          print(f'State changed (pool {_res.pool_name}): {self.pool.state.value} -> {new_state.value}')
          self.pool.state = new_state
          self.pool.state_note = new_task_name
          
          if prompt:
            print(prompt, readline.get_line_buffer(), sep='', end='', flush=True)
        
        if new_state in pool.TaskFinished:
          return
        
      sleep(time_to_sleep)
