#!/usr/bin/env python3

import logging
from cmd import Cmd
from threading import Thread
import yaml
import os
import shlex
from pathlib import Path
import configparser

if __name__ == '__main__':
  from modules.vms_api import *
  from modules.namer import *
else: 
  from .modules.vms_api import *
  from .modules.namer import *


VERSION = '0.1.5'
VMS_API_HOST = 'spb99tpagent01'
VMS_API_PORT = 80
VMS_API_BASE_PATH = 'vms/api/v1'
VMS_API_USE_TLS = False
NAMER_API = 'http://spb99tpagent01:8443'
USERNAME = os.getlogin()
CONFIG_FILENAME = str(Path.home() / Path('.vmshrc'))

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
TITLE_OS = 'Image'
TITLE_CPU = 'CPU'
TITLE_MEMORY = 'RAM'
TITLE_DISK = 'Disk'
TITLE_NOTE = 'Note'

class VmShell(Cmd):
  prompt = 'vms> '
  err = []
  pool_cmds = (
    'create',
    'select',
    'plan',
    'apply',
    'list',
    'destroy',
    'delete'
  )


  def __init__(self, intro: str=None, prompt: str='vms> ', completekey: str='tab', name: str=None):
    super().__init__(completekey=completekey)
    self.intro = intro
    self.prompt = prompt
    self.vms = VMS(username=USERNAME, vms_api=VMS_API_BASE_URL, name=name)
    self.namer = Namer(api_url=NAMER_API)
    #self.completekey = 'tab'

    
  def emptyline(self):
      pass


  def show_error(self, msg: str=None) -> bool:
        
    if len(self.err) > 0:
      [print(f'*** Error: {i}') for i in self.err]
      self.err = []
      return True
    
    return False
    
  
  def do_version(self, input):
    print(f'v{VERSION}')
  

  def do_add(self, input):
    _args = parse(input)
    _qty = 1
    _description = None
    
    if not (len(_args) > 0 and pool.TVMTypes.has_value(_args[0])):
      self.err.append(f'First parameter one of {pool.TVMTypes.list()}')

    if not (len(_args) > 1 and pool.TVMOs.has_value(_args[1])):
      self.err.append(f'Second parameter one of {pool.TVMOs.list()}')

    if len(_args) == 3:
      _description = _args[2]
      
    if not self.show_error():
      self.vms.vm_add(type=_args[0], os=_args[1], qty=_qty, description=_description)
  
  
  def help_add(self):
    print('Add VM instance to pool')
    print('add small redos73 - add VM instance type small with os RedOS 7.3')
    

  def complete_add(self, text, line, begidx, endidx) -> list:
    _args = parse(line)
    
    if not text and len(_args) == 1:
      return [i for i in pool.TVMTypes.list() if i.startswith(text)]
    elif not text and len(_args) == 2:
      return [i for i in pool.TVMOs.list() if i.startswith(text)]
    elif len(_args) == 2:
      return [i for i in pool.TVMTypes.list() if i.startswith(text)]
    elif text and len(_args) == 3:
      return [i for i in pool.TVMOs.list() if i.startswith(text)]
    else:
      return text
  
  
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
      _name = self.namer.get_prefix()
      _res = self.vms.pool_create(name=_name)
      
      if _res:
        print(f'Pool created {_res}')
      else:
        print(f'Could not create pool')
        
    elif _args[0] == 'select':

      if len(_args) == 2:
        res = self.vms.pool_select(name=_args[1])
      
        if res:
          print(f'Selected pool {_args[1]}')
        else:
          print(f'Could not select pool {_args[1]}')
          
      else:
        print('Pool must be specified ex. "pool select <pool_name>"')
        
    elif _args[0] == 'plan':
      self.vms.pool_plan()
      th = Thread(target=self.vms.get_state,
                  daemon=True,
                  name=f'{_args[0]} pool {self.vms.name}',
                  kwargs={'pool_id': self.vms.pool_id,
                          'task_id':self.vms.pool.task_id,
                          'prompt': self.prompt})
      th.start()
    elif _args[0] == 'apply':
      self.vms.pool_apply()
      th = Thread(target=self.vms.get_state,
                  daemon=True,
                  name=f'{_args[0]} pool {self.vms.name}',
                  kwargs={'pool_id': self.vms.pool_id,
                          'task_id':self.vms.pool.task_id,
                          'prompt': self.prompt})
      th.start()
      self.namer.park_prefix(prefix=self.vms.pool.vm_name_prefix)
    elif _args[0] == 'destroy':
      self.vms.pool_destroy()
      th = Thread(target=self.vms.get_state,
                  daemon=True,
                  name=f'{_args[0]} pool {self.vms.name}',
                  kwargs={'pool_id': self.vms.pool_id,
                          'task_id':self.vms.pool.task_id,
                          'prompt': self.prompt})
      th.start()
    elif _args[0] == 'delete':
      _res = self.vms.pool_delete()
      self.namer.free_prefix(self.vms.pool.vm_name_prefix)
    elif _args[0] == 'list':
      _res = self.vms.pool_list()
      
      if _res:
        
        for item in _res.get('pools'):
          if self.vms.pool.name == item:
            print(f'Pool: *{item}')
          else:
            print(f'Pool: {item}')
      
        
  def do_show(self, input):
    items = list(self.vms.pool_show())
    
    if input == 'yaml':
      print(yaml.dump(items))
    else:
      _state = self.vms.pool.state.value if self.vms.pool.state else 'INIT'
      print(f'Pool id: {self.vms.pool_id}')
      print(f'Pool name: {self.vms.pool.name}')
      print(f'owner: {self.vms.pool.owner}')
      print(f'State: {_state}')
      print(f'{TITLE_NUMBER:>3}| {TITLE_NAME:14}| {TITLE_OS:18}| {TITLE_CPU:4}| {TITLE_MEMORY:5}| {TITLE_DISK:6}| {TITLE_NOTE}')
      print('-'*63)
      for idx, item in enumerate(items):
        print(f'{idx:3}| {item["name"]:14}| {item["os"]:18}|{item["cpu"]:4} |{item["memory"]:5} |{item["disk"]:6} | {item["notes"]}')
    
  
  def do_state(self, input):
    self.vms.get_state()
      

  def do_EOF(self, line):
    return True
  

def parse(arg: str):
  'Convert a series of zero or more numbers to an argument tuple'
  return tuple(shlex.split(arg))


def load_config(path: str) -> configparser.ConfigParser:
  logging.debug(f'Check config file {path}')
  conf_file = Path(path)
  config = configparser.ConfigParser()
  
  if conf_file.is_file():
    logging.debug(f'Load config file {str(conf_file)}')
    config.read(str(conf_file))
  
  return config


def save_config(config: configparser.ConfigParser, path: str):
  logging.debug(f'Save config file {path}')
  
  with open(path, 'w') as f:
    config.write(f)


def main():
  log_format = '%(asctime)s [%(name)s] %(levelname)-8s %(message)s'
  logger = logging.getLogger(__name__)
  logging.basicConfig(format=log_format, level=logging.INFO)
  CONFIG = load_config(CONFIG_FILENAME)
  sh = VmShell(intro=f"VMS shell version {VERSION}", prompt="vms> ", name=CONFIG['DEFAULT'].get('POOL_NAME'))  
  sh.cmdloop()

  if sh.vms.pool.name:
    CONFIG['DEFAULT']['POOL_NAME'] = sh.vms.pool.name
  else:
    CONFIG.remove_option(section='DEFAULT', option='POOL_NAME')
    
  save_config(config=CONFIG, path=CONFIG_FILENAME)
    

if __name__ == '__main__':
  main()