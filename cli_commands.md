
# flash esp32
## erase old flash
esptool --port COM4 erase_flash 

## flash new version of micropython
esptool --chip esp32 --port COM4 --baud 460800 write_flash -z 0x1000 C:\Users\Pc\Coding\ESP32\varioproject\esp32_flash.bin

# upload files from \vario\ via script
python upload_to_esp32.py

# mpremote
## list files
mpremote connect COM4 fs ls     

## copy file
mpremote connect COM4 cp boot.py :   

## copy all files from current dir
mpremote connect COM4 fs cp -r . :   