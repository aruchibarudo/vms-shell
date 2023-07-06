from cmd import Cmd
import asyncio
from threading import Thread
from time import sleep
import readline


def echo(line):
  return line


def arun(line):
  for i in range(int(line)):
    sleep(2)
    print()
    print(echo(i))
    print('> ', readline.get_line_buffer(), sep='', end='', flush=True)


class Run(Cmd):
  intro = 'Welcome to the turtle shell.   Type help or ? to list commands.\n'
  prompt = '> '
  


  def __init__(self, completekey: str = "tab", prompt: str='> ') -> None:
    super().__init__(completekey)
    self.prompt = prompt
  
  
  def do_one(self, line):
    print(f'Cmd = {line}')


  def do_trun(self, line):
    th = Thread(target=arun, daemon=True, name='BG', kwargs={'line': line})
    th.start()


  def do_EOF(self, line):
    return True


acmd = Run()
acmd.cmdloop()
