#!/usr/bin/env python3

import os, getpass

# You can change these settings to your own preference

package_url = 'https://clients2.google.com/service/update2/crx?response=redirect&prodversion=999&x=id%3Dbikioccmkafdpakkkcpdbppfkghcmihk%26installsource%3Dondemand%26uc'
icon_url = 'https://drive.google.com/uc?export=view&id=0B-sCqfnhKgTLbmdTSEpTaVVuRGM'
launcher_file = os.path.join('/home', getpass.getuser(), '.local/share/applications/signal.desktop')


# Do not make changes below this line, unless you know what you are doing
# ------------------------------------------------------------------------------

import sys, shutil, urllib.request, json, random, textwrap, subprocess, logging, locale

logging.basicConfig(filename=os.path.join(sys.path[0], 'install.log'), format='%(asctime)s %(levelname)s: %(message)s', level = logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler()) # also log to stderr

def log_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error('Uncaught exception', exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = log_exception

locale.setlocale(locale.LC_ALL, 'C.UTF-8')


class SignalInstaller(object):
    def __init__(self, package_url, icon_url, launcher_file):
        logging.info('Init')

        self.path = sys.path[0]
        self.package_url = package_url
        self.icon_url = icon_url
        self.launcher_file = launcher_file

    def main(self):
        installed_version = self.getInstalledVersion()
        latest_version = self.getLatestVersion()

        if not installed_version or latest_version > installed_version:
            logging.info('New version found, downloading')

            package_file = os.path.join(self.path, 'signal.zip')
            urllib.request.urlretrieve(self.package_url, package_file)

            if latest_version > installed_version:
                self.cleanOldFiles(self.path, ['install.py', 'signal.png', 'signal.zip'])

            self.unpack(package_file)
            os.remove(package_file)

            if not installed_version:
                self.createLauncher()
                self.createCronJob()

        logging.info('Done')

    def unpack(self, file):
        logging.info('Unpacking')

        debug = logging.getLogger().isEnabledFor(logging.DEBUG)
        unzip_cmd = ['unzip', '' if debug else '-q', file, '-d', self.path]

        try:
            output = subprocess.check_output(unzip_cmd,
                                            stderr = subprocess.STDOUT,
                                            universal_newlines = True,
                                            timeout = 10)

            if output:
                logging.info(output)

        except subprocess.TimeoutExpired:
            logging.error('Timeout while unpacking, command was "%s"' % ' '.join(unzip_cmd))

        except subprocess.CalledProcessError as e:                                                                                                   
            if e.returncode == 1:
                logging.warning('Unpacked successfully, but there were some warnings:')
                logging.warning(e.output)
            else:
                logging.error(e.output)

    def createLauncher(self):

        logging.info('Retrieving icon')
        icon_file = os.path.join(self.path, 'signal.png')
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
                    ''' % { 'path': self.path, 'icon': icon_file }

        with open(self.launcher_file, 'w') as f:
            f.write(textwrap.dedent(launcher))

    def createCronJob(self):
        logging.info('Creating cron job')

        job = '''\
                    # Signal Desktop updater
                    %(minute)i */6 * * * %(path)s
                ''' % { 'minute': random.randint(0,59), 'path': os.path.abspath(__file__) }

        os.system('(crontab -l 2>/dev/null; echo "%s") | crontab -' % textwrap.dedent(job) )

    def cleanOldFiles(self, directory, exceptions = []):
        logging.info('Cleaning ' + directory)
        for f in os.listdir(directory):
            if f not in exceptions:
                logging.debug('Removing ' + f)
                f = os.path.join(directory, f)

                if os.path.isfile(f):
                    os.remove(f)
                elif os.path.isdir(f):
                    shutil.rmtree(f)

    def getLatestVersion(self):
        version = ''
        tags_url = 'https://api.github.com/repos/WhisperSystems/Signal-Desktop/tags'

        logging.info('Checking latest version')
        with urllib.request.urlopen(tags_url) as r:
            tags = json.loads(r.read().decode('utf-8'))
            version = tags[0]['name']
            version = ''.join(filter(lambda x: x.isdigit() or x == '.', version)) # remove everything except digits and dots

        logging.info('Latest version is ' + version)
        return version

    def getInstalledVersion(self):
        version = ''
        file = os.path.join(self.path, 'manifest.json')

        logging.info('Checking installed version')
        if os.path.isfile(file):
            try:
                with open(file, 'r') as f:
                    manifest = json.load(f)

                    if 'version' in manifest:
                        version = manifest['version']

            except Exception:
                logging.error('Can\'t read manifest ' + file)

        logging.info('Installed version is ' + version)
        return version

if __name__ == '__main__':
    installer = SignalInstaller(package_url, icon_url, launcher_file)
    installer.main()
