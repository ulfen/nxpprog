#!/usr/bin/python
#
# Copyright (c) 2009 Brian Murphy <brian@murphy.dk>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# A simple programmer which works with the ISP protocol on NXP LPC arm
# processors.

import binascii
import sys
import struct
import getopt
import serial # pyserial
import time

import ihex

# flash sector sizes for lpc23xx/lpc24xx/lpc214x processors
flash_sector_lpc23xx = (
                        4, 4, 4, 4, 4, 4, 4, 4,
                        32, 32, 32, 32, 32, 32, 32,
                        32, 32, 32, 32, 32, 32, 32,
                        4, 4, 4, 4, 4, 4
                       )

# flash sector sizes for 64k lpc21xx processors (without bootsector)
flash_sector_lpc21xx_64 = (
                            8, 8, 8, 8, 8, 8, 8, 8
                           )

# flash sector sizes for 128k lpc21xx processors (without bootsector)
flash_sector_lpc21xx_128 = (
                            8, 8, 8, 8, 8, 8, 8, 8,
                            8, 8, 8, 8, 8, 8, 8
                           )

# flash sector sizes for 256k lpc21xx processors (without bootsector)
flash_sector_lpc21xx_256 = (
                            8, 8, 8, 8, 8, 8, 8, 8,
                            64, 64,
                            8, 8, 8, 8, 8, 8, 8,
                           )

# flash sector sizes for lpc17xx processors
flash_sector_lpc17xx = (
                        4, 4, 4, 4, 4, 4, 4, 4,
                        4, 4, 4, 4, 4, 4, 4, 4,
                        32, 32, 32, 32, 32, 32, 32,
                        32, 32, 32, 32, 32, 32, 32,
                       )


flash_prog_buffer_base_default = 0x40001000
flash_prog_buffer_size_default = 4096
   
