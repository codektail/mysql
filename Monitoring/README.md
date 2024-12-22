# mysql
Automation

# Roles
## Credentials
Use ssh key to authentication, you could use ssh key of your local machine ~/.ssh/rsa_id.pub or you would can create a new

```shell
ssh-keygen -t rsa -b 4096 -C "tu_correo@example.com"
```
copy the content inside a secret var inside the pipeline or put inside roles/credentials/files/ssh_key.pub

## create-database

## setup-replication



Alright, a new bot. How are we going to call it? Please choose a name for your bot.
Impulsos_db_bot
Good. Now let's choose a username for your bot. It must end in `bot`. Like this, for example: TetrisBot or tetris_bot.
Impulsos_db_bot
Done! Congratulations on your new bot. You will find it at t.me/Impulsos_db_bot. You can now add a description, about section and profile picture for your bot, see /help for a list of commands. By the way, when you've finished creating your cool bot, ping our Bot Support if you want a better username for it. Just make sure the bot is fully operational before you do this.

Use this token to access the HTTP API:
7553348867:AAGpcoUQvNs0Fh1B0nODUW-3pH3ZhSK4CrU
Keep your token secure and store it safely, it can be used by anyone to control your bot.

For a description of the Bot API, see this page: https://core.telegram.org/bots/api


1: Install eBPF Tools
# For Ubuntu-based systems
apt update
apt install bpfcc-tools linux-headers-$(uname -r)

2: Install python tools
# For Ubuntu-based systems
apt install python3-bpfcc
apt install python3-pip
pip3 install bcc
pip3 install psutil
pip3 install requests


3: Put template monitoring.py in remote path /root/monitoring/monitoring.py


4: Systemd Integration:
Convert the script into a systemd service so it runs in the background

sudo nano /etc/systemd/system/monitoring.service
```shell
[Unit]
Description=MySQL Monitor
After=network.target

[Service]
ExecStart=/usr/bin/python3 /root/monitoring/monitoring.py
Restart=always

[Install]
WantedBy=multi-user.target
```

5: enable monitoring service
sudo systemctl enable monitoring

6: start monitoring services
sudo systemctl start monitoring
