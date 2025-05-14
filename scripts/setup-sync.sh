#!/usr/bin/env bash

set -eux
sudo apt-get install -y dos2unix
cp /vagrant/scripts/sftp-sync.sh /home/vagrant/sftp-sync.sh
chmod +x /home/vagrant/sftp-sync.sh
dos2unix /home/vagrant/sftp-sync.sh
cp /vagrant/keys/id_ed25519 /home/vagrant/.ssh/id_ed25519
chmod 600 /home/vagrant/.ssh/id_ed25519
chown -R vagrant:vagrant /home/vagrant/.ssh

# New directory for collecting logs
mkdir -p /vagrant/logs

# Add cron for user vagrant
CRON_JOB='*/5 * * * * /home/vagrant/sftp-sync.sh >> /home/vagrant/sync.log 2>&1'
COPY_JOB='*/5 * * * * cp /home/vagrant/sync.log /vagrant/logs/$(hostname).log'
sudo -u vagrant crontab -l 2>/dev/null | grep -v 'sftp-sync.sh' > /tmp/crontab.tmp || true
echo "$CRON_JOB" >> /tmp/crontab.tmp
echo "$COPY_JOB" >> /tmp/crontab.tmp
sudo -u vagrant crontab /tmp/crontab.tmp
rm /tmp/crontab.tmp