# cpu parameter table
cpu_parms = {
        # 128k flash
        "lpc2364" : {
            "flash_sector" : flash_sector_lpc23xx,
            "flash_sector_count": 11,
            "devid": 369162498
        },
        # 256k flash
        "lpc2365" : {
            "flash_sector" : flash_sector_lpc23xx,
            "flash_sector_count": 15,
            "devid": 369158179
        },
        "lpc2366" : {
            "flash_sector" : flash_sector_lpc23xx,
            "flash_sector_count": 15,
            "devid": 369162531
        },
        # 512k flash
        "lpc2367" : {
            "flash_sector" : flash_sector_lpc23xx,
            "devid": 369158181
        },
        "lpc2368" : {
            "flash_sector" : flash_sector_lpc23xx,
            "devid": 369162533
        },
        "lpc2377" : {
            "flash_sector" : flash_sector_lpc23xx,
            "devid": 385935397
        },
        "lpc2378" : {
            "flash_sector" : flash_sector_lpc23xx,
            "devid": 385940773
        },
        "lpc2387" : {
            "flash_sector" : flash_sector_lpc23xx,
            "devid": 402716981

        },
        "lpc2388" : {
            "flash_sector" : flash_sector_lpc23xx,
            "devid": 402718517
        },
        # lpc21xx
        # some incomplete info here need at least sector count
        "lpc2141": {
            "devid": 196353,
            "flash_sector": flash_sector_lpc23xx,
            "flash_sector_count": 8,
        },
        "lpc2142": {
            "flash_sector": flash_sector_lpc23xx,
            "flash_sector_count": 9,
            "devid": 196369,
        },
        "lpc2144": {
            "flash_sector": flash_sector_lpc23xx,
            "flash_sector_count": 11,
            "devid": 196370,
        },
        "lpc2146": {
            "flash_sector": flash_sector_lpc23xx,
            "flash_sector_count": 15,
            "devid": 196387,
        },
        "lpc2148": {
            "flash_sector": flash_sector_lpc23xx,
            "flash_sector_count": 27,
            "devid": 196389,
        },
        "lpc2109" : {
            "flash_sector": flash_sector_lpc21xx_64,
            "devid": 33685249
        },
        "lpc2119" : {
            "flash_sector": flash_sector_lpc21xx_128,
            "devid": 33685266
        },
        "lpc2129" : {
            "flash_sector": flash_sector_lpc21xx_256,
            "devid": 33685267
        },
        "lpc2114" : {
            "flash_sector" : flash_sector_lpc21xx_128,
            "devid": 16908050
        },
        "lpc2124" : {
            "flash_sector" : flash_sector_lpc21xx_256,
            "devid": 16908051
        },
        "lpc2194" : {
            "flash_sector" : flash_sector_lpc21xx_256,
            "devid": 50462483
        },
        "lpc2292" : {
            "flash_sector" : flash_sector_lpc21xx_256,
            "devid": 67239699
        },
        "lpc2294" : {
            "flash_sector" : flash_sector_lpc21xx_256,
            "devid": 84016915
        },
        # lpc22xx
        "lpc2212" : {
            "flash_sector" : flash_sector_lpc21xx_128
        },
        "lpc2214" : {
            "flash_sector" : flash_sector_lpc21xx_256
        },
        # lpc24xx
        "lpc2458" : {
            "flash_sector" : flash_sector_lpc23xx,
            "devid": 352386869,
        },
        "lpc2468" : {
            "flash_sector" : flash_sector_lpc23xx,
            "devid": 369164085,
        },
        "lpc2478" : {
            "flash_sector" : flash_sector_lpc23xx,
            "devid": 386006837,
        },
	# lpc17xx
	"lpc1768" : {
	    "flash_sector" : flash_sector_lpc17xx,
	    "flash_prog_buffer_base" : 0x10001000,
	    "devid": 0x26013f37,
	},
	"lpc1766" : {
	    "flash_sector" : flash_sector_lpc17xx,
	    "flash_prog_buffer_base" : 0x10001000,
	    "devid": 0x26013f33,
	},
	"lpc1765" : {
	    "flash_sector" : flash_sector_lpc17xx,
	    "flash_prog_buffer_base" : 0x10001000,
	    "devid": 0x26013733,
	},
	"lpc1764" : {
	    "flash_sector" : flash_sector_lpc17xx,
	    "flash_prog_buffer_base" : 0x10001000,
	    "devid": 0x26011922,
	},
	"lpc1758" : {
	    "flash_sector" : flash_sector_lpc17xx,
	    "flash_prog_buffer_base" : 0x10001000,
	    "devid": 0x26013f34,
	},
	"lpc1756" : {
	    "flash_sector" : flash_sector_lpc17xx,
	    "flash_prog_buffer_base" : 0x10001000,
	    "devid": 0x26011723,
	},
	"lpc1754" : {
	    "flash_sector" : flash_sector_lpc17xx,
	    "flash_prog_buffer_base" : 0x10001000,
	    "devid": 0x26011722,
	},
	"lpc1752" : {
	    "flash_sector" : flash_sector_lpc17xx,
	    "flash_prog_buffer_base" : 0x10001000,
	    "devid": 0x26001121,
	},
	"lpc1751" : {
	    "flash_sector" : flash_sector_lpc17xx,
	    "flash_prog_buffer_base" : 0x10001000,
	    "devid": 0x26001110,
	},
}


def log(str):
    sys.stderr.write("%s\n" % str)


def panic(str):
    log(str)
    sys.exit(1)


def syntax():
    panic(
"""%s <serial device> <image_file> : program image file to processor.
%s --eraseonly <serial device> : erase the device's flash.
%s --start=<addr> <serial device> : start the device at <addr>
%s --list : list supported processors.
options:
    --cpu=<cpu> : set the cpu type.
    --oscfreq=<freq> : set the oscillator frequency.
    --baud=<baud> : set the baud rate.
    --xonxoff : enable xonxoff flow control.
    --control : use RTS and DTR to control reset and int0.
    --addr=<image start address> : set the base address for the image.
    --eraseonly : don't program, just erase. Implies --eraseall.
    --eraseall : erase all flash not just the area written to.
    --filetype=[ihex|bin]: set filetype to intel hex format or raw binary
           """ % (sys.argv[0], sys.argv[0], sys.argv[0], sys.argv[0]))


