import logging
from cmd import Cmd
import yaml
from modules.vms_api import *

VMS_API_HOST = 'spb99tpagent01'
VMS_API_PORT = 80
VMS_API_BASE_PATH = 'vms/api/v1'
VMS_API_USE_TLS = False

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
  

  def do_connect(self, input):
    res = vms.pool_connect(pool_id=input)
    
    if res:
      print(f'Connected to pool {input}')
    else:
      print(f'Could not connect to pool {input}')
    
  
  def do_create(self, input):
    res = vms.pool_create()
    
    if res:
      print(f'Pool created {res}')
    else:
      print(f'Could not create pool {input}')


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
      vms.vm_add(type=_args[0], os=_args[1], qty=_qty)
  
  
  def help_add(self):
    print('Add VM instance to pool')
    print('add small redos 2 - add 2 VM instance type small with os RedOS')
    

  def complete_add(self, text, line, begidx, endidx) -> list[str]:
    return [i for i in ('small', 'medium', 'large') if i.startswith(text)]
  
  
  def do_rm(self, input):
    vms.vm_rm(input)


  def do_apply(self, input):
    vms.pool_apply()
  
  
  def do_pool(self, input):
    if input == 'plan':
      vms.pool_plan()
    if input == 'apply':
      vms.pool_apply()
    if input == 'destroy':
      vms.pool_destroy()
    if input == 'list':
      _res = vms.pool_list()
      print(f'Selected: {_res.get("selected")}')
      
      for item in _res.get('pools'):
        print (f'Pool: {item}')
      
        
  def do_show(self, input):
    items = list(vms.pool_show())
    
    if input == 'yaml':
      print(yaml.dump(items))
    else:
      print(f'Pool id: {vms.pool_id}')
      print(f'owner: {vms.pool.owner}')
      print(f'State: {vms.pool.state}')
      print(f'{TITLE_NUMBER:>3}| {TITLE_ID:38}| {TITLE_NAME:8}| {TITLE_CPU:4}| {TITLE_MEMORY:5}| {TITLE_DISK:6}|')
      print('-'*74)
      for idx, item in enumerate(items):
        print(f'{idx:3}| {item["id"]:38}| {item["name"]:8}|{item["cpu"]:4} |{item["memory"]:5} |{item["disk"]:6} |')
    
  
  do_EOF = do_exit


def parse(arg: str):
  'Convert a series of zero or more numbers to an argument tuple'
  return tuple(arg.split())


log_format = '%(asctime)s [%(name)s] %(levelname)-8s %(message)s'

if __name__ == '__main__':
  logger = logging.getLogger(__name__)
  logging.basicConfig(format=log_format, level=logging.DEBUG)
  sh = VmShell()
  vms = VMS(username='batalov.av', vms_api=VMS_API_BASE_URL)
  sh.cmdloop()