# Summary
The Linux Web Server Project is part of the Configuring Linux Web Servers
Udacity course. The purpose of the project is to help solidify the concepts
learned in securing and configuring a linux web server that can be used to
host Python based web applications as well as other web sites or applications
based on other stacks.

The Linux Web Server Project is the 5th project laid out in the curriculum for
the Udacity Full Stack web developer Nanodegree.

<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Summary](#summary)
- [Requirements](#requirements)
	- [User Management](#user-management)
	- [Security](#security)
	- [Application Functionality](#application-functionality)
	- [Documentation](#documentation)
- [Web Server Configuration Details](#web-server-configuration-details)
	- [Lightsail Server](#lightsail-server)
		- [Server Connection information](#server-connection-information)
	- [System Software and Package Installation](#system-software-and-package-installation)
		- [Added Packages](#added-packages)
		- [Python Packages](#python-packages)
	- [Linux Server Configuration](#linux-server-configuration)
		- [User configuration](#user-configuration)
			- [sshd configuration](#sshd-configuration)
			- [Key based authentication](#key-based-authentication)
		- [Firewall configuration](#firewall-configuration)
		- [Apache2 Web Server configuration](#apache2-web-server-configuration)
			- [DocumentRoot configuration](#documentroot-configuration)
			- [WSGIAlias configuration](#wsgialias-configuration)
			- [WSGIDaemonProcess configuration](#wsgidaemonprocess-configuration)
		- [PostgreSQL Database configuration](#postgresql-database-configuration)
			- [Database for the application](#database-for-the-application)
			- [Roles/Users](#rolesusers)
		- [File system configuration](#file-system-configuration)

<!-- /TOC -->
# Requirements
## User Management
* The grader user can run commands using sudo to inspect files that are
	readable only by root.
* The SSH key submitted with the project can be used to log in as grader on
	the server.
* You cannot log in as root remotely.

## Security
* Only allow connections for SSH (port 2200), HTTP (port 80), and NTP
	(port 123).
* SSH is hosted on non-default port.
* Key-based SSH authentication is enforced.
* All system packages have been updated to most recent versions.

## Application Functionality
* The web server responds on port 80
* Database server has been configured to serve data (PostgreSQL is
	recommended).
*	Web server has been configured to serve the Item Catalog application as a
	WSGI app.

## Documentation
A README file is included containing the following information: IP address, URL,
summary of software installed, summary of configurations made, and a list of
third-party resources used to complete this project

# Web Server Configuration Details
## Lightsail Server
Based on the rubric for this project it is suggested to use a server provided
by one of the on demand computer platform services that Amazon AWS (Amazon Web
Services) sells. Amazon Lightsail is a service that allows you to easily
provision an Internet connected server or host (a Virtual Private Server - VPS)
running one of the industry standard Operating Systems with or without typical
development stacks or applications.

For this Linux Web Server Project I used the Lightsail service to create a
vanilla VPS running the Ubuntu 16.04 Long Term Support (LTS) Linux distribution.
The requirements for this project are minimal enough that a basic VPS is good
enough. This setup also allows me to control what applications and packages are
installed on the server I'll be using.

I have not used or configured any of the more advanced features that the
Lightsail service provides - like load balancing traffic to the application or
creating a static IP that is publicly usable. The expected traffic to this
VPS/Web Server is quite low and there is no DNS registration pointing a URL at
the IP of the server.

### Server Connection information
* Server IP address
	- 52.25.255.219
* SSH port (not default SSH)
	- port 2200
* Users (Certificate based authentication ONLY)
	- grader
		- To be used by the Udacity grader/reviewer
	- ubuntu
		- built-in user account
	- root
		- built-in user account
		- NO REMOTE LOGIN SUPPORT

To connect to the server you will need to have installed a private ssh key that
has it's public key equivalent stored on the server. See the key based
authentication section for more details.

```
> ssh grader@52.25.255.219 -p 2200 -i <path to your private key>
```

## System Software and Package Installation
It is good practice to keep installed packages up to date on a machine. Software
updates will occur over time (even in the Open Source world) and it is generally
considered good practice to update you system so that it isn't running code
riddled with bugs. For servers that are hosting applications used by many, many
users and for which there are tight restrictions on up time (perhaps there is
a SLA that needs to be honored) regular scheduled maintenance windows may be
needed. Additionally for servers where business critical applications are
running it may be good practice to have a non-production server where updates
can be applied to capture bugs or interoperability issues before rolling the
updates out to the production servers.

For this Linux Web Server Project, with the simplicity of the server setup and
based on the expected lifetime of the server, the most that I did was to make
sure that the initial setup of the server had the most up to date versions of
software that I am going to use. This means updating the existing packages to
the latest stable versions as well as downloading the most recent versions for
the additional packages I am using to support the web application being hosted.

To update the system to the latest packages, I used the Advanced Package Tool
(APT) application that comes built into the Ubuntu distribution. There are 2
commands that need to be run to first update the tree of packages the default
repositories are keeping track of and second perform an upgrade action that will
download and install the latest versions of the packages currently installed on
the system.  

```
> sudo apt-get update
> sudo apt-get upgrade
```

### Added Packages
Beyond the basic packages that have come preinstalled with the Ubuntu image that
is utilized by the Lightsail provisioned VPS, there are a handful of packages
that needed to be installed in order to host a Python and PostgreSQL based
application. The stack being deployed on this VPS is typically referenced as a
Linux Apache PostgreSQL Python or LAPP stack. That last P can also sometimes
refer to the Perl language.

Along with the packages needed to support the deployment of my web application
I also added the finger application to help with user/group administration.

Using the web resources to understand what I needed to support a LAPP deployment
as well as the [Ubuntu packages listing](https://packages.ubuntu.com/) and the
APT application I was able to identify and install the packages listed below -
* finger
	- user information lookup program
* apache2 and libapache2-mod-wsgi-py3
	- webserver and Python3 Web Service Gateway Interface libraries
* postgresql and postgresql-contrib
	- Opensource Object Relational SQL Database
* python3 and python3-pip
	- Python3 language support and Python3 Package installers

The commands to install the packages are listed below -  

```
> sudo apt-get install finger
> sudo apt-get install apache2
> sudo apt-get install libapache2-mod-wsgi-py3
> sudo apt-get install postgresql
> sudo apt-get install postgresql-contrib
> sudo apt-get install python3  
> sudo apt-get install python3-pip
```

### Python Packages
This Linux Web Server Project requires that I deploy a previously implemented
web application on our server. The application that I implemented is Python
based and uses a framework called Flask. Along with Flask there is Object
Relational Mapping (ORM) support to simplify communication with the database
that contains some of the content displayed by the web server. There were a
handful of modules/Python packages that needed to be installed in order for the
application to work properly. Those packages are listed below -
* flask, flask-httpauth, and flask-sqlalchemy
	- a micro web development framework for Python
	- a flask extension to simplify the use of HTTP authentication
	- a flask extension to add SQLAlchemy support
* oauth2client
	- a client library for accessing resources protected by OAuth 2.0
	- for Google and Facebook user authentication API access
* sqlalchemy
	- A Python SQL Toolkit and ORM
* psycopg2
	- A PostgreSQL adapter for Python

The commands to install the Python packages are listed below -  

```
> sudo pip3 install flask
> sudo pip3 install flask-httpauth
> sudo pip3 install flask-sqlalchemy
> sudo pip3 install ouath2client
> sudo pip3 install sqlalchemy
> sudo pip3 install psycopg2
```

**NOTE:  
The above commands install packages for the Python3 language. I don't have a
specific reason for Python3 vs Python2 but simply made a decision to deploy
with Python3. This decision resulted in some work to the web application being
deployed as it was originally written for Python2.**

## Linux Server Configuration
With the necessary packages and software that will allow the Linux Server to
host a LAPP based web application, I also needed to configure some of those
applications as well as the system itself.

### User configuration
The Lightsail Ubuntu installation comes with a number of built in users. The
root and ubuntu users are 2 of them and are what you may consider as the default
user accounts that a system administrator may use. It has generally become a
best practice to not login as the root user as you may inadvertently execute
a command that does something drastic as the root user has the power to do it.
This is why there is a ubuntu user. The builders of Ubuntu decided that a
builtin ubuntu user with sudo privilege is a safe alternative. To enhance that
design decision they also disable the root account by default.

I have left the root account disabled, but I have changed the default password
for the ubuntu user. Additionally I have setup key based authentication for
all users to cut down on the potential attack surface for access to this server
and further limited the SSH login access to just the ubuntu and grader users.

There has been an additional user account created (with a username of grader)
that will allow the Udacity reviewer to have access to the server in order to
inspect the system to see if it meets the requirements laid out in the
project description. This user can only access the system through SSH using key
based authentication. A separate SSH key pair has been generated for the grader.
See the key based authentication section for more details.

The grader user has been given sudo access by adding the user to the sudoers
file which is really handled by adding a grader file within the `/etc/sudoers.d`
directory.

#### sshd configuration
In order to meet the project requirements around SSH, the SSH server (sshd)
needed to be configured to listen on a non-default port (2200 instead of 22),
the root user should not be allowed to login remotely and remote access
should be setup to use key based authentication instead of prompting for a
password. The port configuration was met solely with a change in the sshd
configuration file. The forcing of key based authentication was also handled by
a change int eh configuration file but full support of key based authentication
required a little more work. See the key based authentication section for more
details.

The sshd configuration file is located at the follow path -
`/etc/ssh/sshd_config`  

The following configuration settings needed to be modified -

| Config Parameter       | Modification               |
| ---------------------- | -------------------------- |
| Port                   | changed to 2200 from 22    |
| PasswordAuthentication | changed to no              |
| PermitRootLogin        | changed to no              |
| AllowUsers             | changed to "ubuntu grader" |

#### Key based authentication
This Linux Web Server Project requires that we utilized key based authentication
for the Udacity reviewer via the grader user to access the server in a secure
manner that is different than using a typical username/password authentication
scheme. Typically a user that is going to be granted remote login permissions
would want to generate their own private/public key pair and install the public
key on the machines they want to have secure remote sessions on. In this case I
created the private/public key on the behalf of the Udacity grader, installed
the public key on the server and then am providing the private key to the
grader.

With this process one has to trust that I can guarantee that there is one
private key and that it has been given only to the Udacity grader. There is a
somewhat complex topic that covers the trust issues that present themselves in
relation to digital certificates and public key encryption. I don't intend to
duplicate or implement a public key infrastructure for this project or a simple
certificate management system. The best we can do is trust each other.

There is a certificate management system provided by AWS through the Lightsail
administration pages for my VPS. I could have simply generated the key pair
through that administration page, downloaded the private key and included it
with the project submittal. I don't think that would have followed in the
spirit of the assignment. I instead wanted to make sure I understood how key
based authentication is deployed.

### Firewall configuration
Using the uncomplicated firewall (UFW) application that comes preinstalled with
Ubuntu, I setup the firewall to allow incoming SSH, WWW, and NTP traffic but to
deny all other types of traffic. Additionally I setup the firewall to allow any
outgoing traffic. UFW is disabled by default and needed to be enabled after
configuration.

The below commands allowed me to setup UFW as needed.

```
> sudo ufw default deny incoming
> sudo ufw default allow outgoing
> sudo ufw allow 2200/tcp
> sudo ufw allow www
> sudo ufw allow ntp
> sudo ufw enable
```

### Apache2 Web Server configuration
As mentioned in the System Software and Package Installation section above I
installed the apache2 and libapache2-mod-wsgi-py3 packages to support handling
client HTTP requests. By default apache2 doesn't know how to deal with the
Python, PostgreSQL backend that I am deploying. The point of the wsgi-py3
package is to server as the interface between the Apache2 web server and the
Python backend that I've implemented. There were a handful of configuration
changes that needed to be made before things started to work.
Configuration of Apache2 itself was not needed, but configuration of the WSGI
was. Configuration changes were made in the following file -
`/etc/apache2/sites-enabled/000-default.conf`

#### DocumentRoot configuration
The DocumentRoot is fairly self explanatory but needed to be change to define
the root directory where the WSGI should consider the application lives.
`DocumentRoot /var/www/catalog`

#### WSGIAlias configuration
The WSGIAlias is used by the WSGI to map requests to URIs to Python scripts or
applications on the backed. For my simple deployment I only needed to define one
alias. This alias handles page requests to the root URL and defines some
parameters that the WSGI needs.
```
WSGIScriptAlias / /var/www/catalog/myapp.wsgi  
  <Directory /var/www/catalog/>  
    Options FollowSymLinks  
    WSGIProcessGroup catalogApp  
    Order allow,deny  
    Allow from all  
  </Directory>
```

#### WSGIDaemonProcess configuration
The WSGIDaemonProcess is used by the WSGI to define a specific daemon process
that is used to run the application. I needed to make changes from the default
configuration so that my Python code could access files that expects to be
there for logging as well as Google and Facebook API App secrets. Further
I wanted to specify what user and group is running the application so that
I am not running it as root or some other user with elevated permissions.
```
WSGIDaemonProcess catalogApp user=www-data  
                             group=www-data  
                             home=/var/www/catalog  
                             umask=002
```

### PostgreSQL Database configuration
In order to meet the requirement of deploying a web and database server that
can host my web application, I've followed the suggestion of installing and
using PostgreSQL. The database used in the previous project where I originally
implemented the web application was SQLite. PostgreSQL is a bit heavy weight
for the application itself but the intent of the project is to expose us to
different technologies and deployment methods.

My PostgreSQL configuration is pretty much a default configuration that matches
what you get just after installing. The only differences are that I've added a
new role/user that is going to be used by the application to perform the DB
transactions and I've added a new Database.

#### Database for the application
In addition to creating a new user/role I wanted to create a new database that
is to be used by the application when storing and retrieving information that
is hosted by the web server.

As the "postgres" user and using the `createdb` command that is added with a
PostgreSQL installation I was able to add a new "catalogstore" database that
will contain the User, Item, and Category tables that will themselves contain
the item data that is used by my web application.

#### Roles/Users
Instead of using the default "postgres" user that was added by the PostgreSQL
installation I wanted to create a separate role/user that has a more limited
privilege level. This user should NOT have superuser power. In essence this user
should really just be able to add and remove content to the database that is
specific to the application it is associated with.

Again as the "postgres" user and using the `createuser` command that is added
with a PostgreSQL installation I was able to add a new 'db_admin' role/user. I
also setup that user with a special password that is utilized by the application
when setting up the connection between the application and the database. I
also needed to grant access for the db_admin to the catalogstore database as
by default a new user/role has no database access.

**NOTE: PostgreSQL doesn't have users. Instead they call it a role.**

### File system configuration
In order to host the Item Catalog application I needed a way to deploy my
implementation to the production server. There are a couple ways to do this
but ultimately once the code is on the server it needs to be in a location
that the www-data user and www-data group have access to and permissions for.

Getting source code onto the server can be accomplished with a handful of
different methods - SFTP, FTP, scpy, git. As we've been using git throughout
the entirety of the Full Stack web developer Nanodegree curriculum it made sense
to me to continue to use that method as a means to get the source code onto
the server. The default Ubuntu installation has git installed and it is
fairly trivial to clone the a repo down to a location on the server. The trick
is getting the files in a location that the webserver expects them to be in.

Apache2 expects content it is going to host to be in a /var/www/ directory.
The default installation actually creates a /var/www/html directory where there
is a prepopulated index.html that is viewable right away. I don't need that
directory as I'm not deploying a straight HTML based website. Instead I am
deploying a Python and PostgreSQL based web application.

I've already discussed the Apache2 and WSGI configurations in the above
sections. Those configurations expect the application the websever is hosting to
be in a /var/www/catalog directory. The content in the catalog directory is
actually the content cloned/pulled from the git repository but it is stored in
a different location on the file system. I've used symlinks to allow the
webserver configuration to continue using a /var/www/ location but from a
deployment perspective I don't have to trouble with copying files from some
FTP directory or user directory into the /var/www/ location. Instead I can
FTP or use a git clone/pull to get the content I want (provided that I have a
github account) and as long as the symlink is pointing to the right location the
webserver can start displaying new content with in worst case an Apache2 service
restart.
