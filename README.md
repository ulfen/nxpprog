# Programmer for NXP arm processors using ISP protocol.

For help run the command with no arguments:

    ./nxpprog.py

### Help menu

```
nxpprog.py <serial device> <image_file> : program image file to processor.
nxpprog.py --udp <ip address> <image_file> : program processor using Ethernet.
nxpprog.py --start=<addr> <serial device> : start the device at <addr>.
nxpprog.py --read=<file> --addr=<address> --len=<length> <serial device>:
            read length bytes from address and dump them to a file.
nxpprog.py --serialnumber <serial device> : get the device serial number
nxpprog.py --list : list supported processors.
options:
    --cpu=<cpu> : set the cpu type.
    --oscfreq=<freq> : set the oscillator frequency.
    --baud=<baud> : set the baud rate.
    --xonxoff : enable xonxoff flow control.
    --control : use RTS and DTR to control reset and int0.
    --addr=<image start address> : set the base address for the image.
    --verify : read the device after programming.
    --verifyonly : don't program, just verify.
    --eraseonly : don't program, just erase. Implies --eraseall.
    --eraseall : erase all flash not just the area written to.
    --blankcheck : don't program, just check that the flash is blank.
    --filetype=[ihex|bin] : set filetype to intel hex format or raw binary.
    --bank=[0|1] : select bank for devices with flash banks.
    --port=<udp port> : UDP port number to use (default 41825).
    --mac=<mac address> : MAC address to associate IP address with.
```

### Program image file to processor

    ./nxpprog.py <serial device> <image_file.bin>

The image start address defaults to 0.
When the image start address is 0 a checksum is inserted in the reserved
interrupt vector so that the bootloader will boot the image.
The image file is a raw binary file (output from objcopy -O binary).
