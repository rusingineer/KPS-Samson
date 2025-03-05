#!/bin/bash
#echo '11' | sudo -S sudo yum list qtsoap* ;
echo --------$(date +%Y%m%d-%T) Start Dopinstall.sh--------
DIR=/opt/client/install

# Установить шрифты
bash $DIR/fonts/Font.sh || echo "Ошибка выполнения Font.sh"

# Для Альт Линукс ничего больше не делаем
cat /etc/os-release > LinuxVersion
if grep "altlinux" LinuxVersion ; then 
	echo "====Альт Линукс====" 
	exit 666
fi

## Подходит для всех ОС
#pip2 list --format=legacy > $DIR/pip2.list || exit 601  #не работает на 7,3,1
pip2 list > $DIR/pip2.list || echo "Ошибка выполнения pip2 list"

if ! grep "PyXB" $DIR/pip2.list ; then 
	pip2 install $DIR/PyXB-1.2.6.tar.gz || echo "Ошибка выполнения pip2 install $DIR/PyXB-1.2.6.tar.gz"
fi

if ! grep "numpy" $DIR/pip2.list ; then 
	pip2 install $DIR/numpy-1.16.6-cp27-cp27mu-manylinux1_x86_64.whl || echo "Ошибка выполнения pip2 install $DIR/numpy-1.16.6-cp27-cp27mu-manylinux1_x86_64.whl"
fi

if ! grep "Pillow" $DIR/pip2.list ; then 
	pip2 install $DIR/Pillow-6.2.2-cp27-cp27mu-manylinux1_x86_64.whl || echo "Ошибка выполнения pip2 install $DIR/Pillow-6.2.2-cp27-cp27mu-manylinux1_x86_64.whl"
fi

if ! grep "scipy" $DIR/pip2.list ; then 
	pip2 install $DIR/scipy-1.2.3-cp27-cp27mu-manylinux1_x86_64.whl || echo "Ошибка выполнения pip2 install $DIR/scipy-1.2.3-cp27-cp27mu-manylinux1_x86_64.whl"
fi

if ! grep "pyBarcode" $DIR/pip2.list ; then 
	pip2 install $DIR/pyBarcode-0.8b1-cp27-none-any.whl || echo "Ошибка выполнения pip2 install $DIR/pyBarcode-0.8b1-cp27-none-any.whl"
fi

if ! grep "lxml" $DIR/pip2.list ; then 
	pip2 install $DIR/lxml-4.9.3-cp27-cp27mu-manylinux_2_5_x86_64.manylinux1_x86_64.whl || echo "Ошибка выполнения pip2 install $DIR/lxml-4.9.3-cp27-cp27mu-manylinux_2_5_x86_64.manylinux1_x86_64.whl"
fi

# Чиним проверку орфографии
cat /etc/os-release > LinuxVersion
if grep "RED OS" LinuxVersion ; then 
	echo "====РЕД ОС====" 
	echo "Чиним проверку орфографии"	
	rm -f /usr/lib64/libhunspell.so
	ln -s /usr/lib64/libhunspell-1.7.so.0.0.1 /usr/lib64/libhunspell.so
fi

echo --------$(date +%Y%m%d-%T) End Dopinstall.sh--------






