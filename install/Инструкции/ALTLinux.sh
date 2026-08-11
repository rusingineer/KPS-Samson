#!/bin/bash
### для Альт ОС

VERSION="Версия скрипта 7 от 22.07.2026г"

# Подходит для ОС:
#	ALT SP Workstation 10.X
#	ALT Workstation 10.X (Autolycus)
#	ALT Workstation 11.X (Prometheus)

# Установка клиентской части МИС САМСОН на ОС Альт.
# su -
# cd /home/user/
# bash ALTLinux.sh

# Все пишем в лог рядом со скриптом
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Лог файл
BACKUP_LOG="$SCRIPT_DIR/ALTLinux.log"
# Перенаправляем stdout и stderr
exec > >(tee -a "$BACKUP_LOG")
exec 2>&1

# Дата и время
timestamp() {
    printf '%(%F %T)T'
}

# Функция запуска с выводом ошибки
run() {
    local rc=$1
    shift

    "$@"
    local cmd_rc=$?

    if (( cmd_rc != 0 )); then
        log "Команда завершилась с ошибкой ($cmd_rc): $*"
        exit "$rc"
    fi
}

# Функцию логирования, для добавления даты
log() {
    printf '[%(%F %T)T] %s\n' -1 "$*"
}

#Выполняем в конце после exit
function exit-trap
{
    local rc=$1

	case "$rc" in
        0)
            log "Скрипт ALTLinux.sh выполнен успешно."
			log "Запуск ЕМИС можно проверить командой (ВАЖНО: запуск только от пользователя): python2 /opt/client/s11main.py"
			;;
        *)
            log "✕✕✕ Завершение скрипта с кодом ошибки $rc"
            ;;
    esac
	log "Создан лог файл $BACKUP_LOG"
}
trap 'exit-trap $?' EXIT

log "======= Запущен скрипт установки ЛИН-клиента ЕМИС $VERSION =======" >> /root/.install.ver
log "======= Запущен скрипт установки ЛИН-клиента ЕМИС $VERSION =======" 

#================= Проверки =================
if ! grep "ALT" /etc/os-release > /dev/null ; then
	log "ОС не Альт, установка невозможна!"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    log "Запустите скрипт от root !"
    log "Введите: su -"
    exit 2
fi

ping -c 3 8.8.8.8 || {
	log "Отсутствует доступ к интернету, установка невозможна!"
	exit 3
	}
	
# Проверить наличие программ
for cmd in apt-get tar; do
    command -v "$cmd" >/dev/null || {
        log "Команда $cmd не найдена!"
        exit 4
    }
done

#================= Установка =================
log "###########################################"
log "############ Настройка системы ############"
log "###########################################"

# Определим ОС и настроим репы
source /etc/os-release
MAJOR_VERSION=${VERSION_ID%%.*}
case "$NAME:$MAJOR_VERSION" in
    "ALT SP Workstation:10")
        log "Раскомментировать репозиторий c10f (Только для: ALT SP Workstation версии 10)"
		run 5 sed -i 's/#rpm \[cert8\] http/rpm \[cert8\] http/' /etc/apt/sources.list.d/altsp.list
        ;;
    "ALT Workstation:10")
        log "Раскомментировать репозиторий p10 (Только для: ALT Workstation версии 10)"
		run 6 sed -i 's/#rpm \[p10\] http/rpm \[p10\] http/' /etc/apt/sources.list.d/alt.list 
        ;;
    "ALT Workstation:11")
        log "Раскомментировать репозиторий p11 (Только для: ALT Workstation версии 11)"
		run 7 sed -i 's/#rpm \[p11\] http/rpm \[p11\] http/' /etc/apt/sources.list.d/alt.list 
		log "Добавить репозиторий p10 (Только для: ALT Workstation версии 11)"
		run 8 apt-repo add p10 
        ;;
esac

log "Посмотреть текущие репозитории"
run 9 apt-repo list -a

log "Обновить списки пакетов"
run 10 apt-get update

log "Установить необходимые пакеты"
PACKAGES=(
    python-module-PyQt4
    python-module-requests
    python-module-serial
    python-module-isodate
    python-dev
    python-modules-distutils
    nano
    ftp
    sudo
    wget
    gcc
    swig
    libqt4-sql-mysql
    libmysqlclient21
    libpcsclite-devel
    libenchant
)
run 11 apt-get install -y "${PACKAGES[@]}"  

