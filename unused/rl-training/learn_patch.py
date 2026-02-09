# learn_patch.py
import cattr

# ML-Agents calls cattr.register_structure_hook(...) at import time.
_old = cattr.register_structure_hook

def _patched_register_structure_hook(cl, func):
    # If it's typing.Dict[...], translate to runtime dict class
    origin = getattr(cl, "__origin__", None)
    if origin is dict:
        return _old(dict, func)
    return _old(cl, func)

cattr.register_structure_hook = _patched_register_structure_hook

from mlagents.trainers.learn import main

if __name__ == "__main__":
    main()
