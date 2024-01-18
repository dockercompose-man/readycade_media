@echo off
setlocal enabledelayedexpansion

::--------------------------------------------------------------------
::VARS::
set "authURL=https://forum.readycade.com/auth.php"

::--------------------------------------------------------------------
::CHECK NETWORK SHARE::

echo Checking if the network share is available...
ping -n 1 RECALBOX >nul
if %errorlevel% neq 0 (
    echo Error: Could not connect to the network share \\RECALBOX.
    echo Please make sure you are connected to the network and try again.
    pause
    exit /b
)
echo.

::--------------------------------------------------------------------

::--------------------------------------------------------------------
::PROMPT FOR USERNAME AND PASSWORD (no echo for password)::

set /p "dbUsername=Enter your username: "
set "dbPassword="
powershell -Command "$dbPassword = Read-Host 'Enter your password' -AsSecureString; [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPassword)) | Out-File -FilePath credentials.txt -Encoding ASCII"
set /p dbPassword=<credentials.txt
del credentials.txt
::--------------------------------------------------------------------


::--------------------------------------------------------------------
::DELETE THIS BEFORE PRODUCTION!!!!!!!!!::
::--------------------------------------------------------------------
:: To Debug username/password
:: echo dbUsername=!dbUsername!
:: echo dbPassword=!dbPassword!
::--------------------------------------------------------------------

::--------------------------------------------------------------------
::AUTHENTICATION::
rem Perform authentication by sending a POST request to auth.php using the captured credentials
curl -X POST -d "dbUsername=!dbUsername!&dbPassword=!dbPassword!" -H "Content-Type: application/x-www-form-urlencoded" "!authURL!" > auth_result.txt


rem Check the authentication result
set /p authResult=<auth_result.txt

if "!authResult!" neq "Authenticated" (
    echo Authentication failed. Exiting script...
    del auth_result.txt
    pause
    exit /b
) else (
    echo Authentication successful. Proceeding with installation...
    del auth_result.txt
)

echo.
echo.
::--------------------------------------------------------------------

::--------------------------------------------------------------------
::10 SECOND COUNTDOWN MESSAGE::

rem Wait for 10 seconds and display a countdown message
for /l %%A in (10,-1,1) do (
    cls
    rem Display important notice and warning
    echo IMPORTANT NOTICE: You are about to install images, videos, boxart to \\RECALBOX downloaded from screenscraper.fr.
    echo This operation will overwrite existing media folder on \\RECALBOX\share\roms\%VARIABLE%. Make sure you have backup copies of your important files before proceeding.
    echo.
    echo Readycade Inc and its affiliates are not responsible for any legal issues that may arise from the use of these files.
    echo Use at your own risk. We do not condone piracy or any unauthorized use of copyrighted material.
    echo.
    echo Thank you for choosing Readycade!
    echo.
    echo Starting installation automatically in %%A seconds...
    timeout /t 1 >nul
)
echo.
echo.
::--------------------------------------------------------------------

::--------------------------------------------------------------------
::INSTALL 7-ZIP::

:: Define the installation directory for 7-Zip
set "installDir=C:\Program Files\7-Zip"

:: Define the 7-Zip version you want to download
set "version=2301"

:: Define the download URL for the specified version
set "downloadURL=https://www.7-zip.org/a/7z%version%-x64.exe"

:: Check if 7-Zip is already installed by looking for 7z.exe in the installation directory
if exist "!installDir!\7z.exe" (
    echo 7-Zip is already installed.
) else (
    :: Echo a message to inform the user about the script's purpose
    echo Downloading and installing 7-Zip...

    :: Define the local directory to save the downloaded installer
    set "localTempDir=C:\Temp\readycade"

    :: Download the 7-Zip installer using curl and retain the original name
    cd /d "%localTempDir%"
    curl -L --insecure -o "7z_installer.exe" "!downloadURL!"

    :: Check if the download was successful
    if %errorlevel% neq 0 (
        echo Download failed.
        exit /b %errorlevel%
    )

    :: Run the 7-Zip installer and wait for it to complete
    start /wait "" "7z_installer.exe"

    :: Check if the installation was successful (You may want to customize this part)
    if %errorlevel% neq 0 (
        echo Installation failed.
        exit /b %errorlevel%
    )

    :: Add your additional code here to run after the installation is complete
    echo 7-Zip is now installed.
)

