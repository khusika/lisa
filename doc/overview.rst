********
Overview
********

Installation
============

Native installation
+++++++++++++++++++

For now, you will need to clone LISA from `github <https://github.com/ARM-software/lisa>`_ ,
and then issue these commands::

  git clone https://github.com/ARM-software/lisa.git -b next
  cd lisa
  # A few packages need to be installed, like python3 or kernelshark. Python
  # modules will be installed in a venv at the next step, without touching 
  # any system-wide install location.
  sudo ./install_base_ubuntu.sh
  # On the first run, it will take care of creating a Python venv and populating it
  source init_env

In case the venv becomes unusable for some reason, the ``lisa-install``
shell command available after sourcing ``init_env`` will allow to create a new
clean venv from scratch.

Additional Python packages
--------------------------

``lisa-install`` will also install the content of
``$LISA_HOME/custom_requirements.txt`` if the file exists. That allows
re-installing a custom set of packages automatically when the venv needs to
regenerated.

Git hooks
---------

A git `post-checkout` hook is provided in tools/post-checkout. It will check
that no `setup.py` file have been updated since last time ``lisa-install`` was
executed. If a modification is detected, it will ask the user to run
``lisa-install`` again, since a dependency might have been added, or a version
requirement might have been updated.

Without automatic ``venv``
--------------------------

Sometimes, LISA needs to operate in an environment setup for multiple tools. In
that case, it may be easier to manage manually a venv/virtualenv instead of
letting LISA create one for its shell.

Setting ``export LISA_USE_VENV=0`` prior to ``source init_env`` will avoid the
creation and usage of the LISA-managed venv. ``lisa-install`` command can still
be used to install the necessary Python packages, which will honor any
venv-like system manually setup.

Alternatively, ``lisa`` package is packaged according to the usual Python
practices, which includes a ``setup.py`` script, and a
``devmode_requirements.txt`` file that will install all the shipped packages in
editable mode (including those that are not developped in that repository, but
still included for convenience).

Virtual machine installation
++++++++++++++++++++++++++++++++++

LISA provides a Vagrant recipe which automates the generation of a
VirtualBox based virtual machine pre-configured to run LISA. To generate and
use such a virtual machine you need:

- `VirtualBox <https://www.virtualbox.org/wiki/Downloads>`__
- `Vagrant <https://www.vagrantup.com/downloads.html>`__

Once these two components are available on your machine, issue these commands::

  git clone https://github.com/ARM-software/lisa.git -b next
  cd lisa
  vagrant up

This last command builds and executes the VM according to the description provided
by the Vagrant file available in the root folder of the LISA source tree.

Once the VM installation is complete, you can access that VM with::

  vagrant ssh


Using LISA
==========

You should now have all of the required dependencies installed. From now on, you
can use the LISA shell, which provides a convenient set of commands for easy
access to many LISA related functions (done automatically by Vagrant)::

  source init_env

Run ``lisa-help`` to see an overview of the provided LISA commands.

Notebooks
=========

The LISA shell can simplify starting an Jupyter notebook server::

  [LISAShell lisa] \> lisa-jupyter start

  Starting Jupyter Notebooks...

  Notebook server configuration:
    URL        :  http://127.0.0.1:8888/?token=b34F8D0e457BDa570C4A6D7AF113CB45d9CcAF44Aa7Cf400
    Folder     :  /data/work/lisa/ipynb
    Logfile    :  /data/work/lisa/ipynb/server.log
    PYTHONPATH :
	  /data/work/lisa/modules_root/


  Notebook server task: [4] 30177

Note that the ``lisa-jupyter`` command allows you to specify interface and
port in case you have several network interfaces on your host::

  lisa-jupyter start [interface [port]]

The URL of the main folder served by the server is printed on the screen.
By default it is http://127.0.0.1:8888/

Once the server is started you can have a look at the provided tutorial
notebooks are accessible by following this `link
<http://127.0.0.1:8888/notebooks/tutorial/00_LisaInANutshell.ipynb>`__.

This initial tutorial can be seen (but not executed) also on `github
<https://github.com/ARM-software/lisa/blob/master/ipynb/tutorial/00_LisaInANutshell.ipynb>`__.

Contributing
============

See `this document <https://github.com/ARM-software/lisa/blob/next/CONTRIBUTING.md>`__.
