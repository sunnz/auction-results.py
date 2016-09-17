## requirements

- python 3.x.
    - tested and developed on 3.3, 3.4, and 3.5.
- install dependencies in requirements.txt:
    - `pip install -r requirements.txt`.
    - you may need `sudo` if you are not using virtualenv.
    - lxml
        - on rhel/centos you will need:
            - `yum install python3-devel.x86_64 libxml2-devel.x86_64 libxslt-devel.x86_64`
            - `yum groupinstall 'Development Tools'`
        - equivalent packages should also work on other distros.
        - lxml may failed to install on osx, if so try:
            - `STATIC_DEPS=true LIBXML2_VERSION=2.9.2 pip install lxml==3.5.0`
            - see also:
                - http://louistiao.me/posts/installing-lxml-on-mac-osx-1011-inside-a-virtualenv-with-pip/
                - https://bugs.launchpad.net/lxml/+bug/1503807
                - http://lxml.de/installation.html#source-builds-on-macos-x
