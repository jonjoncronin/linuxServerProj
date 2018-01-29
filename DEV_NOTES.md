# Summary
These developer notes exist to help me remember the steps I followed in order
to configure both the vagrant test machine and then the production server that
was used as part of the project submittal.

# Vagrant Test Server
Use Vagrant on your local machine. The Vagrant file can help dictate a few
things that would have to be handled by hand on the production server. Things
like bulk file permissions, and bulk installation of packages can be included.

Add this for changing the folder and file permissions for the /vagrant
directory -
config.vm.synced_folder "./", "/vagrant",
  owner: "vagrant",
  group: "www-data",
  mount_options: ["dmode=775,fmode=664"]

Add this for installing what ever packages you want -
config.vm.provision "shell", inline: <<-SHELL
   apt-get update
   apt-get upgrade -y
   apt-get install -y finger python python-pip python3 python3-pip apache2
   libapache2-mod-wsgi libapache2-mod-wsgi-py3 postgresql postgresql-contrib
   pip2 install --upgrade pip
   pip2 install flask oauth2client flask-httpauth sqlalchemy flask-sqlalchemy
   psycopg2
   pip3 install --upgrade pip
   pip3 install flask oauth2client flask-httpauth sqlalchemy flask-sqlalchemy
   psycopg2
   echo "VM provisioning complete"
 SHELL

Add this for HTTP Hosting out port 8088 -
config.vm.network "forwarded_port", guest: 80, host: 8088

# Web Server Configuration Details
## System Software and Package Installation
### Added Packages
```
> sudo apt-get update
> sudo apt-get upgrade
> sudo apt-get install finger
> sudo apt-get install apache2
> sudo apt-get install libapache2-mod-wsgi-py3
> sudo apt-get install postgresql
> sudo apt-get install postgresql-contrib
> sudo apt-get install python3  
> sudo apt-get install python3-pip
```

### Python Packages
```
> sudo pip3 install --upgrade pip
> sudo pip3 install flask
> sudo pip3 install flask-httpauth
> sudo pip3 install flask-sqlalchemy
> sudo pip3 install ouath2client
> sudo pip3 install sqlalchemy
> sudo pip3 install psycopg2
```

## Linux Server Configuration
### User configuration
#### adduser
After logging in as the ubuntu user (or vagrant on the local machine) -
```
ubuntu> sudo adduser grader
```
Follow the prompts for adding a user - give it a password of `grader`

#### Sudoers
On Vagrant -
copy the `/etc/sudoers.d/vagrant` file as the new user you want to have sudo
power for. Then modify it so that instead of it saying
`vagrant ALL=(ALL) NOPASSWD:ALL`
it has the username of the new user.

Another solution is to add an extra line for the new user in the the
`90-cloud-init-users` file also in the `/etc/sudoers.d/` directory.

#### sshd configuration
`/etc/ssh/sshd_config`  

The following configuration settings needed to be modified -

| Config Parameter       | Modification               |
| ---------------------- | -------------------------- |
| Port                   | changed to 2200 from 22    |
| PasswordAuthentication | changed to no              |
| PermitRootLogin        | changed to no              |
| AllowUsers             | changed to "ubuntu grader" |

#### Key based authentication
Lightsail has a SSH certificate manager feature - you can download the
private key and the public key gets put on the server.

For the project you need to generate the private public key pair for the
grader to use. The keys need to be generated on your local machine via the
ssh-keygen command from terminal.
Name the keys linuxProj and linuxProj.pub.
Before locking down SSH you can copy the file to the server via the following
command -
```
cat ~/.ssh/id_rsa.pub | ssh username@remote_host "mkdir -p ~/.ssh &&
cat >> ~/.ssh/authorized_keys"
```
### Firewall configuration
```
> sudo ufw default deny incoming
> sudo ufw default allow outgoing
> sudo ufw allow 2200/tcp
> sudo ufw allow www
> sudo ufw allow ntp
> sudo ufw enable
```

### Apache2 Web Server configuration
The `/etc/apache2/sites-enabled/000-default.conf` file contains the
configuration settings that need to be modified. Make sure the config has this
data and that the directory we want to host is at `/var/www/catalog`
```
DocumentRoot /var/www/catalog
WSGIDaemonProcess catalogApp user=www-data  
                             group=www-data  
                             home=/var/www/catalog  
                             umask=002
WSGIScriptAlias / /var/www/catalog/myapp.wsgi  
  <Directory /var/www/catalog/>  
    Options FollowSymLinks  
    WSGIProcessGroup catalogApp  
    Order allow,deny  
    Allow from all  
  </Directory>
```

### PostgreSQL Database configuration
#### Database for the application
to get to the postgres user context -
`sudo -i -u postgres`

As the postgres user run this command to create the database (make sure all
lowercase letters) -
`> createdb catalogstore`

#### Roles/Users
As the postgres user run this command to create the db_admin role (PostgreSQL
thinks of Roles instead of users) -
`> createuser db_admin`

As the postrges user start `psql` -
Grant permissions for the db_admin user on the catalogstore DB by running this
SQL command (don't forget the semicolon ; )-
`GRANT all on database catalogstore to db_admin;`

### File system configuration
We want a way to make it easy to deploy changes - SFTP or git could do it.
We also want to make it so that the user group that Apache is using to run
the daemon can access the files and directory properly.
```
sudo mkdir /projects
sudo chgrp /projects
cd /projects
git clone <your HTTP repo> <whatever directory you want to call it>
sudo chgrp -R <your new working directory> www-data
```

Now we want to create a symbolic link so that Apache has the directory it needs
to run the application.
```
sudo rm -fr /var/www/html
sudo ln -s /projects/<your new working directory> /var/www/catalog
```

Now restart Apache2 -
```
sudo service apache2 restart
```
