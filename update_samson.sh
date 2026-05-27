#!/bin/bash
#----------------------
#source config.conf  #загружаем конфиг

NOWDATE=$(date +%Y%m%d-%T)
f=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
outdir="/opt/client/install/update"
mkdir -p "$outdir"
outfile="$outdir/update.log"
echo "
[$(date +%Y%m%d-%T)] СТАРТ update_samson.sh v8!" >> $outfile

# Запрет повторного запуска
LOCKFILE=$outdir/Samson.LOCKFILE
exec 200>>$LOCKFILE
flock -n 200 || exit 1
PID=$$
echo $PID 1>&200
chmod 777 $LOCKFILE

echo "dir=$f" >> "$outfile"
homedir=$HOME
#if [ -f "$homedir/Рабочий стол/Samson_AutoUP.desktop" ] ; then desktop="$homedir/Рабочий стол"; fi ;
#if [ -f "$homedir/Desktop/Samson_AutoUP.desktop" ] ; then desktop="$homedir/Desktop"; fi ;
desktop=`xdg-user-dir DESKTOP`
mkdir -p "$desktop"
echo "homedir = $homedir" >> "$outfile"
echo "desktop = $desktop" >> "$outfile"
file=$homedir/.config/samson-vista/S11App.ini
serverTemp=`grep ^serverName= $file`
server=${serverTemp##*=}
echo "server = $server"
echo "server = $server" >> "$outfile"

### FTP ###
FTPD="/pub/update"
FTPU="anonymous" #[имя пользавателя (логин) удаленного ftp-cервера]
FTPP="megapassword" #[пароль доступа к удаленному ftp-серверу]
FTPS="$server" #[собственно, адрес ftp-сервера или его IP]
FTPFILE="client_lin.tar.gz" #[файл]
FTP="$(which ftp)"
UPDIR="$outdir"

### ftp ###
cd "$UPDIR"
if [ -f VERSION ] ; then rm -r VERSION ; fi ; 
echo "Подключение к ФТП для проверки версии..."
$FTP -n $FTPS <<END_SCRIPT
quote USER $FTPU
quote PASS $FTPP
cd $FTPD
binary
get VERSION
quit
END_SCRIPT

if [ ! -f VERSION ] ; then
	echo "Ошибка подключения к ФТП. Автообновление недоступно! Запускаем МИС без обновления!" 
	echo "Ошибка подключения к ФТП. Автообновление недоступно! Запускаем МИС без обновления!" >> "$outfile"
	python2 /opt/client/s11main.py
	exit 0
fi

source VERSION #загружаем скачанный конфиг 
#echo "update_new=$update" >> "$outfile"
echo "version_new = $version" >> "$outfile"
version_new=$version
#update_new=$update

source /opt/client/VERSION
#echo "update=$update" >> "$outfile"
echo "version = $version" >> "$outfile"

#if [[ $update_new > $update || $version_new > $version ]] ; then 
if [ "$(printf '%s\n' "$version" "$version_new" | sort -V | head -n1)" = "$version" ]; then 
 	echo "Необходимо обновление..." 
	echo "Необходимо обновление..." >> "$outfile"
	echo "Необходимо обновление..." > "$desktop/Обновление МИС САМСОН"

	#rm "$desktop/Samson_AutoUP.desktop"
	#enconv -x utf8 "$desktop/Samson_AutoUP.desktop"

	# Старый и новый ярлыки
	if ! grep "САМСОН" "$desktop/Samson_AutoUP.desktop" ; then 
		sed -i 's/Samson_AutoUP/Выполняется обновление, подождите.../g' "$desktop/Samson_AutoUP.desktop"
		label=1
	else
		sed -i 's/САМСОН/Выполняется обновление, подождите.../g' "$desktop/Samson_AutoUP.desktop"
		label=2
	fi
	
	echo "[$(date +%Y%m%d-%T)] Скачиваем client_lin.tar.gz ..."
	$FTP -n $FTPS <<END_SCRIPT
    quote USER $FTPU
    quote PASS $FTPP
    cd $FTPD
    binary
    get $FTPFILE
    quit
END_SCRIPT
	
	#echo "[$(date +%Y%m%d-%T)] Cкачали, удаляем лишнее..."
	#echo '11' | sudo rm -rf /opt/client_old /opt/update.log /opt/LinuxVersion /opt/client_lin.tar.gz /opt/VERSION /opt/Samson.LOCKFILE
	
	echo "[$(date +%Y%m%d-%T)] Распаковываем client_lin.tar.gz" 
	tar xvzf client_lin.tar.gz -C /opt/client --strip-components=1 >> "$desktop/Обновление МИС САМСОН" 2>&1 
	echo "[$(date +%Y%m%d-%T)] Клиент обновлен до версии $version_new!" 
	echo "[$(date +%Y%m%d-%T)] Клиент обновлен до версии $version_new!" >> "$outfile"
	chmod 777 -R /opt/client
	chmod +x /opt/client/*.py
	chmod +x /opt/client/*.sh
	chmod +x /opt/client/install/bin/*.sh 
	
	echo "[$(date +%Y%m%d-%T)] делаем резервную копию файла настроек МИС"
	cp $file $file-$NOWDATE >> "$outfile" 2>&1

	# Дополнительная установка
	echo "[$(date +%Y%m%d-%T)] Дополнительная установка скриптом Dopinstall.sh..."
	echo "[$(date +%Y%m%d-%T)] Запуск Dopinstall.sh" >> "$outfile"
	#rm -rf "$desktop/Сбой обновления САМСОН"
	#echo '11' | sudo -S bash /opt/client/Dopinstall.sh >> "$outfile" 2>&1 || echo "Ошибка выполнения /opt/client/Dopinstall.sh, смотри лог /opt/client/install/update.log" > "$desktop/Сбой обновления САМСОН"
	bash /opt/client/Dopinstall.sh >> "$outfile" 2>&1 || echo "Ошибка выполнения /opt/client/Dopinstall.sh"
	echo "[$(date +%Y%m%d-%T)] Dopinstall.sh выполнен" >> "$outfile"
		
	#echo "[$(date +%Y%m%d-%T)] Создание ярлыка Samson_AutoUP" >> "$outfile"
	#cp /opt/client/Samson_AutoUP.desktop "$desktop/Samson_AutoUP.desktop"
    #chmod +x "$desktop/Samson_AutoUP.desktop"
	
	if [ -f "$desktop/Обновление МИС САМСОН" ] ; then rm "$desktop/Обновление МИС САМСОН" ; fi ;
	if [ $label = 1 ] ; then # Старый и новый ярлыки
		sed -i 's/Выполняется обновление, подождите.../Samson_AutoUP/g' "$desktop/Samson_AutoUP.desktop"
	else
		sed -i 's/Выполняется обновление, подождите.../САМСОН/g' "$desktop/Samson_AutoUP.desktop"
	fi	
else 
	echo "Обновление не требуется" 
	echo "Обновление не требуется" >> "$outfile"
fi;
echo "" >> "$outfile"

#запуск МИС
python2 /opt/client/s11main.py 

echo "Подробный лог $outfile"
rm -rf $LOCKFILE
### clear ###

