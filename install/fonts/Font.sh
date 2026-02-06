#!/bin/bash
NOW=$(date +%Y%m%d-%T)
f=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
echo "[$(date +%Y%m%d-%T)] ======= Установка шрифтов Font.sh v2.0 ======="
cd $f

# Для Альт ОС https://www.altlinux.org/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0_%D1%88%D1%80%D0%B8%D1%84%D1%82%D0%BE%D0%B2
if ! grep "ALT" /etc/os-release ; then
	echo "ОС не ALT, установка невозможна!"
    exit 0
fi

if [[ $EUID -ne 0 ]]; then # проверка
    echo "Cкрипт запущен от пользователя, шрифты будут установлены только для него!"
	dir=$HOME/.fonts
else
    echo "Cкрипт запущен от root, шрифты будут установлены для всех пользователей!"
	dir=/usr/share/fonts/ttf/
fi

echo "Копирование шрифтов в $dir"
mkdir -p $dir
cp /opt/client/install/fonts/*.ttf $dir/

echo "Обновление кэша шрифтов"
fc-cache -f -v | grep "$dir: caching"

echo "[$(date +%Y%m%d-%T)] ======= Font.sh v2.0 end ======="