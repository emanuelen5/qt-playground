# PySide6 playground
This is currently just a playground for learning Qt/PySide6 while reading the book *Create GUI Applications with Python & Qt6* by Martin Fitzpatrick.

## Installing Qt Creator
```bash
# Get the installer
wget https://download.qt.io/official_releases/qtcreator/4.15/4.15.1/qt-creator-opensource-linux-x86_64-4.15.1.run
chmod +x qt-creator-opensource-linux-x86_64-4.15.1.run
# Install without having to register an account
http_proxy=http://0.0.0.0:123 ./qt-creator-opensource-linux-x86_64-4.15.1.run
# Step through the installer...

./qtcreator-4.15.1/bin/qtcreator
```

However, Qt Creator did not start at first due to a missing library. It gave the following error:
```console
$ ./qtcreator
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, xcb.

Aborted (core dumped)
```

By running it with the flag `QT_DEBUG_PLUGINS=1 ./qtcreator` it listed what library was missing:

```bash
Got keys from plugin meta data ("xcb")
QFactoryLoader::QFactoryLoader() checking directory path "/home/emaus/qtcreator-4.15.1/bin/platforms" ...
Cannot load library /home/emaus/qtcreator-4.15.1/lib/Qt/plugins/platforms/libqxcb.so: (libxcb-xinerama.so.0: cannot open shared object file: No such file or directory)
QLibraryPrivate::loadPlugin failed on "/home/emaus/qtcreator-4.15.1/lib/Qt/plugins/platforms/libqxcb.so" : "Cannot load library /home/emaus/qtcreator-4.15.1/lib/Qt/plugins/platforms/libqxcb.so: (libxcb-xinerama.so.0: cannot open shared object file: No such file or directory)"
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.
```

Apparently `libxcb-xinerama.so.0` was missing. This was installed using the following command:
```console
apt install libxcb-xinerama0
```

And then everything worked as a charm!

## Notes
* `gtk3-icon-browser` can be used for browsing icons in the distro's theme. It can be installed with `apt install gtk-3-examples`.
  * Get the icons in Qt by calling the function `QtGui.QIcon.fromTheme(name: str)`.
* Some color palettes can be found at <https://coolors.co/palettes/trending>