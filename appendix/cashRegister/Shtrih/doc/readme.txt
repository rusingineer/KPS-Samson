Взаимодействие с ККТ Штрих-М

В принципе для взаимодействия с ККТ Штрих-М есть три подхода:
- Написать низкоуровневую обвязку самостоятельно
- Использовать официальный драйвер (например, DrvFR_5.17_909)
- Использовать несколько менее официальный драйвер fr_drv_ng

Как водится, у каждого решения есть достоинства и недостатки.

Для собственной низкоуровневой обвязки препятствиями являются трудоёмкость собственно написания
помноженная на несоответствие реального обмена и описания обмена в документации, плюс необходимость 
тестирования совместимости реализации с каждой моделью. 

Официальный DrvFR существует только под windows и реализован как COM-объект,
таким образом linux оказывается в пролёте.

Поэтому в качестве базы для взаимодействия с ККТ Штрих-М выбран fr_drv_ng
( https://github.com/shtrih-m/fr_drv_ng , https://git.shtrih-m.ru/ )
Авторы fr_drv_ng ссылаются на документацию https://exam.shtrih-m-partners.ru/assets/materials/DrayverKKT_517_10_12_22.zip ,
но нужно быть осторожным, иногда бывают досадные различия между fr_drv_ng и виндовым COM-драйвером.

В разработке использована версия 1.6.0-14, эту версию можно скачать - 
( см. https://github.com/shtrih-m/fr_drv_ng/releases )

https://github.com/shtrih-m/fr_drv_ng/releases/download/1.6.0-14-g0fbabb3/fr_drv_ng_linux_x86_64_1.6.0-14-g0fbabb3.zip
https://github.com/shtrih-m/fr_drv_ng/releases/download/1.6.0-14-g0fbabb3/fr_drv_ng_linux_i686_1.6.0-14-g0fbabb3.zip

https://github.com/shtrih-m/fr_drv_ng/releases/download/1.6.0-14-g0fbabb3/fr_drv_ng_linux_aarch64_le_1.6.0-14-g0fbabb3.zip
https://github.com/shtrih-m/fr_drv_ng/releases/download/1.6.0-14-g0fbabb3/fr_drv_ng_linux_armv7hf_le_1.6.0-14-g0fbabb3.zip

https://github.com/shtrih-m/fr_drv_ng/releases/download/1.6.0-14-g0fbabb3/fr_drv_ng_windows_mingw_i386_mingw_1.6.0-14-g0fbabb3.zip
https://github.com/shtrih-m/fr_drv_ng/releases/download/1.6.0-14-g0fbabb3/fr_drv_ng_windows_i386_msvc_1.6.0-14-g0fbabb3.zip

https://github.com/shtrih-m/fr_drv_ng/releases/download/1.6.0-14-g0fbabb3/fr_drv_ng_windows_mingw_x86_64_mingw_1.6.0-14-g0fbabb3.zip
https://github.com/shtrih-m/fr_drv_ng/releases/download/1.6.0-14-g0fbabb3/fr_drv_ng_windows_x86_64_msvc_1.6.0-14-g0fbabb3.zip

Поскольку у меня сейчас linux и x86_64, начнём со своего случая - возьмём fr_drv_ng_linux_x86_64_1.6.0-14-g0fbabb3.zip :

   Date      Time    Attr         Size   Compressed  Name
------------------- ----- ------------ ------------  ------------------------
2023-10-17 04:39:29 D....            0            0  dist/linux_1.6.0.595
2023-10-17 04:43:30 D....            0            0  dist/linux_1.6.0.595/x86_64
2023-10-17 04:43:30 .....           32           38  dist/linux_1.6.0.595/x86_64/QClassicFrDrvNg
2023-10-17 04:43:30 .....       151219        15557  dist/linux_1.6.0.595/x86_64/c_classic_interface.h
2023-10-17 04:43:30 .....       582272        82366  dist/linux_1.6.0.595/x86_64/classic_interface.h
2023-10-17 04:43:30 .....        64867         9179  dist/linux_1.6.0.595/x86_64/classic_interface.i
2023-10-17 04:43:30 .....           84           84  dist/linux_1.6.0.595/x86_64/console_test.sh
2023-10-17 04:43:01 .....           26           26  dist/linux_1.6.0.595/x86_64/console_test_fr_drv_ng
2023-10-17 04:43:01 .....      6084304      2460434  dist/linux_1.6.0.595/x86_64/console_test_fr_drv_ng-1.6
2023-10-17 04:41:24 .....           27           27  dist/linux_1.6.0.595/x86_64/libclassic_fr_drv_ng.so
2023-10-17 04:41:24 .....      5706456      2154083  dist/linux_1.6.0.595/x86_64/libclassic_fr_drv_ng.so.1.6
2023-10-17 04:43:29 .....           28           28  dist/linux_1.6.0.595/x86_64/libone_s_fr_drv_ng_32.so
2023-10-17 04:43:29 .....      2326112       973838  dist/linux_1.6.0.595/x86_64/libone_s_fr_drv_ng_32.so.0.1
2023-10-17 04:43:30 .....           28           28  dist/linux_1.6.0.595/x86_64/libone_s_fr_drv_ng_40.so
2023-10-17 04:43:30 .....      2338400       977297  dist/linux_1.6.0.595/x86_64/libone_s_fr_drv_ng_40.so.0.1
2023-10-17 04:43:07 .....           28           28  dist/linux_1.6.0.595/x86_64/libqclassic_fr_drv_ng.so
2023-10-17 04:43:07 .....        10192         2952  dist/linux_1.6.0.595/x86_64/libqclassic_fr_drv_ng.so.1.6
2023-10-17 04:43:30 D....            0            0  dist/linux_1.6.0.595/x86_64/libs
2023-10-17 04:43:30 .....       182064        90860  dist/linux_1.6.0.595/x86_64/libs/ld-linux-x86-64.so.2
2023-10-17 04:43:30 .....      2166744       897494  dist/linux_1.6.0.595/x86_64/libs/libc.so.6
2023-10-17 04:43:30 .....       784360       169876  dist/linux_1.6.0.595/x86_64/libs/libgcc_s.so.1
2023-10-17 04:43:30 .....      1913552      1166785  dist/linux_1.6.0.595/x86_64/libs/libm.so.6
2023-10-17 04:43:30 .....       151112        57741  dist/linux_1.6.0.595/x86_64/libs/libpthread.so.0
2023-10-17 04:43:30 .....      1786104       522952  dist/linux_1.6.0.595/x86_64/libs/libstdc++.so.6
2023-10-17 04:43:30 .....       197793        34697  dist/linux_1.6.0.595/x86_64/qclassic_interface.h
2023-10-17 04:43:30 .....         3232         1083  dist/linux_1.6.0.595/x86_64/setup.py
------------------- ----- ------------ ------------  ------------------------
2023-10-17 04:43:30           24449036      9617453  23 files, 3 folders


Это не очень похоже на обычный образ для установки, причём это политика разработчика - 
типа «хотите пакетов - собирайте, а мне не надо; да и вам не надо»

Поэтому скопируем libclassic_fr_drv_ng.so.1.6 в /opt/fr_drv_ng/lib
и создадим подходящий симлинк -

/opt/fr_drv_ng/lib
итого 5576
lrwxrwxrwx 1 root root      27 ноя 14 19:00 libclassic_fr_drv_ng.so -> libclassic_fr_drv_ng.so.1.6
-rwxr-xr-x 1 root root 5706456 ноя 14 18:59 libclassic_fr_drv_ng.so.1.6

Поскольку ldd для /opt/fr_drv_ng/lib/libclassic_fr_drv_ng.so показывает что-то разумное делаем вывод что
libclassic_fr_drv_ng.so "прижился".

Далее, мы видим setup.py и classic_interface.i - это биндинг для python.
К сожалению oн имеет следующие недостатки:
- он по разному реализует работу со строками в python2 и python3,
  в python2 строковые значения передаются типом str (в utf-8)
  в python3 строковые значения передаются типом str (в unicode)
  что затруднит переход p2->p3
- он не может собраться в windows для python2 при использовании рекомендованного для сборки python2
  msvc, так как использован несколько более продвинутый диалект C++.

Поэтому я написал свою обвязку с использованием ctypes,
которая генерируется на основании разметки doxygen в classic_interface.h.

Для перегенерации привязки нужно:
- скопировать classic_interface.h в generate-binding/h/
- перейти в generate-binding
- запустить doxygen
- запустить ./generate_fr_drv_ng_with_ctypes.py >fr_drv_ng.py
- скопировать полученный fr_drv_ng.py в хорошее место.
- можно удалить директорий xml, он нам больше не нужен.

Теперь давайте позаботимся о пользователях Windows.
Для этого случая авторы fr_drv_ng предоставляют четыре архива:
fr_drv_ng_windows_i386_msvc_1.6.0-14-g0fbabb3.zip
fr_drv_ng_windows_mingw_i386_mingw_1.6.0-14-g0fbabb3.zip
fr_drv_ng_windows_x86_64_msvc_1.6.0-14-g0fbabb3.zip
fr_drv_ng_windows_mingw_x86_64_mingw_1.6.0-14-g0fbabb3.zip

Как нетрудно понять, в архивах имеющих в названии msvc программы и библиотеки собраны с применением MS Visual Studio,
mingw - MinGW-win64, i386 - для 32-битного windows, x86_64 - для 64-разрядного windows.
Хорошо, что в наших краях windowsы на ARM не распространены.

У меня нет критерия выбора msvc/mingw, поэтому опишу оба случая.
Вдруг у Вас сработает только что-то одно?

В fr_drv_ng_windows_i386_msvc_1.6.0-14-g0fbabb3.zip для нас важны
библиотека драйвера classic_fr_drv_ng.dll, и тестовая утилита - console_test_fr_drv_ng.exe.
classic_fr_drv_ng.dll можно записать в директорий рядом с cashRegister.exe .
console_test_fr_drv_ng.exe нам для работы не нужен, но может быть использован для проверки наличия
необходимых библиотек. Если console_test_fr_drv_ng.exe не запускается, то нужно поставить 
подходящий vc_redist. В windows10 и выше может помочь winget:
C:> winget install Microsoft.VCRedist.2015+.x86
в других версиях см. https://learn.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-170

В fr_drv_ng_windows_mingw_i386_mingw_1.6.0-14-g0fbabb3.zip для нас важны
библиотека драйвера libclassic_fr_drv_ng.dll, и тестовая утилита - console_test_fr_drv_ng.exe.
libclassic_fr_drv_ng.dll можно записать в директорий рядом с cashRegister.exe .
console_test_fr_drv_ng.exe нам для работы по прежнему не нужен,
но может быть использован для проверки наличия необходимых библиотек.
Если console_test_fr_drv_ng.exe не запускается с жалобами на разделяемые библиотеки
libgcc_s_dw2-1.dll, libstdc++-6.dll и libwinpthread-1.dll, то их нужно взять из MinGW-w64.
Согласно https://github.com/shtrih-m/fr_drv_ng/issues/191 нужен MinGW-w64 версии 8.1.0
( https://wiki.qt.io/MinGW#MinGW_distributions_and_versions, 
  https://sourceforge.net/projects/mingw-w64/files/Toolchains%20targetting%20Win32/Personal%20Builds/mingw-builds/8.1.0/threads-posix/dwarf/i686-8.1.0-release-posix-dwarf-rt_v6-rev0.7z/download )
Качаем https://altushost-swe.dl.sourceforge.net/project/mingw-w64/Toolchains%20targetting%20Win32/Personal%20Builds/mingw-builds/8.1.0/threads-posix/dwarf/i686-8.1.0-release-posix-dwarf-rt_v6-rev0.7z
и там в mingw32/bin берём искомые библиотеки.

У меня нет намерения вот прямо сейчас исследовать 64-битную сборку cashRegister.exe.
Но на первый взгляд логически всё что было написано для 32-битной остаётся в силе,
поменяются только версии vc_redist и MinGW-w64.

Надеюсь, что перегенерация привязки для windows не потребуется, «жричодали».

-*-

fr_drv_ng в текущем директории ведёт сумасшедший по подробности и объёму журнал.
Как написано в classic_interface.h:
    //! @brief Логгирование в драйвере глобальное и включено всегда.
    //!
    //! Управление происходит через следующие переменные окружения <br>
    //! * FR_DRV_DEBUG_CONSOLE - если определено весь вывод лога будет на stderr <br>
    //! * FR_DRV_LOG_PATH - путь файла лога(по умолчанию fr_drv.log в рабочей директории)<br>
    //! * FR_DRV_LOG_FILE_COUNT - кол-во ротаций(по умолчанию 2)<br>
    //! * FR_DRV_LOG_PART_SIZE - размер части в байтах (по умолчанию 1024 * 1024 * 10)<br>
    //! * FR_DRV_LOG_FLAGS - флаги логгирования, битовая маска со следующими ключами(по умолчанию
    //! всё включено)
    //!
    //!     * 1 << 0 - логгировать обмен
    //!     * 1 << 1 - логгировать каждый read/write в IoLayer, иначе аккумулировать
    //!     * 1 << 2 - логгировать отладку протокола
    //!     * 1 << 3 - логгировать статистику протокола
    //!     * 1 << 4 - логгировать отладку функций-утилит
    //!     * 1 << 5 - логгировать отладку вызовов интерфейсов верхнего уровня (classic,upos, итд)

Таким образом для выключения избыточного журналирования можно установить переменную окружения FR_DRV_LOG_FLAGS=0

