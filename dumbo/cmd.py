# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os

from dumbo.util import (dumpcode, Options, loadcode, dumptext, loadtext,
                        configopts, parseargs, execute, envdef, getconfigparser)
from dumbo.backends import create_filesystem


def dumbo(argv=sys.argv):
    if len(argv) < 2:
        print 'Usages:'
        print '  dumbo start <python program> [<options>]'
        print '  dumbo cat <path> [<options>]'
        print '  dumbo ls <path> [<options>]'
        print '  dumbo exists <path> [<options>]'
        print '  dumbo rm <path> [<options>]'
        print '  dumbo put <path1> <path2> [<options>]'
        print '  dumbo get <path1> <path2> [<options>]'
        print '  dumbo encodepipe [<options>]'
        print '  dumbo decodepipe [<options>]'
        print '  dumbo doctest <python program>'
        print '  dumbo version'
        print '  dumbo configdump'
        return 1
    if argv[1] == 'start':
        retval = start(argv[2], parseargs(argv[2:]))
    elif argv[1] == 'cat':
        retval = cat(argv[2], parseargs(argv[2:]))
    elif argv[1] == 'ls':
        retval = ls(argv[2], parseargs(argv[2:]))
    elif argv[1] == 'exists':
        retval = exists(argv[2], parseargs(argv[2:]))
    elif argv[1] == 'rm':
        retval = rm(argv[2], parseargs(argv[2:]))
    elif argv[1] == 'put':
        retval = put(argv[2], argv[3], parseargs(argv[3:]))
    elif argv[1] == 'get':
        retval = get(argv[2], argv[3], parseargs(argv[3:]))
    elif argv[1] == 'encodepipe':
        retval = encodepipe(parseargs(argv[2:]))
    elif argv[1] == 'decodepipe':
        retval = decodepipe(parseargs(argv[2:]))
    elif argv[1] == 'doctest':
        retval = doctest(argv[2])
    elif argv[1].endswith('.py'):
        retval = start(argv[1], parseargs(argv[1:]))
    elif argv[1] in ('version', '-v', '--version'):
        retval = version()
    elif argv[1] == 'configdump':
        retval = config_dump()
    else:
        print >> sys.stderr, 'ERROR: unknown dumbo command:', argv[1]
        retval = 1
    return retval


def start(prog,
          opts,
          stdout=sys.stdout,
          stderr=sys.stderr):

    opts = Options(opts)
    opts += Options(configopts('common'))
    opts += Options(configopts('start'))

    pyenv = envdef('PYTHONPATH', opts['libegg'],
                   shortcuts=dict(configopts('eggs', prog)),
                   extrapaths=sys.path)

    if not opts['prog']:
        opts.add('prog', prog)

    if not os.path.exists(prog):
        if prog.endswith(".py"):
            print >> sys.stderr, 'ERROR:', prog, 'does not exist'
            return 1
        prog = '-m ' + prog

    return execute("%s %s" % (sys.executable, prog),
                   opts,
                   pyenv,
                   stdout=stdout,
                   stderr=stderr,
                   printcmd=False)


def cat(path, opts):
    opts = Options(opts)
    opts += Options(configopts('common'))
    opts += Options(configopts('cat'))
    return create_filesystem(opts).cat(path, opts)


def ls(path, opts):
    opts = Options(opts)
    opts += Options(configopts('common'))
    opts += Options(configopts('ls'))
    return create_filesystem(opts).ls(path, opts)


def exists(path, opts):
    opts = Options(opts)
    opts += Options(configopts('common'))
    opts += Options(configopts('exists'))
    return create_filesystem(opts).exists(path, opts)


def rm(path, opts):
    opts = Options(opts)
    opts += Options(configopts('common'))
    opts += Options(configopts('rm'))
    return create_filesystem(opts).rm(path, opts)


def put(path1, path2, opts):
    opts = Options(opts)
    opts += Options(configopts('common'))
    opts += Options(configopts('put'))
    return create_filesystem(opts).put(path1, path2, opts)


def get(path1, path2, opts):
    opts = Options(opts)
    opts += Options(configopts('common'))
    opts += Options(configopts('get'))
    return create_filesystem(opts).get(path1, path2, opts)


def encodepipe(opts=None):
    opts = opts or Options()
    keys = ['addpath', 'file', 'alreadycoded']
    addedopts = opts.filter(keys)
    opts.remove(*keys)

    ofiles = addedopts['file']
    files = map(open, ofiles) if ofiles else [sys.stdin]

    loadfun = loadcode if addedopts['alreadycoded'] else loadtext
    addpath = addedopts['addpath']

    for _file in files:
        outputs = loadfun(line[:-1] for line in _file)
        if addpath:
            outputs = (((_file.name, key), value) for (key, value) in outputs)
        for output in dumpcode(outputs):
            print '\t'.join(output)
        _file.close()
    return 0


def decodepipe(opts=None):
    opts = opts or Options()
    ofiles = opts.pop('file')
    files = map(open, ofiles) if ofiles else [sys.stdin]

    for _file in files:
        outputs = loadcode(line[:-1] for line in _file)
        for output in dumptext(outputs):
            print '\t'.join(output)
        _file.close()
        return 0


def doctest(prog):
    import doctest
    sys.path.append(os.getcwd())
    failures = doctest.testmod(__import__(prog[:-3]))
    print '%s failures in %s tests' % failures
    return int(failures > 0)


def version():
    def get_version(project):
        try:
            import pkg_resources
            version = pkg_resources.require(project)[0].version
            return '{p} {v}'.format(p=project, v=version)
        except pkg_resources.DistributionNotFound:
            return '{p} not available'.format(p=project)

    print '{d} (with: {t}, {c})'.format(
        d=get_version('dumbo'),
        t=get_version('typedbytes'),
        c=get_version('ctypedbytes'),
    )
    return 0


def config_dump():
    parser = getconfigparser()
    parser.write(sys.stdout)
    return 0


if __name__ == '__main__':
    sys.exit(dumbo(sys.argv))