::--------------------------------------------------------------------

::--------------------------------------------------------------------
::MEDIA PACK VARS::

:: Define the base URL for downloading media packs
set "base_url=https://forum.readycade.com/readycade_media/"

:: Define the target directory where the media packs will be downloaded and extracted
set "target_directory=%APPDATA%\readycade\mediapacks"

:: Create the target directory if it doesn't exist
if not exist "%target_directory%" mkdir "%target_directory%"

:: Define an array of media packs (use the actual filenames with .7z extension)
set "media_packs[1]=64dd-media.7z"
set "media_packs[2]=amiga600-media.7z"
set "media_packs[3]=amiga1200-media.7z"
set "media_packs[4]=amstradcpc-media.7z"
set "media_packs[5]=apple2-media.7z"
set "media_packs[6]=apple2gs-media.7z"
set "media_packs[7]=arduboy-media.7z"
set "media_packs[8]=atari800-media.7z"
set "media_packs[9]=atari2600-media.7z"
set "media_packs[10]=atari5200-media.7z"
set "media_packs[11]=atari7800-media.7z"
set "media_packs[12]=atarist-media.7z"
set "media_packs[13]=atomiswave-media.7z"
set "media_packs[14]=bbcmicro-media.7z"
set "media_packs[15]=bk-media.7z"
set "media_packs[16]=c64-media.7z"
set "media_packs[17]=channelf-media.7z"
set "media_packs[18]=colecovision-media.7z"
set "media_packs[19]=daphne-media.7z"
set "media_packs[20]=dos-media.7z"
set "media_packs[21]=fds-media.7z"
set "media_packs[22]=gamegear-media.7z"
set "media_packs[23]=gba-media.7z"
set "media_packs[24]=gbc-media.7z"
set "media_packs[25]=gb-media.7z"
set "media_packs[26]=gw-media.7z"
set "media_packs[27]=gx4000-media.7z"
set "media_packs[28]=intellivision-media.7z"
set "media_packs[29]=jaguar-media.7z"
set "media_packs[30]=lowresnx-media.7z"
set "media_packs[31]=lutro-media.7z"
set "media_packs[32]=mastersystem-media.7z"
set "media_packs[33]=megadrive-media.7z"
set "media_packs[34]=model3-media.7z"
set "media_packs[35]=msx1-media.7z"
set "media_packs[36]=msx2-media.7z"
set "media_packs[37]=msxturbor-media.7z"
set "media_packs[38]=multivision-media.7z"
set "media_packs[39]=n64-media.7z"
set "media_packs[40]=naomigd-media.7z"
set "media_packs[41]=naomi-media.7z"
set "media_packs[42]=neogeocd-media.7z"
set "media_packs[43]=neogeo-media.7z"
set "media_packs[44]=nes-media.7z"
set "media_packs[45]=ngpc-media.7z"
set "media_packs[46]=ngp-media.7z"
set "media_packs[47]=o2em-media.7z"
set "media_packs[48]=oricatmos-media.7z"
set "media_packs[49]=pcengine-media.7z"
set "media_packs[50]=pcenginecd-media.7z"
set "media_packs[51]=pcfx-media.7z"
set "media_packs[52]=pcv2-media.7z"
set "media_packs[53]=pokemini-media.7z"
set "media_packs[54]=ports-media.7z"
set "media_packs[55]=samcoupe-media.7z"
set "media_packs[56]=satellaview-media.7z"
set "media_packs[57]=scv-media.7z"
set "media_packs[58]=sega32x-media.7z"
set "media_packs[59]=sg1000-media.7z"
set "media_packs[60]=snes-media.7z"
set "media_packs[61]=solarus-media.7z"
set "media_packs[62]=spectravideo-media.7z"
set "media_packs[63]=sufami-media.7z"
set "media_packs[64]=supergrafx-media.7z"
set "media_packs[65]=supervision-media.7z"
set "media_packs[66]=thomson-media.7z"
set "media_packs[67]=tic80-media.7z"
set "media_packs[68]=trs80coco-media.7z"
set "media_packs[69]=uzebox-media.7z"
set "media_packs[70]=vectrex-media.7z"
set "media_packs[71]=vic20-media.7z"
set "media_packs[72]=videopacplus-media.7z"
set "media_packs[73]=virtualboy-media.7z"
set "media_packs[74]=wasm4-media.7z"
set "media_packs[75]=wswanc-media.7z"
set "media_packs[76]=wswan-media.7z"
set "media_packs[77]=x1-media.7z"
set "media_packs[78]=x68000-media.7z"
set "media_packs[79]=zx81-media.7z"
set "media_packs[80]=zxspectrum-media.7z"

