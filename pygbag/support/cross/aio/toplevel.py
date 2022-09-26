import sys
import aio

# import textwrap

# https://bugs.python.org/issue34616
# https://github.com/ipython/ipython/blob/320d21bf56804541b27deb488871e488eb96929f/IPython/core/interactiveshell.py#L121-L150

#async_skeleton = """
##==========================================
#async def retry_async_wrap():
#    __snapshot = list( locals().keys() )
#{}
#    maybe_new = list( locals().keys() )
#    while len(__snapshot):
#        try:maybe_new.remove( __snapshot.pop() )
#        except:pass
#    maybe_new.remove('__snapshot')
#    while len(maybe_new):
#        new_one = maybe_new.pop(0)
#        print(new_one , ':=', locals()[new_one])
#        setattr(__import__('__main__'), new_one , locals()[new_one] )
##==========================================
#"""
#
#
#async def retry(code, sysinfo):
#    global may_have_value
#    may_have_value = code.startswith("await ")  # will display value
#    try:
#        code = "builtins._ = {}".format(code)
#        code = async_skeleton.format(" " * 4 + code)
#        bytecode = compile(code, "<asyncify>", "exec")
#        # sys.stdout.write(f':async:  asyncify "[code stack rewritten]"\n')
#
#        exec(bytecode, vars(__import__("__main__")), globals())
#        await retry_async_wrap()
#
#        # success ? clear all previous failures
#        if may_have_value:
#            if builtins._ is not None:
#                sys.stdout.write("%r\n" % builtins._)
#
#    except Exception as e:
#        # FIXME: raise old exception
#        sys.__excepthook__(*sysinfo)
#        sys.stdout.write(f":async: can't use code : {e}\n~~> ")
#        sys.print_exception(e)
#    finally:
#        # sys.ps1 = __ps1__
#        aio.prompt_request()




import asyncio
import ast
import code
import types
import inspect

class AsyncInteractiveConsole(code.InteractiveConsole):

    def __init__(self, locals, **kw):
        super().__init__(locals)
        self.compile.compiler.flags |= ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
        self.line = ""
        self.one_liner = None
        self.opts = kw
        self.coro = None

    def process_shell(self, shell, line, **env):
        catch = True
        for cmd in line.strip().split(";"):
            cmd = cmd.strip()
            if cmd.find(" ") > 0:
                cmd, args = cmd.split(" ", 1)
                args = args.split(" ")
            else:
                args = ()

            if hasattr(shell, cmd):
                fn = getattr(shell, cmd)

                try:
                    if inspect.isgeneratorfunction(fn):
                        for _ in fn(*args):
                            print(_)
                    elif inspect.iscoroutinefunction(fn):
                        aio.create_task(fn(*args))
                    elif inspect.isasyncgenfunction(fn):
                        print("asyncgen N/I")
                    elif inspect.isawaitable(fn):
                        print("awaitable N/I")
                    else:
                        fn(*args)

                except Exception as cmderror:
                    print(cmderror, file=sys.stderr)
            else:
                catch = shell.exec(cmd, *args, **env)

        return catch

    def runsource(self, source, filename="<stdin>", symbol="single"):
        try:
            code = self.compile(source, filename, symbol)
        except SyntaxError:
            if self.one_liner:
                shell = self.opts.get('shell', None)
                if shell and self.process_shell(shell, self.line):
                    return
            self.showsyntaxerror(filename)
            return False

        except (OverflowError, ValueError):
            # Case 1
            self.showsyntaxerror(filename)
            return False

        if code is None:
            # Case 2
            return True

        # Case 3
        self.runcode(code)
        return False

    def runcode(self, code):
        embed.set_ps1()
        self.one_liner = True
        self.warmup = None
        self.coro = None
        func = types.FunctionType(code, self.locals)
        try:
            self.coro = func()
        except SystemExit:
            raise

        except KeyboardInterrupt as ex:
            print(ex, file=sys.__stderr__)
            raise

        except ModuleNotFoundError as ex:
            importer = self.opts.get('importer', None)
            if importer:
                want = str(ex).split("'")[1]
                self.warmup = importer(want, ex, func)

        except BaseException as ex:
            if self.one_liner:
                shell = self.opts.get('shell', None)
                if shell and self.process_shell(shell, self.line):
                    return
            sys.print_exception(ex)


    def raw_input(self, prompt):
        maybe = embed.readline()
        if len(maybe):
            return maybe
        else:
            return None
        #raise EOFError


    async def interact(self):
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "

        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "--- "

        cprt = 'Type "help", "copyright", "credits" or "license" for more information.'


        self.write("Python %s on %s\n%s\n(%s)\n" %
                   (sys.version, sys.platform, cprt,
                    self.__class__.__name__))

        prompt = sys.ps1

        while not aio.exit:
            await asyncio.sleep(0)
            try:
                try:
                    self.line = self.raw_input(prompt)
                    if self.line is None:
                        continue
                except EOFError:
                    self.write("\n")
                    break
                else:
                    if self.push(self.line):
                        prompt = sys.ps2
                        embed.set_ps2()
                        self.one_liner = False
                    else:
                        prompt = sys.ps1

            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0

            if self.warmup is not None:
                await self.warmup

            if self.coro is not None:
                await self.coro


            embed.prompt()

        self.write('now exiting %s...\n' % self.__class__.__name__)
