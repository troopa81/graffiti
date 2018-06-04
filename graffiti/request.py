import time
from enum import Enum
from tqdm import trange
import shutil
import os
import requests


class Type(Enum):
    GetCapabilities = 1
    GetMap = 2


class Host(object):

    def __init__(self, name, host, payload={}):
        self.host = host
        self.name = name
        self.payload = payload


class Request(object):

    def __init__(self, name, type, hosts, iterations=50, desc='',
                 logdir=None, title=''):
        self.durations = {}
        self.type = type
        self.hosts = hosts
        self.iterations = iterations
        self.name = name
        self.desc = desc
        self.logdir = logdir
        self.title = title

    @property
    def hosts(self):
        return self._hosts

    @hosts.setter
    def hosts(self, hosts):
        self._hosts = hosts
        for i in range(0, len(self._hosts)):
            hosts[i].payload['REQUEST'] = self.type.name

            service = ''
            if self.type == Type.GetCapabilities or self.type == Type.GetMap:
                service = 'WMS'
            hosts[i].payload['SERVICE'] = service

    @staticmethod
    def build(cfg):
        iterations = cfg.iterations
        name = cfg.name
        title = cfg.title
        desc = cfg.description
        type = cfg.type
        logdir = cfg.logdir

        hosts = []
        for hostCfg in cfg.hosts:
            host = Host(hostCfg.name, hostCfg.host, hostCfg.payload)
            hosts.append(host)

        return Request(name, type, hosts, iterations, desc, logdir, title)

    def run(self):
        log = None
        if self.logdir:
            logfile = os.path.join(self.logdir, '{}.log'.format(self.name))
            log = open(logfile, 'w')

        for i in trange(len(self.hosts), leave=False, desc='Hosts'):
            host = self.hosts[i]
            dur = []

            if log:
                log.write(host.name)
                log.write('\n')
                log.write('    - HOST: \n'.format(host))
                for key in host.payload.keys():
                    log.write('    - {}: {}\n'.format(key, host.payload[key]))

            for j in trange(self.iterations, leave=False, desc='Iterations'):
                start = time.time()
                r = requests.get(host.host, params=host.payload, stream=True)

                if r.status_code != 200:
                    print("ERROR")
                    continue

                # log 1st iteration when it's an image (to be able to include
                # the figure in the long description)
                if self.logdir and j == 0 and 'FORMAT' in host.payload \
                        and 'png' in host.payload['FORMAT']:
                    imname = '{}.png'.format(self.name)
                    logres = os.path.join(self.logdir, imname)
                    with open(logres, 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)

                dur.append(round(time.time() - start, 4))

            self.durations[host.name] = dur

    def save(self, path):
        with open(path, 'w') as f:
            for host in self.hosts:
                f.write(host.name)
                f.write(' ')
                f.write(' '.join(map(str, self.durations[host.name])))
                f.write('\n')