::--------------------------------------------------------------------

::--------------------------------------------------------------------
::DOWNLOAD "MEDIA PACK" + MAX DOWNLOAD ATTEMPTS & RESUME::

:: Display the list of available media packs
echo Choose a media pack to download:
for /L %%i in (1, 1, 77) do (
    echo %%i. !media_packs[%%i]!
)

:: Prompt the user to select a media pack
set /p "choice=Enter the number of the media pack you want to download: "

:: Validate the user's choice
if not defined media_packs[%choice%] (
    echo Invalid choice. Please enter a valid number.
    exit /b 1
)

:: Get the selected media pack name and URL
set "selected_media_pack=!media_packs[%choice%]!"
set "download_url=!base_url!!selected_media_pack!"

:: Extract the console name (e.g., "3do") from the selected media pack name
set "console_name=!selected_media_pack:.7z=!"
set "console_name=!console_name:-media=!"

:: Create a folder with the console name inside the target directory
mkdir "%target_directory%\!console_name!"

:: Download the selected media pack
:: echo Downloading !selected_media_pack!...
:: curl -o "%target_directory%\!selected_media_pack!" "!download_url!"


:: Download the selected media pack with curl
::echo Downloading !selected_media_pack!...
::curl -k -C - -o "%target_directory%\!selected_media_pack!" "!download_url!"


::--------------------------------------------------------------------
::DOWNLOAD LOOP

:: Set the number of maximum download attempts
set max_attempts=4

:: Initialize a variable to keep track of the current attempt
set /a attempt=0

:download_loop
:: Increment the attempt counter
set /a attempt+=1

:: Download the selected media pack with curl
echo Attempt %attempt% to download !selected_media_pack!...
curl -k -C - -o "%target_directory%\!selected_media_pack!" "!download_url!"

:: Check if the download was successful (0 indicates success)
if %errorlevel% equ 0 (
    echo Download of !selected_media_pack! was successful.
    goto :download_completed
) else (
    echo Download of !selected_media_pack! failed on attempt %attempt%.
    if %attempt% lss %max_attempts% (
        echo Retrying in 5 seconds...
        timeout /t 5
        goto :download_loop
    ) else (
        echo Maximum download attempts reached. Download failed.
        goto :download_failed
    )
)

:download_completed
echo Download completed.
goto :end

:download_failed
echo Download failed.
goto :end

:end

::--------------------------------------------------------------------

::--------------------------------------------------------------------
::CHECK MD5 CHECKSUM::

