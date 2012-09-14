#!/usr/bin/python2.3
# -*- coding: utf-8 -*-

# Copyright (c) 2009-2012, Rémy J. A. Mouëza. 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Rémy J. A. Mouëza (the author) nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os, sys

# Helpers ---------------------------------------------
def updated (d, **ks):
    r = d.copy ()
    r.update (ks)
    return r

# Partial function application.
partial = (lambda f, *ca, **ck:
                  lambda *fa, **fk: f (*(ca + fa), **updated (ck, **fk)))

# builds singletons classes/objects. 
make = lambda nm, *bs, **attr: type (nm, bs, attr) ()


class F (object):
    # A "super", possibly partial, function.
    def __init__ (self, f = None, *a, **k): 
        self.f = f or (lambda x: x)
        if a or k: 
            self.f = partial (f, *a, **k)
    __pow__ = lambda s, x: type (s) (x)

    # function composition: f >> g == lambda x: f (g (x))
    __rshift__  = lambda s, g: F (lambda *a, **k: g (s.f (*a, **k)))
    __rrshift__ = lambda s, g: F (lambda *a, **k: s.f (g (*a, **k)))
    # function call: f (x) <=> f | x
    __call__    = lambda s, *a, **k: s.f (*a, **k)
    __or__      = __call__
    # Partial application: f [x] <=> partial (f, x)
    __getitem__ = lambda s, *a: F (s.f, *a) # Partial function call
    # Boolean logic: * <=> and, + <=> or
    __mul__  = lambda s, f: F (lambda *a, **ks: s.f (*a, **ks) and   f (*a, **ks))
    __add__  = lambda s, f: F (lambda *a, **ks: s.f (*a, **ks)  or   f (*a, **ks))
    __rmul__ = lambda s, f: F (lambda *a, **ks:   f (*a, **ks) and s.f (*a, **ks))
    __radd__ = lambda s, f: F (lambda *a, **ks:   f (*a, **ks)  or s.f (*a, **ks))
F = F (F)

uncurry = F (lambda f: F (lambda a: f (*a)))
idf = fid = lift = F (lambda x: x)

# >>> map (get [0], [('a', 1), ('b', 2)])
# ['a', 'b']
get = make ('get', 
            __getitem__ = lambda s, k: F (lambda this: this [k]), 
            __getattr__ = lambda s, k: F (lambda this: getattr (this, k)))

# >>> map (call.split (', '), ["hello, world"])
# [['hello', 'world']]
call = make ('call', 
             __getattr__ = lambda s, fn: 
                                  lambda *a, **k: 
                                         F (lambda this: getattr (this, fn) (*a, **k)))

begin = lambda *args: args [-1]
disp  = lambda x: begin (sys.stderr.write ("%s\n" % str (x)), x)

# >>> seq.sorted (compareOn (get [1])) | [(1, 2), (2, 1)]
seq = make ('seq', 
            __getattr__ = lambda s, nm:
                                 F (lambda *a , **ks: 
                                           F (lambda this: 
                                                     begin (getattr (this, nm) (*a, **ks), 
                                                            this))))
notF = lambda f: lambda *a, **ks: not f (*a, **ks)
notV = F (lambda v: not v)
isNone = F (lambda v: v is None)
notNone = isNone >> notV

def fork (*args): 
    def branches (parameters): 
        assert len (parameters) == len (args)
        return tuple ([function (parameter) for function, parameter in zip (args, parameters)])
    return F (branches)
fork = F | fork 

def dup (times): 
    def duplicate (item): 
        return [item] * times 
    return F (duplicate)
dup = F | dup

null  = make ('null', __getattr__ = lambda s, k: s        # null.whatever   == null
                    , __getitem__ = lambda s, k: s        # null [whatever] == null
                    , __call__    = lambda s, *a, **k: s  # null.whatever (any, thing, ...) == null
                    , __repr__    = lambda s: '<null>'    # str (null) == <null>
                    , __iter__    = lambda s: iter ([])   # list (null) == <null> | for each in null -> exit the loop
                    , __nonzero__ = lambda s: False       # if null -> always false
                    , __bool__    = lambda s: False)      # bool (null) == false 

def mayben (x): # a -> a | null
    if not x:
        return null
    return x
mayben = F (mayben)

def tryCatch (f, onError):
    try:
        return f ()
    except Exception, e:
        return onError (e)
    
const  = lambda x: lambda *a, **k: x
maybef = F (lambda f, default=None: lambda x: tryCatch (lambda: f (x), const (default)))

flip = lambda f: lambda *a, **ks: f (*a [::-1], **ks)

def rightOperandType (nm, bs, ks):
    import operator
    getWrapped = lambda fn: lambda s, x: F (fn, x)
    
    for nm, v in vars (operator).items (): 
        if callable (v):
            ks [nm] = getWrapped (v)
    
    return type (nm, bs, ks)
rop = rightOperandType ('rop', (object,), {}) ()

def leftOperandType (nm, bs, ks):
    import operator
    getWrapped = lambda fn: lambda s, x: F (flip (fn), x)
    
    for nm, v in vars (operator).items (): 
        if callable (v):
            ks [nm] = getWrapped (v)
    
    return type (nm, bs, ks)
