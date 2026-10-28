"""OrchardIQ: Production-style Agentic Enterprise Analytics Platform."""

import sys

# Windows Python 3.10 WinError 1450 work-around for inspect / getfinalpathname
if sys.platform == "win32":
    try:
        import ntpath
        _orig_getfinalpathname = getattr(ntpath, "_getfinalpathname", None)
        if _orig_getfinalpathname is not None:
            def _safe_getfinalpathname(p):
                try:
                    return _orig_getfinalpathname(p)
                except OSError:
                    return str(p)
            ntpath._getfinalpathname = _safe_getfinalpathname
    except Exception:
        pass

# Ensure DLL libraries load in optimal memory order on Windows
try:
    import torch
except Exception:
    pass

try:
    import scipy.stats
except Exception:
    pass

__version__ = "0.1.0"
