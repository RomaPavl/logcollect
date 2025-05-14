#!/usr/bin/env bash
set -eux

# Встановлюємо OpenSSH (з SFTP)
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-server

# Створюємо групу та користувача sftpuser (без shell)
groupadd -f sftpusers
if ! id -u sftpuser &>/dev/null; then
  useradd -m -g sftpusers -s /usr/sbin/nologin sftpuser
fi

# Забезпечуємо коректні права на домашню теку (chroot)
#    — власник root:root, права 755, без write для групи/інших
chown root:root /home/sftpuser
chmod 755     /home/sftpuser

# Налаштовуємо .ssh–каталог і ключі
mkdir -p /home/sftpuser/.ssh
chmod 700 /home/sftpuser/.ssh

cp /vagrant/keys/id_ed25519.pub /home/sftpuser/.ssh/authorized_keys
chmod 600 /home/sftpuser/.ssh/authorized_keys

chown -R sftpuser:sftpusers /home/sftpuser/.ssh

# Створюємо теку для обміну файлами (uploads)
mkdir -p /home/sftpuser/uploads
chown sftpuser:sftpusers /home/sftpuser/uploads
chmod 700               /home/sftpuser/uploads

# Налаштовуємо sshd для чистого key-only SFTP у chroot
sed -i 's@^Subsystem sftp.*@Subsystem sftp internal-sftp@' /etc/ssh/sshd_config
cat <<'EOF' >> /etc/ssh/sshd_config

# правила для групи sftpusers
Match Group sftpusers
  ChrootDirectory %h
  ForceCommand internal-sftp

  PasswordAuthentication no
  PubkeyAuthentication yes
  X11Forwarding no
  AllowTcpForwarding no
EOF

systemctl restart ssh
