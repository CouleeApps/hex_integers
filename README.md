# Hex Integer Display
A simple python displayhook wrapper for printing ints in hex. Works on nested types, like
arrays, tuples, and dictionaries. Also prints the contents of generator objects.

    # Prints integers as hex
    >>> 123
    123 / 0x7b
    
    # Decimal printing is optional (see Settings)
    >>> 123
    0x7b
    
    # Works on both the repl and the print function 
    >>> print(123)
    123 / 0x7b
    
    # Lists, dicts, and tuples supported 
    >>> list(range(10))
    [0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9]
    
    # Generator unwrapping, because why not?
    >>> bv.functions
    (generator FunctionList) [<func: x86@0x401005>,
     <func: x86@0x40100a>,
     <func: x86@0x40100f>,
     <func: x86@0x40101e>,
     ...]