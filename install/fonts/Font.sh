#!/bin/bash
NOW=$(date +%Y%m%d-%T)
f=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
echo "[$(date +%Y%m%d-%T)] ======= Установка шрифтов Font.sh v1.0 ======="
cd $f
dir=/usr/share/fonts

if [ ! -f $dir/code39/code39.ttf ]; then
	echo install fonts code39 and Code128...
	mkdir -p $dir/code39
	mkdir -p $dir/Code128
	cp code39.ttf   $dir/code39/
	cp Code128.ttf  $dir/Code128/
fi

if [ ! -f $dir/pt-root/pt-root-ui_regular.ttf ]; then
	echo install fonts pt-root...
	mkdir -p $dir/pt-root
	cp pt-root*.ttf   $dir/pt-root/
fi
 
if [ ! -f $dir/Liberation/LiberationMono-Regular.ttf ]; then
	echo install fonts Liberation...
	mkdir -p $dir/Liberation
	cp Liberation*.ttf   $dir/Liberation/
fi
 
#echo "[$(date +%Y%m%d-%T)] ======= Установка шрифтов Font.sh v1.0 =======" >> /root/.install.ver