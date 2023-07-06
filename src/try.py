from cmd import Cmd
import asyncio
from threading import Thread
from time import sleep


def echo(line):
  return line


def arun(line):
  for i in range(int(line)):
    sleep(2)
    print(echo(i))


class Run(Cmd):
  intro = 'Welcome to the turtle shell.   Type help or ? to list commands.\n'
  prompt = '(turtle) '
  
  async def echo(self, line):
    return line


  async def arun(self, line):
    for i in range(int(line)):
      await asyncio.sleep(2)
      self.stdout.write(await self.echo(i))
  


  def __init__(self, loop: asyncio.AbstractEventLoop, completekey: str = "tab") -> None:
    super().__init__(completekey)
    self.loop = loop
  
  
  def do_one(self, line):
    print(f'Cmd = {line}')
    
    
  def do_run(self, line):
    bt = set()
    task = self.loop.create_task(self.arun(line))
    bt.add(task)
    task.add_done_callback(bt.discard)
      

  def do_trun(self, line):
    th = Thread(target=arun, daemon=True, name='BG', kwargs={'line': line})
    th.start()
    
    
loop = asyncio.new_event_loop()
acmd = Run(loop=loop)
acmd.cmdloop()
