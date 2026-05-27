#!/bin/bash

VERSION="Версия 6 от 30.10.2025г"
# Подходит для версий:
#	ALT SP Workstation
#	ALT Workstation 10.X (Autolycus)
#	ALT Workstation 11.X (Prometheus)

cat /etc/os-release

# Установка клиентской части МИС САМСОН на ОС Альт.
# su -
# cd /home/user/
# bash ALTLinux_v6.sh

#================= Проверки =================
if ! grep "ALT" /etc/os-release > /dev/null ; then
	echo "ОС не Альт, установка невозможна!"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    echo "Запустите скрипт от root !"
    echo "Введите: su -"
    exit 1
fi

ping -c 1 8.8.8.8 || echo 'Отсутствует доступ к интернету, установка невозможна!'
ping -c 1 8.8.8.8 > /dev/null || exit 1

function ERROR
{
echo -en "
\033[31m ========== Обнаружена ОШИБКА! ========== \033[39m
\033[31m ========== Установка прервана! ========= \033[39m
"
exit 1
}

echo "[$(date +%Y%m%d-%T)] ======= Запущен скрипт установки ЛИН-клиента ЕМИС $VERSION =======" >> /root/.install.ver
echo "[$(date +%Y%m%d-%T)] ======= Запущен скрипт установки ЛИН-клиента ЕМИС $VERSION =======" 

#================= Установка =================
echo "###########################################"
echo "############ Настройка системы ############"
echo "###########################################"

if grep "ALT SP Workstation" /etc/os-release && grep "VERSION_ID=10" /etc/os-release ; then
	echo "[$(date +%Y%m%d-%T)] Раскомментировать репозиторий c10f (Только для: ALT SP Workstation версии 10)"
	sed -i 's/#rpm \[cert8\] http/rpm \[cert8\] http/' /etc/apt/sources.list.d/altsp.list || ERROR 
fi

if grep "ALT Workstation" /etc/os-release && grep "VERSION_ID=10" /etc/os-release ; then
	echo "[$(date +%Y%m%d-%T)] Раскомментировать репозиторий p10 (Только для: ALT Workstation версии 10)"
	sed -i 's/#rpm \[p10\] http/rpm \[p10\] http/' /etc/apt/sources.list.d/alt.list || ERROR 
fi

if grep "ALT Workstation" /etc/os-release && grep "VERSION_ID=11" /etc/os-release ; then
	echo "[$(date +%Y%m%d-%T)] Раскомментировать репозиторий p11 (Только для: ALT Workstation версии 11)"
	sed -i 's/#rpm \[p11\] http/rpm \[p11\] http/' /etc/apt/sources.list.d/alt.list || ERROR 
	echo "[$(date +%Y%m%d-%T)] Добавить репозиторий p10 (Только для: ALT Workstation версии 11)"
	apt-repo add p10 || ERROR 
		# rpm [p10] http://update.altsp.su/pub distributions/ALTLinux/p10/branch/x86_64 classic gostcrypto
		# rpm [p10] http://update.altsp.su/pub distributions/ALTLinux/p10/branch/x86_64-i586 classic
		# rpm [p10] http://update.altsp.su/pub distributions/ALTLinux/p10/branch/noarch classic
fi

echo "[$(date +%Y%m%d-%T)] Посмотреть текущие репозитории"
apt-repo list -a

echo "[$(date +%Y%m%d-%T)] Обновить списки пакетов"
apt-get update

echo "[$(date +%Y%m%d-%T)] Установить необходимые пакеты"
apt-get install -y python-module-PyQt4 python-module-requests python-module-serial python-module-isodate python-dev python-modules-distutils || ERROR  
apt-get install -y nano ftp sudo wget  || ERROR 
apt-get install -y gcc swig libqt4-sql-mysql libmysqlclient21 libpcsclite-devel libenchant || ERROR 
rpm -qa | grep libmysqlclient21 ## Версия должна быть libmysqlclient21-8.0.40-alt1.x86_64

# Вылетов МИС меньше и печать быстрее
echo "[$(date +%Y%m%d-%T)] Отключение системы обеспечивающей обнаружение сервисов в локальной сети:"
systemctl disable avahi-daemon
systemctl stop avahi-daemon

## Это веб интерфейс сервера печати для удаленных принтеров https://packages.debian.org/ru/sid/cups-browsed
#echo "[$(date +%Y%m%d-%T)] Отключение удаленных принтеров:"
#systemctl disable cups-browsed
#systemctl stop cups-browsed


echo "########################################"
echo "############ Установка ЕМИС ############"
echo "########################################"
read -r -p "Введите IP-адрес сервера БД: " server
read -r -p "Введите имя БД: " baza

### FTP ###
FTPD="/pub/update"
FTPU="anonymous" #[имя пользавателя (логин) удаленного ftp-cервера]
FTPP="megapassword" #[пароль доступа к удаленному ftp-серверу]
FTPS="$server" #[собственно, адрес ftp-сервера или его IP]
FTPFILE="client_lin.tar.gz" #[файл]
FTP="$(which ftp)"

echo "[$(date +%Y%m%d-%T)] Скачиваем client_lin.tar.gz с сервера БД по ФТП..."
$FTP -n $FTPS <<END_SCRIPT
 quote USER $FTPU
 quote PASS $FTPP
 cd $FTPD
 binary
 get $FTPFILE
 quit
END_SCRIPT
mv client_lin.tar.gz /opt/ || ERROR 

### Или скачиваем по ssh
### Скопировать с сервера каталог /var/ftp/pub/update/client_lin.tar.gz в директорию /opt
#scp ftp@192.168.1.225:/var/ftp/pub/update/client_lin.tar.gz /opt/
#  ## Пароль: ввести пароль от учетной записи "ftp" на сервере МИС (пасс у КМИАЦ "ftp")
  
echo "[$(date +%Y%m%d-%T)] Распаковываем клиента"
tar xzf /opt/client_lin.tar.gz -C /opt || ERROR 

echo "[$(date +%Y%m%d-%T)] Выдаем все права каталогу с клиентом"
chmod -R 777 /opt/client
user=`ls /home | grep -v '^lost+found$'`
chown $user:$user -R /opt/client

echo "[$(date +%Y%m%d-%T)] Создаем ярлык на рабочем столе"
cp /opt/client/Samson_AutoUP.desktop "/home/$user/Рабочий стол/"
chmod 755 "/home/$user/Рабочий стол/Samson_AutoUP.desktop"
chown $user:$user "/home/$user/Рабочий стол/Samson_AutoUP.desktop"

echo "[$(date +%Y%m%d-%T)] Настраиваем ЕМИС"
mkdir -p /home/$user/.config/samson-vista
echo '[db]
serverName='$server'
database='$baza'

[appPrefs]
provinceKLADR=2300000000000
defaultKLADR=2300000000000

' > /home/$user/.config/samson-vista/S11App.ini
chmod 777 /home/$user/.config/samson-vista/S11App.ini
chown $user:$user -R /home/$user/.config

echo "[$(date +%Y%m%d-%T)] Устанавливаем шрифты для печати штрихкода и другие"
#https://www.altlinux.org/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0_%D1%88%D1%80%D0%B8%D1%84%D1%82%D0%BE%D0%B2
cp /opt/client/install/fonts/*.ttf /usr/share/fonts/ttf/
fc-cache -f -v

echo "########################################"
echo "############ Установка pip2 ############"
echo "########################################"

echo "[$(date +%Y%m%d-%T)] Устанавливаем необходимые пакеты pip2"

#apt-get install -y python-module-pip #вместо этого исключенного пакета:
#https://pip.pypa.io/en/stable/installation/
#curl 'https://bootstrap.pypa.io/pip/2.7/get-pip.py' > /opt/client/install/get-pip.py  # можно скачать
python2 /opt/client/install/get-pip.py || ERROR 

pip2 install --upgrade setuptools || ERROR 
pip2 install --upgrade pip 		  || ERROR 
pip2 install wheel 				  || ERROR 
pip2 install /opt/client/install/ZSI-2.1-a1.tar.gz  || ERROR 
pip2 install /opt/client/install/PyXML-0.8.4.tar.gz || ERROR 

#sed -i '/pyscard/d' /opt/client/requirements.txt # error: command 'x86_64-alt-linux-gcc' failed with exit status 1
cat /opt/client/requirements.txt
pip2 install -r /opt/client/requirements.txt || ERROR 

echo "[$(date +%Y%m%d-%T)] Установка завершена!"

echo "[$(date +%Y%m%d-%T)] Запуск ЕМИС можно проверить командой (ВАЖНО: запуск только от пользователя):
python2 /opt/client/s11main.py"

