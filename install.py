#!/usr/bin/env python3

import argparse
import json
import locale
import logging
import os
import random
import shutil
import sys
import textwrap
import urllib.request
import zipfile

# You can change these settings to your own preference

package_url = 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=999&x=id' \
              '%3Dbikioccmkafdpakkkcpdbppfkghcmihk%26installsource%3Dondemand%26uc '
icon_url = 'https://drive.google.com/uc?export=view&id=0B-sCqfnhKgTLbmdTSEpTaVVuRGM'

install_dir_user = os.path.dirname(os.path.abspath(__file__))
install_dir_root = "/opt/signal"
launcher_file_user = os.path.abspath(os.path.join(os.path.expanduser("~"), '.local/share/applications/signal.desktop'))
launcher_file_root = "/usr/share/applications/signal.desktop"
log_file_name = 'install.log'

# Do not make changes below this line, unless you know what you are doing
# ------------------------------------------------------------------------------

root = os.getuid() == 0
launcher_file = launcher_file_root if root else launcher_file_user
install_dir = install_dir_root if root else install_dir_user

logging.basicConfig(filename=os.path.join(install_dir, log_file_name), format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())  # also log to stderr


def log_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error('Uncaught exception', exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = log_exception

locale.setlocale(locale.LC_ALL, 'C.UTF-8')


class SignalInstaller(object):
    def __init__(self, install_dir_, package_url_, icon_url_, launcher_file_, log_file_name_, cron_):
        logging.info('----------------')
        if root:
            logging.info("Detected installation as root")
        else:
            logging.info("Detected installation as user")
        logging.info('Init')

        self.path = install_dir_
        self.package_url = package_url_
        self.icon_url = icon_url_
        self.launcher_file = launcher_file_
        self.cron = cron_

        self.icon_file_name = 'signal.png'
        self.package_file_name = 'signal.zip'
        self.log_file_name = log_file_name_

    def main(self):

        if self.path != os.path.dirname(os.path.abspath(__file__)):
            if not os.path.exists(self.path):
                os.makedirs(self.path, exist_ok=True)

            shutil.copy(os.path.abspath(__file__), self.path)

        installed_version = self.get_installed_version()
        latest_version = self.get_latest_version()

        if not installed_version or (latest_version > installed_version and latest_version[0] == '0'):
            logging.info('New version found, downloading')

            package_file = os.path.join(self.path, self.package_file_name)
            urllib.request.urlretrieve(self.package_url, package_file)

            if latest_version > installed_version:
                self.clean_old_files(self.path,
                                     [os.path.basename(__file__), self.icon_file_name, self.package_file_name,
                                      self.log_file_name])

            self.unpack(package_file)
            os.remove(package_file)

            if not installed_version:
                if self.launcher_file:
                    self.create_launcher()

                if self.cron:
                    self.create_cron_job()

        logging.info('Done')

    def unpack(self, file):
        logging.info('Unpacking ' + file)

        with zipfile.ZipFile(file) as z:
            z.extractall(self.path)

    def create_launcher(self):

        logging.info('Retrieving icon')
        icon_file = os.path.join(self.path, self.icon_file_name)
        urllib.request.urlretrieve(self.icon_url, icon_file)

        logging.info('Creating launcher')
        launcher = '''\
                        [Desktop Entry]
                        Exec=nw %(path)s
                        Icon=%(icon)s
                        Name=Signal
                        Path=
                        StartupNotify=true
                        Terminal=false
                        Type=Application
                    ''' % {'path': self.path, 'icon': icon_file}

        with open(self.launcher_file, 'w') as f:
            f.write(textwrap.dedent(launcher))

    def create_cron_job(self):
        logging.info('Creating cron job')

        job = '''\
                    # Signal Desktop updater
                    %(minute)i */6 * * * /usr/bin/env python3 %(path)s
                ''' % {'minute': random.randint(0, 59), 'path': os.path.join(self.path, os.path.basename(__file__))}

        os.system('(crontab -l 2>/dev/null; echo "%s") | crontab -' % textwrap.dedent(job))

    @staticmethod
    def clean_old_files(directory, exceptions=None):
        if exceptions is None:
            exceptions = []
        logging.info('Cleaning ' + directory)
        for f in os.listdir(directory):
            if f not in exceptions:
                logging.debug('Removing ' + f)
                f = os.path.join(directory, f)

                if os.path.isfile(f):
                    os.remove(f)
                elif os.path.isdir(f):
                    shutil.rmtree(f)

    @staticmethod
    def get_latest_version():
        tags_url = 'https://api.github.com/repos/WhisperSystems/Signal-Desktop/releases/latest'

        logging.info('Checking latest version')
        with urllib.request.urlopen(tags_url) as r:
            tags = json.loads(r.read().decode('utf-8'))
            version = tags['tag_name']
            version = ''.join(
                filter(lambda x: x.isdigit() or x == '.', version))  # remove everything except digits and dots

        logging.info('Latest version is ' + version)
        return version

    def get_installed_version(self):
        version = ''
        file = os.path.join(self.path, 'manifest.json')

        logging.info('Checking installed version')
        if os.path.isfile(file):
            try:
                with open(file, 'r') as f:
                    manifest = json.load(f)

                    if 'version' in manifest:
                        version = manifest['version']

            except OSError or IOError:
                logging.error('Can\'t read manifest ' + file)

        logging.info('Installed version is ' + version or 'none')
        return version


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--install-dir', '-d', help='Installation directory. Will be created if nonexistent.')
    parser.add_argument('--no-launcher', help='Don\'t create a .desktop file', action='store_true')
    parser.add_argument('--no-cron', help='Don\'t create a cron job for auto-updating', action='store_true')
    args = parser.parse_args()

    install_dir = args.install_dir or install_dir
    if root and args.install_dir is not None:
        os.mkdir(install_dir_root)
    launcher_file = None if args.no_launcher else launcher_file
    cron = not args.no_cron

    installer = SignalInstaller(install_dir, package_url, icon_url, launcher_file, log_file_name, cron)
    installer.main()
