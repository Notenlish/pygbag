print("pkpyrc")
import sys
import embed
import builtins
import embed
import os
# split/rsplit fix from c++
# os.environ {} is filled from c++

class shell:
    HOME = "/data/data/org.python/assets"
    def ls(path="."):
        for elem in os.listdir(path):
            yield elem

    def cd(path="~"):
        if path=="~":
            os.chdir(shell.HOME)
        else:
            os.chdir(path)

shell.cd()


if 0:
    __next__ = next
    def next(it, default=0xdeadbeef):
        itrv = __next__(it)
        if itrv == StopIteration:
            if default == 0xdeadbeef:
                raise itrv
            return default
        return itrv

    __import__('builtins').next = next



import sys
sys.modules = []
sys.orig_argv = []
sys.argv = []
sys.__eot__ = chr(4)+chr(10)
sys.__stdout__ = sys.stdout
sys.__stderr__ = sys.stderr

def print_exception(*argv, **kw):
    import traceback
    traceback.print_exc()

sys.print_exception = print_exception
del print_exception


def ESC(*argv):
    for arg in argv:
        sys.__stdout__.write(chr(0x1B))
        sys.__stdout__.write(arg)
    sys.__stdout__.write(sys.__eot__)

def CSI(*argv):
    for arg in argv:
        ESC(f"[{arg}")


CSI("2J","f")
with open("pkpy.six","r") as source:
    print(source.read())
print(f"Python {sys.version} PocketPy::pykpocket edition on Emscripten", '.'.join(map(str, sys._emscripten_info)))


def new_module(name, code):
    if len(code)<80:
        with open(code,'r') as source:
            code=source.read()

    embed._new_module(name, code)
    return __import__(name)


embed.new_module = new_module
del new_module


def compile(source, filename, mode, flags=0, dont_inherit=False, optimize=-1, _feature_version=-1):
    return source
builtins.compile = compile
del compile

embed.new_module("platform", '''
__PKPY__ = True
__CPY__ = False

import json
import embed

class ProxyType(object):
    __callsign : dict = {}
    __callpath : list = []
    __serial : int  = 0
    __value = None


    def __init__(self, root, **env):
        self.__dlref = root #" ".join(map(str, argv))
        if __PKPY__:
            self.__callsign[id(self)]= root

    @staticmethod
    def __store( *argv):
        self = ProxyType

        #print("__store:",self.__callpath, argv, self.__callsign.get(argv[1],'?!') )

        if not len(self.__callpath):
            self.__serial = self.__serial + 1
            self.__callpath.append(f"C{self.__serial}")
            self.__callpath.append("<?>")

        if argv[1]>0:
            self.__callpath[1] = self.__callsign[argv[1]]

        if self.__callpath[-1]!=argv[0]:
            self.__callpath.append(argv[0])


    def __call__(self, *argv, **env):
        self.__callpath[1] = self.__dlref
        #print("__STORED",self.__callpath, argv)

        callid = self.__callpath.pop(0)
        fn = '.'.join(self.__callpath)
        stack : list = [ callid, self.__callpath ]
        if len(argv):
            stack.extend(argv)
        if env:
            stack.append(env)

        print(json.dumps(stack))
        # reset call stack
        self.__callpath.clear()
        args = tuple(stack[2:])
        print(f"CALL: {fn}{args} {callid}")
        embed.jseval(f"{fn}{args}")

    def __setattr(self_id, attr, line):
        self = ProxyType
        root = self.__callsign.get(self_id)
        callid = self.__callpath.pop(0)
        path = '.'.join(self.__callpath)
        jsdata = json.dumps(ProxyType.__value)
        #print(root, self.__callpath, attr, line, jsdata)
        embed.jseval(f"{path}.{attr}=JSON.parse(`{jsdata}`)")

    def __str__(self):
        if len(self.__callpath):
            descr = '.'.join(self.__callpath[1:])
        else:
            descr = self.__dlref
        return f"[object {descr}]"


    if not __PKPY__:

        def __all(self, *argv, **env):
            self.__serial += 1
            return self.__call__(f"C{self.__serial}", self.__lastc, *argv, **env)

        def __getattr__(self, attr):
            if not len(self.__callpath):
                self.__serial = self.__serial + 1
                self.__callpath.append(f"C{self.__serial}")
                self.__callpath.append(self.__dlref)
            self.__callpath.append(attr)
            return self

window = ProxyType('window')
print("window=", window, id(window))
document = ProxyType('document')

try:
    import readline
except:
    print("readline module not found")


################################################################################
################################################################################
################################################################################
''')