op = leftOperandType ('op', (object,), {}) ()


def groupBy (groupingFunction, ls): 
    """ {Return a dictionary}
        groupBy :: (a -> b) -> [c] -> Dict b [c]

        groupingFunction (element : object) -> category : object (a key)
        ls : a list

        Returns the element of ls grouped using the groupingFunction in a dictionary: 
        {keys: the keys returned by the groupingFunction when given an element, 
         values: sub-list of the element of ls for which groupingFunction returns the same value}
        
        >> groupBy (lambda x: {0: "even", 1: "odd"} [x % 2], range (10))
        {"even": [0, 2, 4, 6, 8],
         "odd": [1, 3, 5, 7, 9]}
    """
    groups = {}
    for each in ls: 
        groups.setdefault (groupingFunction (each), []).append (each)
    return groups
groupBy = F | groupBy

def compareOn (getter): 
    """ Returns a comparison function :: (a -> b) -> (a -> a -> bool)
        
        Takes a getter and return a comparison function that uses cmp over the
        result of the getter applied to its two parameters:
        
        compareOn (lambda x: x.name) <=> lambda a, b: cmp (a.name, b.name)
    """
    return lambda a, b: cmp (getter (a), getter (b))


def find (f, xs, default=None): 
    """ Returns an object or the given default.
        :: (a -> Maybe b) -> [a] -> (Maybe b | default)
        
        Searches an x element in xs:
         - if f (x) returns a value that is evaluated to True using bool (x) we return that value,
         - when nothing is found, returns the given default.
    """
    for x in xs:
        value = f (x)
        if value: 
            return value
    else:
        return default
find = F | find

def readFile (nm):
    f = open (os.path.expanduser (nm))
    content = f.read (); f.close () 
    return content
F | readFile 

def Write (mode):
    def inFile (nm, content): 
        import os
        f = open (os.path.expanduser (nm), mode)
        f.write (content)
        f.close ()

    return F | inFile

writeFile = Write ('w')
addFile   = Write ('a')

# Make an object wrapper around some os.path functions (usefull when they are heavily used).  - Path 
# ('home/user/dir') / 'filename'   <=> os.path.join ('home/user/dir', 'filename') - p = Path ('a/b/c')
#       p.normpath () <=> os.path.normpath ('a/b/c')
#
# One can then chain calls to os.path function: 
#     Path ('a/b/c').dirname ().normpath ().realpath ().islink ()
# 
# Also define an empty (or null) path to easily create other path from it: 
#     path / 'path/to/somewhere'   <=> Path ('path/to/somewhere')
def wrapPath (f):
    """ Wrap a function from os.path """
    def delegate (s, *a, **k):
        """ Delegates a call to a function of os.path """
        r = f (s, *a, **k) # call the function.
        if isinstance (r, basestring):
            return type (s) (r) # Make it a Path instance if it's a string.
        return r
    return delegate

def metaPath (nm, bs, ks): 
    import os
    ks.update (dict ([(k, wrapPath (v)) 
                      for k, v in vars (os.path).items ()
                      if callable (v) and k not in dir (unicode)])) 
    return type (nm, bs, ks)

class Path (unicode): 
    """ A path object. 
    """
    __metaclass__ = metaPath
    # __new__    = lambda cls, value: unicode.__new__ (cls, value)
    __div__    = lambda s, x: Path (os.path.join (s, x))
    __rdiv__   = lambda s, x: Path (os.path.join (x, s))
    __call__   = lambda s, x: type (s) (x)
    __or__     = __call__

    # def __getattribute__ (s, k): 
    #     f = getattr (os.path, k, None)
    #     if f and callable (f): 
    #         return partial (wrapPath (f), s)
    #     return super (Path, s).__getattribute__ (k)

path = Path ("") # the "null" or empty path: use it to create bigger paths. 

class ostream :
    """ Defines a C++ like output stream with included pprint for debugging.
    
        cout = ostream ()
        cout << "strange value to debug:" << dicoToDebug << '\n'
        
    """
    def __init__ ( self, fileobj = sys.stderr ):
        self.fileobj = fileobj        
    def __repr__ ( self ): return "" 
    def __lshift__ ( self, data ):
        """ {Return self } 
        
            returns self to allow chaining :
            cout << "strange value to debug:" << dicoToDebug << '\n'
        """
        from pprint import pprint
        import types
        
        if isinstance ( data, str ):  self.fileobj.write ( data )        
        elif hasattr ( data, '__dict__' ):         
            # Use id ( data ) & 0xFFFFFFFFL to avoid to call hex on a negative number.
            # See http://mail.python.org/pipermail/python-list/2004-February/207093.html
            self << ( data.__class__.__name__ + " @ %x" % ( id ( data ) & 0xffffffffL ), data.__dict__ )
        else : pprint ( data, self.fileobj )
        
        return self
    write    = __lshift__
    __call__ = lambda s, a: [s << a, a] [-1]

cerr = ostream ()

