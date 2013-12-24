#!/usr/bin/env python
""" Export
"""
import os
import csv
import logging
import argparse
from bs4 import BeautifulSoup

HEADER = [
    'Id',
    'MatchCode',
    'ContactType',
    'FranchiseLocation',
    'ZeeContactName',
    'ZeeContactPhoneNumber',
    'FirstName',
    'LastName',
    'Organization',
    'PhoneNumber',
    'Unit #',
    'Street #',
    'Street Name',
    'Street Type',
    'Direction',
    'City',
    'Province',
    'PostalCode',
    'LeadType',
    'AssignTo',
    'AskingPrice',
    'CommissionPlusTax',
    'CPStatus'
]

#
# Export
#
class Export(object):
    """ Sync
    """
    def __init__(self, folder='www.realtor.ca', loglevel=logging.INFO):

        self.running = False
        self.loglevel = loglevel

        self._folder = None
        if folder:
            self._folder = folder
        self._logger = None
        self._database = None
        self._path = None
        self._logfile = None

    @property
    def logger(self):
        """ Logger
        """
        if self._logger:
            return self._logger

        # Setup logger
        self._logger = logging.getLogger('export')
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
            self._folder = u"output"

        if not os.path.exists(self._folder):
            raise IOError("Invalid folder: %s", self._folder)

        return self._folder

    @property
    def path(self):
        """ Path
        """
        if self._path is None:
            self._path = os.path.join(self.folder, self.folder + u'.csv')
        return self._path

    @property
    def logfile(self):
        """ Log file
        """
        if self._logfile is None:
            self._logfile = os.path.join(self.folder, self.folder + u'.export.log')
        return self._logfile

    @property
    def playlist(self):
        """ Songs playlist
        """
        for item in os.listdir(self.folder):
            try:
                item = int(item)
            except ValueError:
                continue
            else:
                yield item

    def get_filename(self, item):
        """ Get filename from header
        """
        filename = os.path.join(self.folder, "%d" % item)
        return filename

    def autosave(self, action='Ctrl+C'):
        """ Save database from time to time
        """
        self.logger.debug("Autosave: %s", action)

    def start(self, **kwargs):
        """ Start sync
        """
        idx = 0
        self.running = True
        writer = csv.writer(open(self.path, 'w'))
        writer.writerow(HEADER)

        for item in self.playlist:
            row = [item]

            path = self.get_filename(item)

            html = ""
            with open(path, "r") as html:
                html = html.read()

            soup = BeautifulSoup(html)

            # MatchCode
            match = soup.find_all("td", {'class': "MainHeadingLeft"})
            match = ''.join(x.get_text().strip() for x in match)
            match = match.replace(u'MLS\xae:', u'').strip()
            row.append(match.encode('utf-8'))

            self.logger.info('Adding row to %s: %s', self.path, match)

            # ContactType
            match = soup.find_all("td", {'class': "Designation"})
            match = match[0].get_text().strip() if len(match) else u''
            row.append(match.encode('utf-8'))

            # FranchiseLocation
            row.append('')

            # ZeeContactName
            row.append('')

            # ZeeContactPhoneNumber
            row.append('')

            # FirstName
            match = soup.find_all("div", {'id': "_ctl0_elRealtor3_rptRealtors_pnlAgentInfo_0"})
            match = match[0].get_text().strip() if len(match) else u' '
            match = match.split('\r\n')[0]
            first, last = match.split(u' ', 1)
            row.append(first.encode('utf-8'))

            # LastName
            row.append(last.encode('utf-8'))

            # Organization
            match = soup.find_all("td", {'class': "Label"})
            match = match[1].get_text().strip() if len(match) > 1 else u""
            row.append(match.encode('utf-8'))

            # PhoneNumber
            match = soup.find_all('table', {'class': 'SubTable'})
            tr = u''
            if len(match):
                tr = match[0].find_all('tr')
                for x in tr:
                    text = x.get_text()
                    if 'Telephone' in x.get_text():
                        tr = text.replace('Telephone: ', '').strip()
                        break
            row.append(tr.encode('utf-8'))

            # Unit #
            match = soup.find_all('div', {'class': 'PropDetailsSummaryValue'})
            match = match[0].get_text().strip() if len(match) else u""
            row.append(match.encode('utf-8'))

            # Street #
            labels = soup.find_all('div', {'class': 'PropDetailsSummarySpecText'})
            idx = [idx for idx, label in enumerate(labels) if 'location' in label.get_text().lower()]
            idx = idx[-1] if len(idx) else None

            details = soup.find_all('div', {'class': 'PropDetailsSummaryValue'})
            if idx is not None and len(details) > idx:
                location = details[idx]
                location = location.get_text().strip()
            else:
                location = u''

            row.append(location.encode('utf-8'))

            # Street Name
            row.append('')

            # Street Type
            row.append('')

            # Direction
            row.append('')

            # City
            row.append('')

            # Province
            row.append('')

            # PostalCode
            row.append('')

            # LeadType
            row.append('')

            # AssignTo
            row.append('')

            # AskingPrice
            price = soup.find_all('td', {'class': 'MainHeadingRight'})
            price = ''.join(x.get_text().strip() for x in price)

            action, price = [x.strip() for x in price.split(":", 1)]
            action = action.replace('For ', '')

            um = ''
            if '/' in price:
                price, um = [x.strip() for x in price.split('/')]

            row.append(price)

            # CommissionPlusTax
            row.append('')

            # CPStatus
            row.append('')

            writer.writerow(row)

    def stop(self, error=None, **kwargs):
        """ Close files and exit
        """
        if error:
            self.logger.exception(error)
        self.autosave()
        self.running = False

    __call__ = start

def main(*a, **kw):
    """ Main server
    """
    cmd = argparse.ArgumentParser(u"Export: parse html into CSV\n")

    cmd.add_argument("-D", "--no-debug",
                         action='store_const', const=True, default=False,
                         help=u"Don't show debug messages")

    cmd.add_argument("-f", "--folder", default=u"",
                     help=u"Input directory")

    args = cmd.parse_args()
    cmd.print_help()

    LOGLEVEL = logging.DEBUG if not args.no_debug else logging.INFO

    options = {
        'loglevel': LOGLEVEL,
    }

    if args.folder:
        options['folder'] = args.folder

    server = Export(**options)

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
    except Exception as error:
        server.stop(error)


if __name__ == "__main__":
    main()