import platform
print("platform.window.console=", platform.window.console)
platform.window.console.log(" ---------- PROXY -------------------")

embed.new_module("asyncio", '''
self = __import__(__name__)
tasks : list = []
loop : object = None

def create_task(task):
    self.tasks.append(task)

def get_event_loop():
    if self.loop is None:
        self.loop = self
    return self.loop

get_running_loop = get_event_loop

def is_closed():
    return len(self.tasks)==0

if 0:
    def iterloop():
        frame : int = 0
        while tasks:
            for task in self.tasks:
                if next(task) is StopIteration:
                    self.tasks.remove(task)
                frame += 1
                yield frame

    def step():
        for task in self.tasks:
            itrv = next(task, 0xfeedc0de)
            if itrv == 0xfeedc0de:
                self.tasks.remove(task)
else:
    frame : int = 0

    def step():
        global frame
        for task in self.tasks:
            if next(task) is StopIteration:
                self.tasks.remove(task)
        frame += 1


def run(task, block=None):
    tasks.append(task)

    if block is None:
        try:
            sys._emscripten_info
        except:
            block = True

    if not block:
        return
    while tasks:
        step()


''')

import asyncio



def shelltry(*cmd):
    if hasattr(shell, cmd[0] ):
        rv = getattr(shell, cmd[0])(*cmd[1:])
        if rv is not None:
            for line in rv:
                print(line)
        return False
    return True



out = sys.__stdout__.write
damages = {}
bname_last = 0
anchor_last = 0

class Tui:
    # use direct access, it is absolute addressing on raw terminal.
#    out = out
    decvssm = False

    # save cursor
    def __enter__(self):
        # ESC("7","[?25l","[?69h")
        #        self.out("\x1b7\x1b[?25l\x1b[?69h")
        out("\x1b7")
        #        self.out("\x1b7\x1b[?25l")
        return self

    # restore cursor
    def __exit__(self, *tb):
        # ESC("[?69l","8","[?25h")
        #        self.out("\x1b[?69l\x1b8\x1b[?25h")
        out("\x1b8")
        out(sys.__eot__)
        #        self.out("\x1b8\x1b[?25h")
        pass

    def __call__(self, *a, **kw):
        global bname_last, anchor_last

        x :int = kw.get("x", 1)
        z :int = kw.get("z", 1)

        #   most term do not deal properly with vt400
        #            if decvssm:
        #                CSI(f"{x};{999}s")
        #                CSI(f"{z};{x}H\r")

        if not isinstance(a[0], str):
            import rich, io

            sio = io.StringIO()
            rich.print(*a, file=sio)
            sio.seek(0)
            block = sio.read()
        else:
            block = " ".join(a)

        # so position line by line
        filter = kw.get("filter", None)

        bname_last = 0
        anchor_last = 0

        for row in block.split("\n"):
            hr_old = damages.get(z, 0)
            hr = hash(row)
            if hr != hr_old:
                damages[z] = hr
                if filter:
                    # destroy event list ref by the old line
                    evpos.setdefault(z, {}).pop(hr_old, None)
                    evpos[z][hr] = []
                    row = filter(row, x, 0, z)

                #Tui.out("\x1b[{};{}H{}".format(z, x, row))
                sys.__stdout__.write(f"\x1b[{z};{x}H{row}")

            z += 1



def main():
    line = "\n"
    tui = Tui()

    while line not in ["exit()","quit()"]:
        if not asyncio.frame % 60:
            window.document.title = f"Frame={asyncio.frame}"

        with tui as tui:
            tui(f"Frame={asyncio.frame}\n", x=70,y=1, z=25)


        if line:
            line = line.rstrip()
            fail = False
            if line:
                try:
                    _=eval(line)
                    if _ is not None:
                        print(_)
                except NameError:
                    fail = shelltry(*line.split(" "))
                except SyntaxError:
                    try:
                        exec(line, globals())
                    except SyntaxError:
                        fail = shelltry(*line.split(" "))
                    except:
                        sys.print_exception()
                if fail:
                    sys.print_exception()
                print()
            print('>>> ',end=sys.__eot__)
        yield 0
        line = embed.readline()
    print("bye")


from platform import window, document

asyncio.get_running_loop().create_task(main())


pkpyrc = 1