echo Downloaded file: !selected_media_pack!
set "expected_md5="
if "!selected_media_pack!"=="64dd-media.7z" set "expected_md5=a2e36d62227447a9217b4a2b2c6bdef2"
if "!selected_media_pack!"=="amiga600-media.7z" set "expected_md5=864c64b15e80ee992bf011894b5e5980"
if "!selected_media_pack!"=="amiga1200-media.7z" set "expected_md5=35444479df16c4bad8476ce5e5fd2e76"
if "!selected_media_pack!"=="amstradcpc-media.7z" set "expected_md5=211e304e1396e99c487f566ff5acd4ee"
if "!selected_media_pack!"=="apple2gs-media.7z" set "expected_md5=74e8e5669f2923e4bcbdac2753cd3434"
if "!selected_media_pack!"=="apple2-media.7z" set "expected_md5=eb831f572b4e10c99357eb5a089fb09e"
if "!selected_media_pack!"=="arduboy-media.7z" set "expected_md5=2ca7fe373cadf5fa8dc6311ffe2d0bf2"
if "!selected_media_pack!"=="atari800-media.7z" set "expected_md5=50aa147f426464580bd9fb003f408ade"
if "!selected_media_pack!"=="atari2600-media.7z" set "expected_md5=fa453d942a8b94e88e520443ed67b08b"
if "!selected_media_pack!"=="atari5200-media.7z" set "expected_md5=b80a40f28375415977fa0a0fe1e79d3a"
if "!selected_media_pack!"=="atari7800-media.7z" set "expected_md5=166ae4335e4d8a4c26660b32c8b8235e"
if "!selected_media_pack!"=="atarist-media.7z" set "expected_md5=be3e23d1417aac6198f7f1b9b90f318e"
if "!selected_media_pack!"=="atomiswave-media.7z" set "expected_md5=5cdfe5e3efb05accc30c9d36726ca454"
if "!selected_media_pack!"=="bbcmicro-media.7z" set "expected_md5=294dc037877a08d5bb781f6ab3822070"
if "!selected_media_pack!"=="bk-media.7z" set "expected_md5=7302244a58842e2548eff3a3d9e53fab"
if "!selected_media_pack!"=="c64-media.7z" set "expected_md5=ad8ac05290a3b94df8f047d9904ff16e"
if "!selected_media_pack!"=="channelf-media.7z" set "expected_md5=ef1613ee3fe43b40ea481d40b0c06e68"
if "!selected_media_pack!"=="colecovision-media.7z" set "expected_md5=5409c95725191751c1c8912f0765816d"
if "!selected_media_pack!"=="daphne-media.7z" set "expected_md5=a515e01e9f1b756bb813f9be023786a7"
if "!selected_media_pack!"=="dos-media.7z" set "expected_md5=1b9c50565666b71277e325675a95d99e"
if "!selected_media_pack!"=="fds-media.7z" set "expected_md5=cca31f6c53186afe9940640252b58820"
if "!selected_media_pack!"=="gamegear-media.7z" set "expected_md5=f8507f38545df1dca632ee9edf680ce1"
if "!selected_media_pack!"=="gba-media.7z" set "expected_md5=02d9c5cedb63a44e8ba5a68d45292961"
if "!selected_media_pack!"=="gbc-media.7z" set "expected_md5=4591390a77ba3203bad17da641809eea"
if "!selected_media_pack!"=="gb-media.7z" set "expected_md5=8f12081ee4b74e7973b3d461086c32b8"
if "!selected_media_pack!"=="gw-media.7z" set "expected_md5=50e7395253d9276c94d39df57b8ab249"
if "!selected_media_pack!"=="gx4000-media.7z" set "expected_md5=db97c08c5670ebe0b6915bc357954dd7"
if "!selected_media_pack!"=="intellivision-media.7z" set "expected_md5=b29a85e56917bf24ddc167182d3f5bc3"
if "!selected_media_pack!"=="jaguar-media.7z" set "expected_md5=0788dc617baa475fb57323aa4a1d44d8"
if "!selected_media_pack!"=="lowresnx-media.7z" set "expected_md5=41d147eb86660756145ea6ee87a27c3d"
if "!selected_media_pack!"=="lutro-media.7z" set "expected_md5=69cb7245a230ccdbe80421bdb13f09ef"
if "!selected_media_pack!"=="mastersystem-media.7z" set "expected_md5=21d6cb6a4225e615dfa0da6785046b75"
if "!selected_media_pack!"=="megadrive-media.7z" set "expected_md5=05468e87ec889a28a68a67babc26532a"
if "!selected_media_pack!"=="model3-media.7z" set "expected_md5=d30a63408a27b165ab70c70df01c9a1d"
if "!selected_media_pack!"=="msx1-media.7z" set "expected_md5=01a11257ad67bdbca73f7ccae1087d0d"
if "!selected_media_pack!"=="msx2-media.7z" set "expected_md5=21448c7315a44892e670914644397812"
if "!selected_media_pack!"=="msxturbor-media.7z" set "expected_md5=f34fddcf7fa097795482ee2678349d78"
if "!selected_media_pack!"=="multivision-media.7z" set "expected_md5=6acd96d673b1efad6e868516c3a053fb"
if "!selected_media_pack!"=="n64-media.7z" set "expected_md5=4dc383561d084f99ee8cd27642d7a6ba"
if "!selected_media_pack!"=="naomigd-media.7z" set "expected_md5=2768016cedca059c408a360775526d75"
if "!selected_media_pack!"=="naomi-media.7z" set "expected_md5=29e5705b7cb55a4335163f319f5f9053"
if "!selected_media_pack!"=="neogeocd-media.7z" set "expected_md5=489f65bafcc76720e126b8ddaa79fdc9"
if "!selected_media_pack!"=="neogeo-media.7z" set "expected_md5=a3675db62149016f45840481c8b4654e"
if "!selected_media_pack!"=="nes-media.7z" set "expected_md5=0983d81b024187b0c3f9cbcf8e0d62ef"
if "!selected_media_pack!"=="ngpc-media.7z" set "expected_md5=adcae5943a396093a5386c847c527145"
if "!selected_media_pack!"=="ngp-media.7z" set "expected_md5=07e94103b433777cb80b2b26ce2cd32c"
if "!selected_media_pack!"=="o2em-media.7z" set "expected_md5=3c794679c66e54088bfa30d016580078"
if "!selected_media_pack!"=="oricatmos-media.7z" set "expected_md5=c7609eb24a1ab1ef4061390fbdc7dbaf"
if "!selected_media_pack!"=="pcengine-media.7z" set "expected_md5=557e7c8d678db5306049a9f77db7505b"
if "!selected_media_pack!"=="pcenginecd-media.7z" set "expected_md5=d48c2cda02f34882214746bd2a520258"
if "!selected_media_pack!"=="pcfx-media.7z" set "expected_md5=e68086f8439bf3b19c0ea22c925a535e"
if "!selected_media_pack!"=="pcv2-media.7z" set "expected_md5=4748db2648ffc134f2775d3c6a0bbea8"
if "!selected_media_pack!"=="pokemini-media.7z" set "expected_md5=8b2eb047b5f9d9bc991c260a7f53aec4"
if "!selected_media_pack!"=="ports-media.7z" set "expected_md5=b388c84f0c7d9cb5e529c758bc8d5dcd"
if "!selected_media_pack!"=="samcoupe-media.7z" set "expected_md5=b9b873d2178987f139a3284e66de458f"
if "!selected_media_pack!"=="satellaview-media.7z" set "expected_md5=75fbba3c1a16f26ee8c22b0d4a5db363"
if "!selected_media_pack!"=="scv-media.7z" set "expected_md5=b32ba0f51cba58b1505d10f4e085db63"
if "!selected_media_pack!"=="sega32x-media.7z" set "expected_md5=3d06ba89a1fc1301b00b2aae14178975"
if "!selected_media_pack!"=="sg1000-media.7z" set "expected_md5=29968ebb163796abf635667a69c606bf"
if "!selected_media_pack!"=="snes-media.7z" set "expected_md5=a49c05f6601f6d74901c77afa228bc87"
if "!selected_media_pack!"=="solarus-media.7z" set "expected_md5=ef72a08ce0ce14cf47e8a907a1fe6a0f"
if "!selected_media_pack!"=="spectravideo-media.7z" set "expected_md5=7daef6d8807811b5f2ae482ec227e1c0"
if "!selected_media_pack!"=="sufami-media.7z" set "expected_md5=4df212b924b467b30812348f01a4b71b"
if "!selected_media_pack!"=="supergrafx-media.7z" set "expected_md5=466b87c835852d0545905d89f2b7d922"
if "!selected_media_pack!"=="supervision-media.7z" set "expected_md5=9961c3dcad91387b39ea6909e4658010"
if "!selected_media_pack!"=="thomson-media.7z" set "expected_md5=2054a9d8c102926364056af4de3414d2"
if "!selected_media_pack!"=="tic80-media.7z" set "expected_md5=089a5e636561d3683760e606cd22c512"
if "!selected_media_pack!"=="trs80coco-media.7z" set "expected_md5=f658209dd1fc8b1976f2033317eabf07"
if "!selected_media_pack!"=="uzebox-media.7z" set "expected_md5=24f987cd885297b5591b936e7475bf2a"
if "!selected_media_pack!"=="vectrex-media.7z" set "expected_md5=86b466983295c90a69da59eb415b5867"
if "!selected_media_pack!"=="vic20-media.7z" set "expected_md5=03dce302b66f04343b9e7819a1ded8b4"
if "!selected_media_pack!"=="videopacplus-media.7z" set "expected_md5=9662df65f41d8fac6f246f38dfe49db7"
if "!selected_media_pack!"=="virtualboy-media.7z" set "expected_md5=1605f05f73cb142715ee25dbe504773f"
if "!selected_media_pack!"=="wasm4-media.7z" set "expected_md5=3543bee3bc2bc692044b29560333ca31"
if "!selected_media_pack!"=="wswanc-media.7z" set "expected_md5=5c317009d4cdda494bd67ee68a5a9014"
if "!selected_media_pack!"=="wswan-media.7z" set "expected_md5=6f18cc6a4cec027e8a0908e0e25d45a1"
if "!selected_media_pack!"=="x1-media.7z" set "expected_md5=0fc04dc8aa141bd4d70b25b4dfc83030"
if "!selected_media_pack!"=="x68000-media.7z" set "expected_md5=6ebf2a0fdc1be37f74bfce03067326d5"
if "!selected_media_pack!"=="zx81-media.7z" set "expected_md5=c4f23cc445c898de892ed2782d15677c"
if "!selected_media_pack!"=="zxspectrum-media.7z" set "expected_md5=e89800571eb212fa297260c691d4651d"


