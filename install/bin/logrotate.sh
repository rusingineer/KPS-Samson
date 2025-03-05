#!/bin/bash

echo "Очистка старых логов" 

# AriadnaExchange
find /var/log/AriadnaExchange/ -type f -mtime +1 -exec gzip {} \;
find /var/log/AriadnaExchange/ -type f -mtime +30 -exec rm {} \;

# ODIIExchange
find /var/log/ODIIExchange/ -type f -mtime +1 -exec gzip {} \;
find /var/log/ODIIExchange/ -type f -mtime +30 -exec rm {} \;

# downloadRecipeLLO
find /var/log/downloadRecipeLLO/ -type f -mtime +1 -exec gzip {} \;
find /var/log/downloadRecipeLLO/ -type f -mtime +30 -exec rm {} \;

# WarrantNumberUpdater
mv /var/log/Warrant/WarrantNumberUpdater.log /var/log/Warrant/WarrantNumberUpdater_$(date '+%Y-%m-%d').log
find /var/log/Warrant/ -type f -mtime +1 -exec gzip {} \;
find /var/log/Warrant/ -type f -mtime +30 -exec rm {} \;
		
# Holter
mv /var/log/Holter/HolterExchanger.log /var/log/Holter/HolterExchanger_$(date '+%Y-%m-%d').log
find /var/log/Holter/ -type f -mtime +1 -exec gzip {} \;
find /var/log/Holter/ -type f -mtime +30 -exec rm {} \;
		
# RISExchange
find /var/log/RISExchange/ -type f -mtime +1 -exec gzip {} \;
find /var/log/RISExchange/ -type f -mtime +30 -exec rm {} \;
		
# hl7server
mv /opt/hl7server/grpcServer.log /opt/hl7server/Logs/grpcServer_$(date '+%Y-%m-%d').log
mv /opt/hl7server/mllpServer.log /opt/hl7server/Logs/mllpServer_$(date '+%Y-%m-%d').log
find /opt/hl7server/Logs/ -type f -mtime +1 -exec gzip {} \;
find /opt/hl7server/Logs/ -type f -mtime +30 -exec rm {} \;

# labExchange
find /var/log/labExchange/ -type f -mtime +1 -exec gzip {} \;
find /var/log/labExchange/ -type f -mtime +30 -exec rm {} \;
 