## Install Signal Desktop as a standalone app, without Chrome dependency [\*](#note-on-chrome-dependency)

This guide and installer script is written and tested on Linux systems, but as Node.js and NW.js are cross-platform, it probably is easily adaptable for macOS and Windows. There is also a [guide to install Signal Desktop manually](https://gist.github.com/shvchk/60b8410edf7eb00e7696f1534d47428d#install-signal-desktop-as-a-standalone-app-without-chrome-dependency-) with an option to build it from source.

Let's do it the easy and automated way:

1. **Install dependencies:**
    - **[Node.js and NPM](https://nodejs.org/en/download/package-manager/)**
    - **NW.js:** `sudo npm install -g nw` (global) or `npm install nw` (current user)

2. **Create app folder and go into it:** `mkdir -p ~/apps/Signal && cd $_`

3. **Get and run install script:**

    `wget https://raw.githubusercontent.com/shvchk/Signal-Desktop-installer/master/install.py && python3 install.py`

    This will download Signal Desktop package, unpack it to the current directory, create a .desktop file and a cron job for updating.

That's it! Signal Desktop launcher should now appear in the programs list.

---

Feel free to report installer bugs to this repository issue queue or/and contribute with a pull requests.

Don't forget, though, that this kind of setup is not supported by Open Whisper Systems. For further info on Signal Desktop (bug reporting, contributing, etc.) please use [official Signal Desktop repository](https://github.com/WhisperSystems/Signal-Desktop#signal-desktop).

---

##### Note on Chrome dependency

This setup is not dependent on Chromium (or derivative) browser installation and does not use any of its files or settings. Still, at its core NW.js and therefore this setup uses the same technology used in Chromium based browsers, including Blink rendering engine and V8 JavaScript engine.
