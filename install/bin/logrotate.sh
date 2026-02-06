#!/bin/bash

echo "Очистка старых логов"

# AriadnaExchange
pkill -f "AriadnaExchange"
find /var/log/AriadnaExchange/ -type f -mtime +30 -exec rm {} \;
find /var/log/AriadnaExchange/ -type f -mtime +1 -exec gzip {} \;

# ODIIExchange
pkill -f "ODIIExchange"
find /var/log/ODIIExchange/ -type f -mtime +30 -exec rm {} \;
find /var/log/ODIIExchange/ -type f -mtime +1 -exec gzip {} \;

# downloadRecipeLLO
pkill -f "downloadRecipeLLO"
find /var/log/downloadRecipeLLO/ -type f -mtime +30 -exec rm {} \;
find /var/log/downloadRecipeLLO/ -type f -mtime +1 -exec gzip {} \;

# WarrantNumberUpdater
pkill -f "WarrantNumberUpdater"
mv /var/log/Warrant/WarrantNumberUpdater.log /var/log/Warrant/WarrantNumberUpdater_$(date '+%Y-%m-%d' -d "yesterday").log
find /var/log/Warrant/ -type f -mtime +30 -exec rm {} \;
find /var/log/Warrant/ -type f -mtime +1 -exec gzip {} \;
		
# Holter
pkill -f "HolterExchanger"
mv /var/log/Holter/HolterExchanger.log /var/log/Holter/HolterExchanger_$(date '+%Y-%m-%d' -d "yesterday").log
find /var/log/Holter/ -type f -mtime +30 -exec rm {} \;
find /var/log/Holter/ -type f -mtime +1 -exec gzip {} \;

# ODLI - labExchange
pkill -f "autoexport_new"
find /var/log/labExchange/ -type f -mtime +30 -exec rm {} \;
find /var/log/labExchange/ -type f -mtime +1 -exec gzip {} \;

# AlisaExchange
pkill -f "AlisaExchange"
find /var/log/AlisaExchange/ -type f -mtime +60 -exec rm {} \;
find /var/log/AlisaExchange/ -type f -mtime +1 -exec gzip {} \;

# RISExchange
pkill -f "RISExchange"
find /var/log/RISExchange/ -type f -mtime +30 -exec rm {} \;
find /var/log/RISExchange/ -type f -mtime +1 -exec gzip {} \;

# hl7server
mv /opt/hl7server/grpcServer.log /opt/hl7server/Logs/grpcServer_$(date '+%Y-%m-%d' -d "yesterday").log
mv /opt/hl7server/mllpServer.log /opt/hl7server/Logs/mllpServer_$(date '+%Y-%m-%d' -d "yesterday").log
service hl7server restart
find /opt/hl7server/Logs/ -type f -mtime +30 -exec rm {} \;
find /opt/hl7server/Logs/ -type f -mtime +1 -exec gzip {} \;
# если служба не запустилась, перезапустить еще раз
service hl7server status | grep active || echo "$(date '+%Y-%m-%d_%T') hl7server остановлен, перезапускаем" >> /opt/hl7server/ERROR.log
service hl7server status | grep active || echo service hl7server restart

