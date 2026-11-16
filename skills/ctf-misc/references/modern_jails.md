# Modern jails (2026) — beyond pyjail

Authors now gate code-execution challenges with ML classifiers and non-Python
runtimes to resist auto-solve. Patterns seen in-window (UIUCTF, scriptCTF, L3akCTF).

## (a) ML-classifier / CNN pre-filtered jails
A model (often a small CNN over the raw bytes, shipped as safetensors / a pickled
`state_dict`) scores your input and rejects anything it flags as malicious before
the interpreter ever runs it.

**Approach — adversarial evasion:**
1. **Reproduce the model offline.** Load the weights with NumPy/safetensors (or
   PyTorch) and reimplement the forward pass. Now you can test payloads for free.
2. **Perturb the payload to drop the malicious logit while keeping semantics:**
   - block comments / dead strings to shift the byte histogram,
   - string concatenation (`'o'+'s'`) and `getattr` indirection,
   - `\uXXXX` / `\xNN` escapes for key tokens,
   - **identifier-ignorable Unicode code points** inside identifiers
     (e.g. `U+008A`, `U+0013`, zero-width joiners) — Python treats them as part of
     the name but they move the classifier's input distribution.
3. Search (hill-climb / random perturbation) against your offline copy until the
   score is below threshold, then submit once.

## (b) Non-Python jails
### Java
- Goal: defeat `SecurityManager`. Use reflection to reach a private field:
  `Class.getDeclaredFields0(false)` → locate and **null `System.security`** → the
  manager is gone → `Runtime.getRuntime().exec(...)`.
- Also: unsafe deserialization gadgets, `ProcessBuilder`, JNI if a `.so` is loaded.

### Emacs Lisp (native-compile)
- The jail native-compiles your Lisp and then runs a **Capstone** check over the
  produced machine code (rejecting call/jmp to forbidden targets).
- Escape at **compile time**, before that check: a `featurep` **compiler macro**
  that performs `(eval form)` runs during compilation, so your payload executes
  while the file is being compiled — ahead of the output inspection.

## (c) Traceback source-leak
When you can't exec but Python prints tracebacks, force an *uncaught* exception so
the traceback dumps the surrounding source lines (which contain the flag/check):
- huge integer into a `float` operation → `OverflowError`, or
- a crafted modulo/division → `ZeroDivisionError` (e.g. `1.0 % 0`), or
- a type confusion that raises inside the checker.
Often placed behind a PoW — solve the PoW (`pow_solver.py`), then trigger the crash.

## Tooling
- `python3 -c "import numpy, safetensors" 2>/dev/null || pip install --user numpy safetensors` (reproduce the classifier); PyTorch if the
  model needs it. Java: a JDK (`command -v javac >/dev/null || sudo pacman -S jdk-openjdk`). Emacs:
  `command -v emacs >/dev/null || sudo pacman -S emacs`. `command -v cshatag >/dev/null || paru -S capstone` to mirror the output check.
