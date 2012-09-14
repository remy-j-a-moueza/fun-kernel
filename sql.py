#!/usr/bin/python
#-*- coding: utf-8 -*-

# Copyright (c) 2011, Rémy J. A. Mouëza. 
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
# Add kernel.py directory to the path, if not installed system wise.
# sys.path.append (os.path.expanduser ('~/lib'))
import kernel
kernel.powerUp ()

import MySQLdb

conn = MySQLdb.connect (host   = "host",
                        user   = "user",
                        passwd = "password",
                        db     = "db")

@F
def select (sql):
    cur  = conn.cursor ()
    cur.execute (sql)
    desc = mmap [get [0]] | cur.description 
    return mmap [zzip [desc] >> dict] | cur.fetchall ()

@F
def escape (value):
    if isinstance (value, basestring):
        return "'%s'" % reduce (lambda s, (mch, rpl): s.replace (mch, rpl), 
                                [("'", "''"), (";", "")], 
                                value)
    if isinstance (value, bool):
        return "'1'" if value else "'0'"
    if isinstance (value, (int, long)):
        return "%d" % value
    if isinstance (value, float):
        return "%f" % value
    return str (value)

@F
def insert (table, **kw): 
    try:
        conn.cursor ().execute (
             ddisp |
             "INSERT INTO %s(%s) VALUES(%s)" 
                   % (table,
                      ", ".join (kw.keys ()), 
                      ", ".join (mmap [escape] | kw.values ())))
        conn.commit ()
    except Exception, e:
        conn.rollback ()
        raise e

@F
def update (table, where, **kw):
    try:
        conn.cursor ().execute (
             ddisp |
             "UPDATE %s SET %s WHERE %s" 
                   % (table,
                      mmap [rop % "%s = %s"] 
                      >> ", ".join 
                      | zip (kw.keys (), 
                             mmap [escape] | kw.values ()),
                     where))
    except Exception, e:
        conn.rollback ()
        raise e

