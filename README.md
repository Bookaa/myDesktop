Fork by Bookaa
==============

fix some bug on Mac OS.

* run on Python2
* install anaconda2-2.4.1, this include PyQt4
    pyenv install anaconda2-2.4.1
    pyenv global anaconda2-2.4.1
* pip install twisted

* install Quartz:
    pip install pyobjc-framework-Quartz

* pip install service_identity
* pip install --upgrade google-auth-oauthlib
* pip install qt4reactor

myDesktop
=========

python remote desktop programe (like vnc)

About
============
This program implemented the server and the client, the client can control and view the server's desktop, just like using a local computer.

Platform
========
* Linux
* Mac OS X
* Windows

Screenshots
===========
##### myDesktop Server
<img  src="https://raw.github.com/jacklam718/myDesktop/master/screenshots/myDesktopServer.png" alt="myDesktop Server"  width="450px" height="250px" />

##### the myDesktop client remote to server
<img src="https://raw.github.com/jacklam718/myDesktop/master/screenshots/myDesktopViewer.png" alt="myDesktop Client"
width="450px" height="250px"/>

##### the myDesktop client remote to server to watch YouTube
<img src="https://raw.github.com/jacklam718/myDesktop/master/screenshots/myDesktopViewer2.png" alt="myDesktop Client"
width="450px" height="250px"/>
