// Ghidra headless post-script: dump decompiled C for every function.
// Usage:
//   analyzeHeadless /tmp/ghproj proj -import ./chall \
//       -postScript DecompileAll.java -scriptPath <dir-of-this-file> -deleteProject
// Output goes to stdout; redirect to a file:  ... > decomp.c
// @category CTF

import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DecompileAll extends GhidraScript {
    @Override
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Function f = it.next();
            DecompileResults res = ifc.decompileFunction(f, 60, monitor);
            if (res != null && res.decompileCompleted()) {
                println("// ==== " + f.getName() + " @ " + f.getEntryPoint());
                println(res.getDecompiledFunction().getC());
            }
        }
        ifc.dispose();
    }
}