class nxpprog:
    def __init__(self, cpu, device, baud, osc_freq, xonxoff = 0, control = 0):
        self.echo_on = 1
        self.OK = "OK\r\n"
        self.RESEND = "RESEND\r\n"
        self.sync_str = 'Synchronized'

        # for calculations in 32 bit modulo arithmetic
        self.U32_MOD = (2 ** 32)

        # uuencoded line length
        self.uu_line_size = 45
        # uuencoded block length
        self.uu_block_size = self.uu_line_size * 20

        self.serdev = serial.Serial(device, baud)

        # set a two second timeout just in case there is nothing connected
        # or the device is in the wrong mode.
        # This timeout is too short for slow baud rates but who wants to
        # use them?
        self.serdev.setTimeout(5)
        # device wants Xon Xoff flow control
        if xonxoff:
            self.serdev.setXonXoff(1)

        self.cpu = cpu
        
        # reset pin is controlled by DTR implying int0 is controlled by RTS
        self.reset_pin = "dtr"

        if control:
            self.isp_mode()

        self.serdev.flushInput()

        self.connection_init(osc_freq)

    # put the chip in isp mode by resetting it using RTS and DTR signals
    # this is of course only possible if the signals are connected in
    # this way
    def isp_mode(self):
        self.reset(0)
        time.sleep(.1)
        self.reset(1)
        self.int0(1)
        time.sleep(.1)
        self.reset(0)
        time.sleep(.1)
        self.int0(0)

    def reset(self, level):
        if self.reset_pin == "rts":
            self.serdev.setRTS(level)
        else:
            self.serdev.setDTR(level)

    def int0(self, level):
        # if reset pin is rts int0 pin is dtr
        if self.reset_pin == "rts":
            self.serdev.setDTR(level)
        else:
            self.serdev.setRTS(level)

    def connection_init(self, osc_freq):
        self.sync(osc_freq)

        if self.cpu == "autodetect":
            devid = self.get_devid()
            for dcpu in cpu_parms.keys():
                cpu_devid = cpu_parms[dcpu].get("devid")
                if not cpu_devid:
                    continue
                if devid == cpu_devid:
                    log("detected %s" % dcpu)
                    self.cpu = dcpu
                    break
            if self.cpu == "autodetect":
                panic("Cannot autodetect from device id %d, set cpu name manually" % devid)

        # unlock write commands
        self.isp_command("U 23130")


    def dev_write(self, data):
        self.serdev.write(data)

    def dev_readline(self):
        return self.serdev.readline()

    # something suspicious here in tty setup - these should be the same
    def str_in(self, str):
        return "%s\r\n" % str

    def str_out(self, str):
        return "%s\n" % str

    def errexit(self, str, status):
        if not status:
            panic("%s: timeout" % str)
        err = int(status)
        if err != 0:
            panic("%s: %d" % (str, err))


    def isp_command(self, cmd):
        self.dev_write("%s\n" % cmd)

        # throw away echo data
        if self.echo_on:
            self.dev_readline()

        status = self.dev_readline()
        self.errexit("'%s' error" % cmd, status)


    def sync(self, osc):
        self.dev_write("?")
        s = self.dev_readline()
        if not s:
            panic("sync timeout")
        if s != self.str_in(self.sync_str):
            panic("no sync string")

        self.dev_write(self.str_out(self.sync_str))
        # recieve our echoed data
        s = self.dev_readline()
        if s != self.str_out(self.sync_str):
            panic("no sync string")

        s = self.dev_readline()
        if s != self.OK:
            panic("not ok")

        self.dev_write("%d\n" % osc)
        # discard echo
        s = self.dev_readline()
        s = self.dev_readline()
        if s != self.OK:
            panic("osc not ok")

        self.dev_write("A 0\n")
        # discard echo
        s = self.dev_readline()
        s = self.dev_readline()
        if int(s):
            panic("echo disable failed")

        self.echo_on = 0


    def sum(self, str):
        s = 0
        for i in str:
            s += ord(i)
        return s


    def write_ram_block(self, addr, data):
        data_len = len(data)

        self.isp_command("W %d %d\n" % ( addr, data_len ))

        for i in range(0, data_len, self.uu_line_size):
            c_line_size = data_len - i
            if c_line_size > self.uu_line_size:
                c_line_size = self.uu_line_size
            block = data[i:i+c_line_size]
            bstr = binascii.b2a_uu(block)
            self.dev_write(bstr)


        self.dev_write("%s\n" % self.sum(data))
        status = self.dev_readline()
        if not status:
            return "timeout"
        if status == self.RESEND:
            return "resend"
        if status == self.OK:
            return ""
        
        # unknown status result
        panic(status)


    def write_ram_data(self, addr, data):
        image_len = len(data)
        for i in range(0, image_len, self.uu_block_size):

            a_block_size = image_len - i
            if a_block_size > self.uu_block_size:
                a_block_size = self.uu_block_size

            err = self.write_ram_block(addr, data[i : i + a_block_size])
            if err:
                panic("write error: %s" % err)

            addr += a_block_size


    def find_flash_sector(self, addr):
        table = self.get_cpu_parm("flash_sector")
        faddr = 0
        for i in range(0, len(table)):
            n_faddr = faddr + table[i] * 1024
            if addr >= faddr and addr < n_faddr:
                return i
            faddr = n_faddr
        return -1


    def bytestr(self, ch, count):
        str = ''
        for i in range(0, count):
            str += ch
        return str


    def insert_csum(self, orig_image):
        # make this a valid image by inserting a checksum in the correct place
        intvecs = struct.unpack("<8I", orig_image[0:32])

        valid_image_csum_vec = 5
        # calculate the checksum over the interrupt vectors
        csum = 0
        intvecs_list = []
        for vec in range(0, len(intvecs)):
            intvecs_list.append(intvecs[vec])
            csum = csum + intvecs[vec]
        # remove the value at the checksum location
        csum -= intvecs[valid_image_csum_vec]

        csum %= self.U32_MOD
        csum = self.U32_MOD - csum

        intvecs_list[valid_image_csum_vec] = csum

        image = ''
        for vecval in intvecs_list:
            image += struct.pack("<I", vecval)

        image += orig_image[32:]

        return image


    def prepare_flash_sectors(self, start_sector, end_sector):
        self.isp_command("P %d %d" % (start_sector, end_sector))


    def erase_sectors(self, start_sector, end_sector):
        self.prepare_flash_sectors(start_sector, end_sector)

        log("erasing flash sectors %d-%d" % (start_sector, end_sector))

        self.isp_command("E %d %d" % (start_sector, end_sector))


    def erase_flash(self, start_addr, end_addr):
        start_sector = self.find_flash_sector(start_addr)
        end_sector = self.find_flash_sector(end_addr)

        self.erase_sectors(start_sector, end_sector)


    def get_cpu_parm(self, key, default = None):
        ccpu_parms = cpu_parms.get(self.cpu)
        if not ccpu_parms:
            panic("no parameters defined for cpu %s" % self.cpu)
        parm = ccpu_parms.get(key)
        if parm:
            return parm
        if default:
            return default
        else:
            panic("no value for required cpu parameter %s" % key)


    def erase_all(self):
        end_sector = self.get_cpu_parm("flash_sector_count",
            len(self.get_cpu_parm("flash_sector"))) - 1

        self.erase_sectors(0, end_sector)


    def prog_image(self, image, flash_addr_base = 0, 
            erase_all = 0):

        # the base address of the ram block to be written to flash
        ram_addr = self.get_cpu_parm("flash_prog_buffer_base",
                flash_prog_buffer_base_default)
        # the size of the ram block to be written to flash
        # 256 | 512 | 1024 | 4096
        ram_block = self.get_cpu_parm("flash_prog_buffer_size",
                flash_prog_buffer_size_default)

        if self.get_cpu_parm("intvec_checksum", 1) and flash_addr_base == 0:
            log("inserting intvec checksum in image")
            image = self.insert_csum(image)

        image_len = len(image)
        # pad to a multiple of ram_block size with 0xff
        pad_count_rem = image_len % ram_block
        if pad_count_rem != 0:
            pad_count = ram_block - pad_count_rem
            image += self.bytestr('\xff', pad_count)
            image_len += pad_count

        log("padding with %d bytes" % pad_count)

        if erase_all:
            self.erase_all()
        else:
            self.erase_flash(flash_addr_base, flash_addr_base + image_len)

        for image_index in range(0, image_len, ram_block):
            a_ram_block = image_len - image_index
            if a_ram_block > ram_block:
                a_ram_block = ram_block

            flash_addr_start = image_index + flash_addr_base
            flash_addr_end = flash_addr_start + a_ram_block

            log("writing %d bytes to %x" % (a_ram_block, flash_addr_start))

            self.write_ram_data(ram_addr,
                    image[flash_addr_start: flash_addr_end])

            s_flash_sector = self.find_flash_sector(flash_addr_start)

            e_flash_sector = self.find_flash_sector(flash_addr_end)

            self.prepare_flash_sectors(s_flash_sector, e_flash_sector)

            # copy ram to flash
            self.isp_command("C %d %d %d" %
                    (flash_addr_start, ram_addr, a_ram_block))


    def start(self, addr = 0, mode = "arm"):
        # start image at address 0
        if mode == "arm":
            m = "A"
        elif mode == "thumb":
            m = "T"
        else:
            panic("invalid mode to start")

        self.isp_command("G %d %s" % (addr, m))


    def get_devid(self):
        self.isp_command("J")
        id = self.dev_readline()
        return int(id)