:: Retrieve the expected MD5 checksum from the media_packs array
set "expected_md5=!media_packs[%selected_media_pack%]!"

if "!expected_md5!" neq "!actual_md5!" (
    echo Checksum verification failed for !selected_media_pack!. Exiting...
    exit /b 1
) else (
    echo Checksum verification successful for !selected_media_pack!.
)

:: Continue with the script if the checksum matches
::--------------------------------------------------------------------


::--------------------------------------------------------------------
::EXTRACTION AND XCOPY TO NETWORK SHARE::

echo Extracting archive: "%target_directory%\!selected_media_pack!"
"C:\Program Files\7-Zip\7z.exe" x -o"%target_directory%\!console_name!" "%target_directory%\!selected_media_pack!"

:: Determine the target directory on the network share
set "target_directory_network=\\RECALBOX\share\roms\!console_name!"

:: Check the exit code of 7z (0 indicates success)
if %errorlevel% equ 0 (

:: Copy the extracted folder and its contents to the network share
xcopy /Y /I /H /Q /E "%target_directory%\!console_name!\*" "%target_directory_network%\"

echo !selected_media_pack! media pack copied to %target_directory_network%

echo Download and copy completed.


::--------------------------------------------------------------------
:: CLEAN UP TEMP FILES::

echo Deleting temporary files and folders...
rd /s /q "%target_directory%"
del /q "%target_directory%\*.*"
) else (
echo Extraction failed. Temporary files are not deleted.
)
::--------------------------------------------------------------------

::--------------------------------------------------------------------
::END MESSAGE::
echo.
echo Enjoy your Readycade!
echo Press any key to exit.

rem Author: Michael Cabral
::--------------------------------------------------------------------

::--------------------------------------------------------------------
::END MESSAGE WITH COUNTDOWN::

rem Wait for 10 seconds and display a countdown message
for /l %%A in (10,-1,1) do (
    cls
    echo Thank you for choosing Readycade!
    echo.
    echo Installation Complete!
    echo Please run the scraper to complete the media installation process per console/system.
    echo See your user manual or the website for instructions.
    echo.
    echo Exiting script automatically in %%A seconds...
    timeout /t 1 >nul
)

exit /b


endlocal