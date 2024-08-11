

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

## Copying from windows to linux scp "C:\Users\User\.blabla" oleks@oleks:/home/oleks


#https://www.digitalocean.com/community/tutorials/how-to-install-git-on-ubuntu
