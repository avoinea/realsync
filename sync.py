#!/usr/bin/env python
""" Sync
"""
import sys
import time
import os
import urllib2
import logging
import json
import argparse
from urllib2 import urlparse
from random import randint, choice
from proxy import PROXIES
from browser import AGENTS
#
# Sync
#
class Sync(object):
    """ Sync
    """
    def __init__(self, begin=10000000, end=20000000,
        template='http://www.realtor.ca/PropertyDetails.aspx?&PropertyId=%s',
        folder=None, sleep=1, loglevel=logging.INFO, proxy=True):

        self.begin = begin
        self.end = end
        self.template = template
        self.sleep = sleep
        self.proxy = proxy
        self.running = False

        self.loglevel = loglevel

        self._folder = None
        if folder:
            self._folder = folder

        self._logger = None

        self._database = None
        self._valid = None
        self._invalid = None
        self._path = None
        self._logfile = None


    @property
    def logger(self):
        """ Logger
        """
        if self._logger:
            return self._logger

        # Setup logger
        self._logger = logging.getLogger('sync')
        self._logger.setLevel(self.loglevel)
        fh = logging.FileHandler(self.logfile)
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        self._logger.addHandler(fh)
        self._logger.addHandler(ch)
        return self._logger

    @property
    def folder(self):
        """ Output folder
        """
        if not self._folder:
            parser = urlparse.urlparse(self.template)
            self._folder = parser.netloc if parser.netloc else u"output"

        if not os.path.exists(self._folder):
            os.makedirs(self._folder)

        return self._folder

    @property
    def path(self):
        """ Path
        """
        if self._path is None:
            self._path = os.path.join(self.folder, self.folder + u'.json')
        return self._path

    @property
    def logfile(self):
        """ Log file
        """
        if self._logfile is None:
            self._logfile = os.path.join(self.folder, self.folder + u'.sync.log')
        return self._logfile

    def initialize(self):
        """ Init database
        """
        if not os.path.exists(self.path):
            json.dump({}, open(self.path, "w"), indent=2)

    @property
    def database(self):
        """ Database
        """
        if not self._database:
            if not os.path.exists(self.path):
                self.initialize()
            self._database = json.load(open(self.path, 'r'))
        return self._database

    @property
    def valid(self):
        """ Get valid ids
        """
        if self._valid is None:
            valid = self.database.get('valid', None)
            if valid is None:
                valid = self.database['valid'] = ()
            self._valid = set(valid)
        return self._valid

    @property
    def invalid(self):
        """ Invalid ids
        """
        if self._invalid is None:
            invalid = self.database.get('invalid', None)
            if invalid is None:
                invalid = self.database['invalid'] = ()
            self._invalid = set(invalid)
        return self._invalid

    @property
    def playlist(self):
        """ Songs playlist
        """
        while self.running:
            play = randint(self.begin, self.end)
            if self.exists(play):
                continue
            yield play

    @property
    def headers(self):
        """ Headers
        """
        agent =  choice(AGENTS)
        return {
            'User-Agent' : agent
        }

    def changeProxy(self):
        """ Proxy
        """
        if not self.proxy:
            return ''

        proxy = choice(PROXIES.keys())
        typo = PROXIES[proxy]

        self.logger.debug('Using proxy: %s', proxy)
        proxy = urllib2.ProxyHandler({typo: proxy})

        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)

    def get_filename(self, default):
        """ Get filename from header
        """
        filename = os.path.join(self.folder, "%d" % default)
        return filename

    def get_length(self, connection):
        """ Get file length
        """
        headers = dict(connection.headers)
        length = headers.get('content-length')
        try:
            length = float(length)
        except (TypeError, ValueError):
            length = 1.0
        return length

    def exists(self, name):
        """ File exists
        """
        if name in self.invalid or name in self.valid:
            return True
        return False

    def autosave(self, action='Ctrl+C'):
        """ Save database from time to time
        """
        self.logger.debug("Autosave: %s", action)
        self._database = {
            'valid': tuple(self.valid),
            'invalid': tuple(self.invalid)
        }
        json.dump(self.database, open(self.path, "w"), indent=2)

    def start(self, **kwargs):
        """ Start sync
        """
        idx = 0
        self.running = True
        for house in self.playlist:
            if idx % 100 == 0:
                self.changeProxy()
                self.autosave(idx)

                self.logger.debug("Sleeping for %d. Zzzz ...", self.sleep)
                time.sleep(self.sleep)
            idx += 1

            filename = self.get_filename(house)
            url = self.template % house
            request = urllib2.Request(url, headers=self.headers)

            try:
                conn = urllib2.urlopen(request, timeout=10)
            except Exception as err:
                self.logger.exception(err)
                continue
            else:
                if "%s" % house not in conn.url:
                    data = "Your search did not return any results."
                else:
                    data = conn.read()
                conn.close()

            if "Your search did not return any results" in data:
                self.logger.info("Invalid:	%s", house)
                self.invalid.add(house)
                continue

            self.logger.info("Valid:	%s", house)
            self.valid.add(house)
            open(filename, 'w').write(data)

    def stop(self, error=None, **kwargs):
        """ Close files and exit
        """
        if error:
            self.logger.exception(error)
        self.autosave()
        self.running = False

    __call__ = start

def main(*a, **kw):

    cmd = argparse.ArgumentParser(u"Sync: easy grab pages with int ids\n")

    cmd.add_argument("-N", "--no-proxy",
                     action='store_const', const=True, default=False,
                     help=u"Don't use proxies")

    cmd.add_argument("-D", "--no-debug",
                         action='store_const', const=True, default=False,
                         help=u"Don't show debug messages")

    cmd.add_argument("-t", "--template", default=u"",
                     help=u"Url template. e.g.: http://example.com/x/y?id=%%s")

    cmd.add_argument("-f", "--folder", default=u"",
                     help=u"Output directory")

    cmd.add_argument("-b", "--begin", type=int, default=13000000,
                     help=u"Begining int for ids range")

    cmd.add_argument("-e", "--end", type=int, default=14000000,
                         help=u"Ending int for ids range")

    args = cmd.parse_args()
    cmd.print_help()

    proxy = True if not args.no_proxy else False
    LOGLEVEL = logging.DEBUG if not args.no_debug else logging.INFO

    options = {
        'loglevel': LOGLEVEL,
        'proxy': proxy
    }

    if args.template:
        options['template'] = args.template

    if args.folder:
        options['folder'] = args.folder

    if args.begin:
        options['begin'] = args.begin

    if args.end:
        options['end'] = args.end

    server = Sync(**options)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
    except Exception as error:
        server.stop(error)


if __name__ == "__main__":
    main()