# Вылетов МИС меньше и печать быстрее
log "Отключение системы обеспечивающей обнаружение сервисов в локальной сети:"
systemctl disable avahi-daemon >/dev/null 2>&1 || true
systemctl stop avahi-daemon >/dev/null 2>&1 || true

## Это веб интерфейс сервера печати для удаленных принтеров https://packages.debian.org/ru/sid/cups-browsed
#log "Отключение удаленных принтеров:"
#systemctl disable cups-browsed  >/dev/null 2>&1 || true
#systemctl stop cups-browsed  >/dev/null 2>&1 || true


log "########################################"
log "############ Установка ЕМИС ############"
log "########################################"
read -r -p "Введите IP-адрес сервера БД: " server
log "$server"
read -r -p "Введите имя БД: " baza
log "$baza"

### FTP ###
FTPD="/pub/update"
FTPU="anonymous" #[имя пользавателя (логин) удаленного ftp-cервера]
FTPP="megapassword" #[пароль доступа к удаленному ftp-серверу]
FTPS="$server" #[собственно, адрес ftp-сервера или его IP]
FTPFILE="client_lin.tar.gz" #[файл]
FTP="$(which ftp)"

log "Скачиваем client_lin.tar.gz с сервера БД по ФТП..."
$FTP -n $FTPS <<END_SCRIPT
 quote USER $FTPU
 quote PASS $FTPP
 cd $FTPD
 binary
 get $FTPFILE
 quit
END_SCRIPT
run 12 mv client_lin.tar.gz /opt/ 
### Или скачиваем по ssh
### Скопировать с сервера каталог /var/ftp/pub/update/client_lin.tar.gz в директорию /opt
#scp ftp@192.168.1.225:/var/ftp/pub/update/client_lin.tar.gz /opt/
#  ## Пароль: ввести пароль от учетной записи "ftp" на сервере МИС (пасс у КМИАЦ "ftp")
  
log "Распаковываем клиента"
run 13 tar xzf /opt/client_lin.tar.gz -C /opt 

log "Выдаем все права каталогу с клиентом"
chmod -R 777 /opt/client
user=$(logname)
chown $user:$user -R /opt/client

log "Создаем ярлык на рабочем столе"
cp /opt/client/Samson_AutoUP.desktop "/home/$user/Рабочий стол/"
chmod 755 "/home/$user/Рабочий стол/Samson_AutoUP.desktop"
chown $user:$user "/home/$user/Рабочий стол/Samson_AutoUP.desktop"

log "Настраиваем ЕМИС"
mkdir -p /home/$user/.config/samson-vista
cat > "/home/$user/.config/samson-vista/S11App.ini" <<EOF
[db]
serverName=$server
database=$baza

[appPrefs]
provinceKLADR=2300000000000
defaultKLADR=2300000000000
EOF

chmod 777 /home/$user/.config/samson-vista/S11App.ini
chown $user:$user -R /home/$user/.config

log "Устанавливаем шрифты для печати штрихкода и другие"
#https://www.altlinux.org/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0_%D1%88%D1%80%D0%B8%D1%84%D1%82%D0%BE%D0%B2
cp /opt/client/install/fonts/*.ttf /usr/share/fonts/ttf/
fc-cache -f -v

log "########################################"
log "############ Установка pip2 ############"
log "########################################"

log "Устанавливаем необходимые пакеты pip2"

#apt-get install -y python-module-pip #вместо этого исключенного пакета:
#https://pip.pypa.io/en/stable/installation/
#curl 'https://bootstrap.pypa.io/pip/2.7/get-pip.py' > /opt/client/install/get-pip.py  # можно скачать
run 14 python2 /opt/client/install/get-pip.py 
run 15 pip2 install --upgrade setuptools
run 16 pip2 install --upgrade pip
run 17 pip2 install wheel 
run 18 pip2 install /opt/client/install/ZSI-2.1-a1.tar.gz 
run 19 pip2 install /opt/client/install/PyXML-0.8.4.tar.gz
cat /opt/client/requirements.txt
run 20 pip2 install -r /opt/client/requirements.txt 