import __builtin__
if 'set' not in dir (__builtin__):
    from sets import Set as set

if 'sorted' not in dir (__builtin__):
    sorted = F (lambda xs, cmpF=cmp: list >> get [:] >> seq.sort (cmpF) | xs)
try: 
    import mx.DateTime
    asDate = F | mx.DateTime.Parser.DateTimeFromString
except ImportError, e: 
    asDate = fid


intersperse = F (lambda x, xs: reduce (lambda a, b: a + [x, b], xs, []))
mapKeys = F (lambda f, dic: dict (zip (map (f, dic.keys ()), dic.values ()))) # (k -> k') -> {k -> v} -> {k' -> v}
mapVals = F (lambda f, dic: dict (zip (dic.keys (), map (f, dic.values ())))) # (v -> v') -> {k -> v} -> {k -> v'}


__splits = lambda c, xs: [x.split (c) for x in xs]
splitOn  = F (lambda xs, s: xs and reduce (lambda a, b: concat (__splits (b, a)), xs [1:], s.split (xs [0])) or s)

uzip = uncurry | zip 

# Flatten nested tuples.
# >>> from operator import setitem
# >>> [setitem (locals (), ltr, ltr) for ltr in "abcdefghijklmnopqrstuvwxyz"] # a = 'a'; b = 'b'; ...; z = 'z'
# >>> flatT ((a, b, (c, d), ((e, f, (g, h))), (i, j, (k, (l, (m, (n, (o, p))))), ((((q, r), s), t), u), v, w, x, y)))
# ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y')
flatT = F (lambda ts: tuple (reduce (lambda a, b: (not isinstance (b, tuple)) 
                                                    and a + [b] 
                                                     or a + list (flatT (b)), 
                                     ts, 
                                     [])))

def rlc ():
    try :
        import readline
    except ImportError :
        print "Module readline not available."
    else :
        # irlcompleter = imp.load_source ('irlcompleter', os.path.expanduser ('~/nobackup/ray/python/irlcompleter.py'))
        # import irlcompleter
        import rlcompleter
        readline.parse_and_bind ("set completion-ignore-case on")
        readline.parse_and_bind ("tab: complete")
        
        try :
            readline.read_history_file (os.path.expanduser ('~/.python_history'))
            import atexit
            atexit.register (lambda: __import__ ('readline').write_history_file (os.path.expanduser ('~/.python_history')))
        except Exception, e :
            print e

def extern (editor = 'gvim -f %s', delay=False):
    """ Edit some code in an external editor then excute it in the caller's context.
    """
    import os, sys, tempfile
    temporary = "%s/%s-%s.py" %  (tempfile.gettempdir (), tempfile.gettempprefix (), os.getpid ())
    os.system (editor % temporary)
    frames = [sys._getframe ().f_back]
    def thunk ():
        back = frames [0]
        exec open (temporary) in back.f_locals, back.f_globals
        del back
    if delay: 
        return thunk
    else: 
        thunk ()

def powerUp ():
    import sys
    # import mx.DateTime
    import __builtin__
    from fnmatch import fnmatch
    from glob    import glob
    import shutil
    env = sys._getframe (1).f_globals
    env.update (dict ( F            = F   
                     , bbool        = F | bool    
                     , ddict        = F | dict    
                     , ddir         = F | dir     
                     , ddisp        = F | disp    
                     , ffilter      = F | filter
                     , ffnmatch     = F | flip (fnmatch)
                     , hhelp        = F | help    
                     , iisinstance  = F | isinstance 
                     , llen         = F | len     
                     , llist        = F | list    
                     , mmap         = F | map
                     , rreduce      = F | reduce
                     , rreload      = F | reload  
                     , rrepr        = F | repr    
                     , sset         = F | set     
                     , sstr         = F | str     
                     , ttuple       = F | tuple   
                     , vvars        = F | vars 
                     , zzip         = F | zip 
                     , addFile      = addFile     
                     , asDate       = asDate
                     , call         = call        
                     , cerr         = cerr
                     , compareOn    = compareOn
                     , const        = const       
                     , disp         = disp        
                     , dup          = dup         
                     , extern       = extern
                     , fid          = fid         
                     , find         = find
                     , flatT        = flatT 
                     , flip         = flip        
                     , fork         = fork        
                     , get          = get         
                     , glob         = glob
                     , groupBy      = groupBy
                     , idf          = idf         
                     , intersperse  = intersperse 
                     , isNone       = isNone      
                     , mapKeys      = mapKeys     
                     , mapVals      = mapVals     
                     , maybef       = maybef      
                     , mayben       = mayben      
                     , notF         = notF        
                     , notNone      = notNone     
                     , notV         = notV        
                     , null         = null        
                     , op           = op          
                     , partial      = partial     
                     , path         = path        
                     , readFile     = readFile    
                     , rlc          = rlc
                     , rop          = rop         
                     , seq          = seq         
                     , shutil       = shutil 
                     , splitOn      = splitOn     
                     , tryCatch     = tryCatch
                     , uncurry      = uncurry     
                     , uzip         = uzip        
                     , writeFile    = writeFile   
                     ))

powerUp ()
