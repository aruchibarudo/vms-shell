#!/usr/bin/env python3

import logging
from cmd import Cmd
from typing import IO, Union
import yaml
import os

if __name__ == '__main__':
  from modules.vms_api import *
else: 
  from .modules.vms_api import *
  
VMS_API_HOST = 'spb99tpagent01'
VMS_API_PORT = 80
VMS_API_BASE_PATH = 'vms/api/v1'
VMS_API_USE_TLS = False
USERNAME = os.getlogin()

if VMS_API_USE_TLS:
  VMS_API_BASE_URL = f'https://{VMS_API_HOST}'
else:
  VMS_API_BASE_URL = f'http://{VMS_API_HOST}'

if VMS_API_PORT:
  VMS_API_BASE_URL += f':{VMS_API_PORT}'

if VMS_API_BASE_PATH:
  VMS_API_BASE_URL += f'/{VMS_API_BASE_PATH}'


TITLE_NUMBER = '#'
TITLE_ID = 'ID'
TITLE_NAME = 'Name'
TITLE_CPU = 'CPU'
TITLE_MEMORY = 'RAM'
TITLE_DISK = 'Disk'

class VmShell(Cmd):
  prompt = 'vms> '
  err = []
  pool_cmds = (
    'create',
    'connect',
    'plan',
    'apply',
    'list',
    'destroy'
  )


  def __init__(self, completekey: str = "tab", stdin: IO[str] = None, stdout: IO[str] = None) -> None:
    super().__init__(completekey, stdin, stdout)
    self.vms = VMS(username=USERNAME, vms_api=VMS_API_BASE_URL)
    
  def show_error(self, msg: str=None) -> bool:
    
    if len(self.err) > 0:
      [print(f'*** Error: {i}') for i in self.err]
      self.err = []
      return True
    
    return False
    
  
  def do_exit(self, input):
    print("bye")
    return True
  

  def do_hello(self, input):
    print(f'Hello "{input}"')
  
   

  def do_add(self, input):
    _args = parse(input)
    _qty = None
    
    if not (len(_args) > 0 and pool.TVMTypes.has_value(_args[0])):
      self.err.append(f'First parameter one of {pool.TVMTypes.list()}')

    if not (len(_args) > 1 and pool.TVMOs.has_value(_args[1])):
      self.err.append(f'Second parameter one of {pool.TVMOs.list()}')

    if len(_args) == 3:
      try:
        _qty = int(_args[2])
      except ValueError:
        self.err.append('Third paramter must be an integer')
    else:
      _qty = 1
      
    if not self.show_error():
      self.vms.vm_add(type=_args[0], os=_args[1], qty=_qty)
  
  
  def help_add(self):
    print('Add VM instance to pool')
    print('add small redos73 - add VM instance type small with os RedOS 7.3')
    

  def complete_add(self, text, line, begidx, endidx) -> list:
    return [i for i in pool.TVMTypes.list() if i.startswith(text)]
  
  
  def do_rm(self, input):
    self.vms.vm_rm(input)


  def do_apply(self, input):
    self.vms.pool_apply()
  
  
  def complete_pool(self, text, line, begidx, endidx) -> list:
    return [i for i in self.pool_cmds if i.startswith(text)]


  def do_pool(self, input):
    _args = parse(input)
    
    if not (_args and _args[0] in self.pool_cmds):
      self.err.append(f'pool has only {self.pool_cmds} command')
      
      if self.show_error():
        return None
    
    if _args[0] == 'create':
      _res = self.vms.pool_create()
      
      if _res:
        print(f'Pool created {_res}')
      else:
        print(f'Could not create pool')
        
    elif _args[0] == 'connect':
      res = self.vms.pool_select(pool_id=_args[1])
    
      if res:
        print(f'Selected pool {_args[1]}')
      else:
        print(f'Could not select pool {_args[1]}')
        
    elif _args[0] == 'plan':
      self.vms.pool_plan()
    elif _args[0] == 'apply':
      self.vms.pool_apply()
    elif _args[0] == 'destroy':
      self.vms.pool_destroy()
    elif _args[0] == 'list':
      _res = self.vms.pool_list()
      
      if _res:
        print(f'Selected: {_res.get("selected")}')
        
        for item in _res.get('pools'):
          print (f'Pool: {item}')
      
        
  def do_show(self, input):
    items = list(self.vms.pool_show())
    
    if input == 'yaml':
      print(yaml.dump(items))
    else:
      print(f'Pool id: {self.vms.pool_id}')
      print(f'owner: {self.vms.pool.owner}')
      print(f'State: {self.vms.pool.state.value}')
      print(f'{TITLE_NUMBER:>3}| {TITLE_ID:38}| {TITLE_NAME:8}| {TITLE_CPU:4}| {TITLE_MEMORY:5}| {TITLE_DISK:6}|')
      print('-'*74)
      for idx, item in enumerate(items):
        print(f'{idx:3}| {item["id"]:38}| {item["name"]:8}|{item["cpu"]:4} |{item["memory"]:5} |{item["disk"]:6} |')
    
  
  do_EOF = do_exit


def parse(arg: str):
  'Convert a series of zero or more numbers to an argument tuple'
  return tuple(arg.split())


def main():
  log_format = '%(asctime)s [%(name)s] %(levelname)-8s %(message)s'
  logger = logging.getLogger(__name__)
  logging.basicConfig(format=log_format, level=logging.DEBUG)
  sh = VmShell()
  sh.cmdloop()

if __name__ == '__main__':
  main()