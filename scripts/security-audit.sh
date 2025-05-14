#!/usr/bin/env bash
set -eux

# Оновлюємо індекси та встановлюємо rkhunter і curl
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y rkhunter curl

# Встановлюємо curl як інструмент для завантаження
sed -i 's|^WEB_CMD=.*|WEB_CMD=curl|' /etc/rkhunter.conf

# Ігноруємо помилки оновлення, щоб провізіон не падав
set +e
rkhunter --update
UPDATE_RC=$?
rkhunter --propupd
set -e

# Попередження в разі проблеми з --update
if [ "$UPDATE_RC" -ne 0 ]; then
  echo "Warning: rkhunter --update returned ${UPDATE_RC}. Check /var/log/rkhunter.log"
fi
