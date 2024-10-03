sudo apt-get install &&  sudo apt-get upgrade -y

sudo apt install git -y
git --version

# git dependencies:
sudo apt install libz-dev libssl-dev libcurl4-gnutls-dev libexpat1-dev/
 gettext cmake gcc -y
# added with user and email 
~/.gitconfig

# ssh and adding the key to GitHub
#https://stackoverflow.com/questions/76052045/how-to-save-the-login-credentials-for-github-on-linux
uncommented Port 22 and added Port 80 and 55555 at /etc/ssh/sshd_config 
made copies of an old config cp /etc/ssh/sshd_config /etc/ssh/sshd_config.old
end restarted ssh service sudo /etc/init.d/ssh restart
https://forums.raspberrypi.com/viewtopic.php?t=256770

## Note! check /etc/ssh/sshd_config when establishing SSH: uncomment ports and restart!!!
## Note! Roter kill wifi connection after some time!
## ufw settings https://www.digitalocean.com/community/tutorials/how-to-set-up-a-firewall-with-ufw-on-ubuntu

## if any issue with db user rights: GRANT postgres TO <user>;
python manage.py migrate --run-syncdb


[nginx-stat-failed-13--permission-denied](https://stackoverflow.com/questions/25774999/nginx-stat-failed-13-permission-denied)
sudo -u www-data stat /username/test/static
gpasswd -a www-data root
chmod g+x /root && chmod g+x /root/leginabroad && chmod g+x /root/leginabroad/static

sudo journalctl -u gunicorn --since "5min ago"

python manage.py makemigrations --empty yourappname

python manage.py migrate yourappname
It turns out adding an extra empty migration forces django to recheck the table and in the process, it noticed the new migrations. There's probably some caching taking place somewhere.
