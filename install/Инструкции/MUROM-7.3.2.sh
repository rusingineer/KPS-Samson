#!/bin/bash
#Установка клиентской части МИС САМСОН на РЕД ОС 7.3.2.
#cat /etc/os-release
#	NAME="RED OS"
#	VERSION="MUROM (7.3.2)"
#	PLATFORM_ID="platform:el7"
#	ID="redos"
#	ID_LIKE="rhel centos fedora"
#	VERSION_ID="7.3.2"
#	PRETTY_NAME="RED OS MUROM (7.3.2)"
#	ANSI_COLOR="0;31"
#	CPE_NAME="cpe:/o:redos:redos:7"
#	HOME_URL="http://red-soft.ru/ru/main_products.html#redos"
#	BUG_REPORT_URL="http://redos-support.red-soft.ru"
#	EDITION="Standard"

#================= Проверки =================
if ! grep "RED OS MUROM" /etc/os-release ; then
	echo "ОС не RED OS MUROM, установка невозможна!"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    echo "Запустите скрипт от root !"
	echo "sudo su"
    exit 1
fi

#================= Установка =================
echo "###########################################"
echo "############ Настройка системы ############"
echo "###########################################"

echo "[$(date +%Y%m%d-%T)] ======= Запущен скрипт установки ЕМИС MUROM-7.3.2.sh (v1) =======" >> /root/.install.ver

echo "[$(date +%Y%m%d-%T)] Проверить систему"
dnf list installed "rpm.x86_64"
## Версия rpm.x86_64 должна быть не ниже 4.15.0-1

dnf list installed "rpm.x86_64" > rpm.version.txt
if grep "4.13.90" rpm.version.txt ; then
	echo "ОС не обновлена, необходимо обновление!"
	echo " Будет ошибка при установке python2-pip (если система с сайта РЕД ОС и не обновлена)"
	echo " Ошибка: проверка транзакции на разрешение зависимостей:"
	echo " rpmlib(CaretInVersions) <= 4.15.0-1 нужен для systemd-249.12-2.el7.x86_64"
	echo " Описание решения: https://redos.red-soft.ru/base/update/update-redos-73-corr-releases/?nocache=1732110214093"
	echo "dnf update -y rpm"
	echo "dnf update -y"
	echo "dnf update -y #второй раз тоже"
	echo "	##Зависимости разрешены."
	echo "	##Отсутствуют действия для выполнения."
	echo "	##Выполнено!"
	echo "dnf clean packages"	
    exit 1
fi


echo "[$(date +%Y%m%d-%T)] Установить необходимые пакеты"
#dnf install -y htop screen mc wget ntp  || echo "========== Обнаружена ОШИБКА! =========="
dnf install -y PyQt4 qt-mysql gcc swig ftp	|| echo "========== Обнаружена ОШИБКА! =========="
dnf install -y python2-pyserial python2-requests python2-isodate python2-devel python2-pip || echo "========== Обнаружена ОШИБКА! =========="

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
mv client_lin.tar.gz /opt/

### Или скачиваем по ssh
### Скопировать с сервера каталог /var/ftp/pub/update/client_lin.tar.gz в директорию /opt
#scp ftp@192.168.1.225:/var/ftp/pub/update/client_lin.tar.gz /opt/
#  ## Пароль: ввести пароль от учетной записи "ftp" на сервере МИС (пасс у КМИАЦ "ftp")
  
echo "[$(date +%Y%m%d-%T)] Распаковываем клиента"
tar xzf /opt/client_lin.tar.gz -C /opt || echo "========== Обнаружена ОШИБКА! =========="

echo "[$(date +%Y%m%d-%T)] Выдаем все права каталогу с клиентом"
chmod -R 777 /opt/client

user=`ls /home`
echo "[$(date +%Y%m%d-%T)] Создаем ярлык на рабочем столе"
cp /opt/client/Samson_AutoUP.desktop "/home/$user/Рабочий стол/"
chmod 777 "/home/$user/Рабочий стол/Samson_AutoUP.desktop"

echo "[$(date +%Y%m%d-%T)] Настраиваем ЕМИС"
mkdir -p /home/$user/.config/samson-vista
echo '[db]
serverName='$server'
database='$baza'

[appPrefs]
TFCheckPolicy=1
provinceKLADR=2300000000000
defaultKLADR=2300000000000
orgId=
' > /home/$user/.config/samson-vista/S11App.ini
chmod 777 /home/$user/.config/samson-vista/S11App.ini

echo "########################################"
echo "############ Установка pip2 ############"
echo "########################################"

echo "[$(date +%Y%m%d-%T)] Устанавливаем необходимые пакеты pip2"
pip2 install --upgrade setuptools || echo "========== Обнаружена ОШИБКА! =========="
pip2 install --upgrade pip 		  || echo "========== Обнаружена ОШИБКА! =========="
pip2 install wheel 				  || echo "========== Обнаружена ОШИБКА! =========="

pip2 install /opt/client/install/ZSI-2.1-a1.tar.gz	|| echo "========== Обнаружена ОШИБКА! =========="
pip2 install /opt/client/install/PyXML-0.8.4.tar.gz || echo "========== Обнаружена ОШИБКА! =========="
cat /opt/client/requirements.txt
pip2 install -r /opt/client/requirements.txt || echo "========== Обнаружена ОШИБКА! =========="

echo "[$(date +%Y%m%d-%T)] Запуск ЕМИС можно проверить командой (ВАЖНО: запуск только от пользователя):
python2 /opt/client/s11main.py"

echo "[$(date +%Y%m%d-%T)] Установка завершена!"



