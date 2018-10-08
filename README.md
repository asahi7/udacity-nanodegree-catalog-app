# Catalog App Project Offered By Udacity Full Stack Nanodegree

The actual name of this project is Restauritta. The final project of Udacity Full Stack Nanodegree Program.

The idea of this website is to simulate real-life visitor's judgements about the services restaurant owners provide. So, for example, a user can complain about bad service they received or recommend some insighful things.

Currently, there is only one admistrator who can manage the app in order to not overcomplicate the project.

## Prerequisites

* Install [VirtualBox](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)
* Install [Vagrant](https://www.vagrantup.com/downloads.html)
* In your terminal (CLI tool), inside vagrant folder, run: `vagrant up`
* After previous command finishes executing, run: `vagrant ssh`, this will open a SSH connection to your virtual machine
* Inside VM, change your directory to: `cd /vagrant/`, this is the working directory of our project, as you would be able to see
* You will also have to create a new PostgreSQL database with help of `psql`. Run: `psql`, then `create database catalogdb`

## Launch the website

With SSH, in /vagrant/catalog/, run: `python init_db.py`, this will initialize tables in the database

In /vagrant/catalog/, run: `python catalog.py`

Go to [http://localhost:58779/](http://localhost:58779/) and enjoy! You will have to login as either an admin or an ordinary user. The registration allows only one email to be used for one role, in other words, you can not use one email to be used for two roles simultaneously.

Administrators can create new cities and group their restaurants into them, whereas ordinary users post their complaints or recommendations to restaurants.