if __name__ == "__main__":
    # defaults
    osc_freq = 16000 # kHz
    baud = 115200
    cpu = "autodetect"
    flash_addr_base = 0
    erase_all = 0
    erase_only = 0
    xonxoff = 0
    start = 0
    control = 0
    filetype = "bin"

    optlist, args = getopt.getopt(sys.argv[1:], '',
            ['cpu=', 'oscfreq=', 'baud=', 'addr=', 'start=', 'filetype=',
                'xonxoff', 'eraseall', 'eraseonly', 'list', 'control'])

    for o, a in optlist:
        if o == "--list":
            log("Supported cpus:")
            for val in cpu_parms.keys():
                log(" %s" % val)
            sys.exit(0)
        if o == "--cpu":
            cpu = a
        elif o == "--xonxoff":
            xonxoff = 1
        elif o == "--oscfreq":
            osc_freq = int(a)
        elif o == "--addr":
            flash_addr_base = int(a, 0)
        elif o == "--baud":
            baud = int(a)
        elif o == "--eraseall":
            erase_all = 1
        elif o == "--eraseonly":
            erase_only = 1
        elif o == "--control":
            control = 1
        elif o == "--filetype":
            filetype = a
	    if not ( filetype == "bin" or filetype == "ihex" ):
		panic("invalid filetype: %s" % filetype)
        elif o == "--start":
            start = 1
            if a:
                startaddr = a
            else:
                startaddr = 0
        else:
	    panic("unhandled option: %s" % o)

    if cpu != "autodetect" and not cpu_parms.has_key(cpu):
        panic("unsupported cpu %s" % cpu)

    if len(args) == 0:
        syntax()

    log("cpu=%s oscfreq=%d baud=%d" % (cpu, osc_freq, baud))

    device = args[0]

    prog = nxpprog(cpu, device, baud, osc_freq, xonxoff, control)

    if erase_only:
        prog.erase_all()
    elif start:
        prog.start(startaddr)
    else:
        if len(args) != 2:
            syntax()

        filename = args[1]

	if filetype == "ihex":
	    ih = ihex.ihex(filename)
	    (flash_addr_base, image) = ih.flatten()
	else:
            image = open(filename, "rb").read()

        prog.prog_image(image, flash_addr_base, erase_all)

        prog.start()
