# Item Catalog

## Description

This web application provides a list of items, each is a member of a specific category, it allows authentificated users to add/edit/delete items.

## Features

    - Full CRUD.
    - JSON end points.
    - OAUTH authentification with google sign-in api.

## Requirements and running steps

    1. Virtualbox (download and install)
    2. Vagrant (download and install)
    3. Vagrant vm configuration [file](https://github.com/udacity/fullstack-nanodegree-vm) 
    4. Follow installation process in this [link](https://github.com/udacity/fullstack-nanodegree-vm)
    5. Connect to Vagrant machine with `vagrant ssh` and move to `cd /vagrant`
    5. Unzip the zipped project to the vagrant folder.
    6. Install requirements with `pip install -r requirements.txt`
    7. Setup the database with `python database_setup.py`
    8. Populate the database with `python dummy-data.py`
    9. Run the server with `python project.py`
    10. Visite http://localhost:8000 and enjoy
