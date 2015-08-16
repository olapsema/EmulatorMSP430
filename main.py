__author__ = 'OlaPsema'

import binascii
import hexdump
import struct

CR = ((0), (0), (0, 0, 4, 8), (0, 1, 2, 0xFFFF))


class Core(object):
    def __init__(self, code, memory):
        self.R = [0] * 16
        for i in range(4, len(self.R)):
            self.R[i] = 0xcdcd
            # print(self.R[15])
        self.code = code
        self.memory = memory
        self.caller = {
            4: Core.twooparithm,
            5: Core.twooparithm,

            0x3F: Core.jmp
        }
        self.dict = {
            4: Core.mov,
            5: Core.add,
            6: Core.addc,
            7: Core.subc,
            8: Core.sub,
            9: Core.cmp,
            0xA: Core.dadd,
            0xB: Core.bit,
            0xC: Core.bic,
            0xD: Core.bis,
            0xE: Core.xor,
            0xF: Core.andf,

            0x3F: Core.jmp
        }

    # def getbytes(self, word, start, end):
    #     start -= 1
    #     end -= 1
    #     len = end - start
    #     wordlen = str(word)
    #     #wordlen = len(wordlen)
    #     rmask = 0
    #     count = 0
    #     if len == 0 : return 0
    #     while len!=0:
    #         if (len-4) >= 0:
    #             len -= 4
    #             rmask += (0xF << 4 * count)
    #         elif (len-3) >= 0:
    #             len -= 3
    #             rmask += (0x7 << 4 * count)
    #         elif (len-2) >= 0:
    #             len -= 2
    #             rmask += (0x3 << 4 * count)
    #         elif (len-1) >= 0:
    #             len -= 1
    #             rmask += (0x1 << 4 * count)
    #         count += 1
    #         print(rmask)
    #         j = (word >> (wordlen-end-1))
    #     return (word >> (wordlen-end-1)) & rmask


    def getinstrlength(self, word, src, dst, asrc, adst, bw):
        length = 1
        result = [0, 0, 0]
        if asrc == 1 and src != 3 or asrc == 3 and src == 0:
            length += 1
            result[1] = 1
        if adst == 1:
            length += 1
            result[2] = 1
        result[0] = length
        return result
        # returns list with params (length, hasSourceWord, hasDestinationWord)

    # payload
    def mov(self, result, dst, wtd):
        if wtd == 1:
            self.memory.write_word(dst, result)
        elif wtd == 2:
            self.R[dst] = result

    def add(self, word):
        pass

    def addc(self, word):
        pass

    def subc(self, word):
        pass

    def sub(self, word):
        pass

    def cmp(self, result, dst, wtd):
        pass

    def dadd(self, word):
        pass

    def bit(self, word):
        pass

    def bit(self, word):
        pass

    def bic(self, word):
        pass

    def bis(self, word):
        pass

    def xor(self, word):
        pass

    def andf(self, word):
        pass

    def jmp(self, word, payload):
        print(self.R[0])
        offset = (word & 0x03ff)
        self.R[0] += (2 + offset * 2) & 0x3ff
        print(self.R[0])
        pass

    def twooparithm(self, word, payload):
        src = (word & 0x0f00) >> 8
        adst = (word & 0x0080) >> 7
        bw = (word & 0x0040) >> 6
        asrc = (word & 0x0030) >> 4
        dst = word & 0x000f
        result = 0
        wtd = 0 # 0 -> nothing 1 -> write to memory 2 -> write to register
        instrdescr = self.getinstrlength(word, src, dst, asrc, adst, bw)
        self.R[0] += 2*instrdescr[0]

        if src == 2 and asrc != 1 and asrc != 0 or src == 3:
            result = CR[src][asrc]
        else:
            if asrc == 3:  # mov #N, () src == 0 # mov @RI+, () src != 0
                result = self.memory.read_word(self.R[src]-2*(instrdescr[1]+instrdescr[2])*(src == 0))
                self.R[src] += 2 * (src != 0)
            elif asrc == 2:
                result = self.memory.read_word(self.R[src]-2*(instrdescr[1]+instrdescr[2])*(src == 0))
            elif asrc == 1:
                result = self.memory.read_word((self.R[src]*(src != 2) - 2*(src == 0) + self.memory.read_word(self.R[0]-2*(instrdescr[1]+instrdescr[2]))) & 0x0ffff)
            elif asrc == 0:
                result = self.R[src]

        if adst == 1:
            dst = (self.R[dst]*(dst != 2) - 2*(dst == 0) + self.memory.read_word(self.R[0] - 2*instrdescr[2])) & 0x0ffff
            # self.memory.write_word(dst, result)
            wtd = 1

        elif adst == 0 and dst != 3:
            #dst = self.R[dst]
            wtd = 2
            # self.R[dst] = result
        payload(self, result, dst, wtd)
        return 0

    def getopcode(self, word):
        opcode = (word & 0xf000) >> 12  # mov add cmp etc.
        if opcode in self.dict:
            return opcode
        opcode = ((word & 0xfc00) >> 10) + 0x30
        if opcode in self.dict:
            return opcode
        raise SystemError('Wrong opcode found')

    def run(self, word):
        self.R[0] = word
        # while True:
        # print(word)
        # self.R[15] = 0x110a
        # self.memory.write_word(self.R[0], 0x4f05)
        # self.memory.write_word(self.R[0] + 2, 0xfff2)
        # self.memory.write_word(self.R[0] + 4, 0x007)
        for i in range(200):
            command = self.memory.read_word(self.R[0])
            opcode = self.getopcode(command)
            print(command)
            self.caller[opcode](self, command, self.dict[opcode])
            #self.dict[opcode](self, command)
        hexdump.hexdump(memory.dump())
        for i in range(16): print("R["+str(i)+"]= "+str(self.R[i]))


class IMemory(object):
    def read_byte(self, addr):
        raise NotImplementedError

    def read_word(self, addr):
        raise NotImplementedError

    def write_byte(self, addr, value):
        raise NotImplementedError

    def write_word(self, addr, value):
        raise NotImplementedError


class Segment(IMemory):
    READ_MODE = 1
    WRITE_MODE = 2

    def __init__(self, name, start, end, mode=READ_MODE):
        self.name = name
        self.start = start
        self.end = end
        self.mode = mode
        self.data = None

    def update(self, data):
        self.data = bytearray(data[self.start:self.end])

    # '\xFF' -> int_dec(\xFF)
    def read_byte(self, addr):
        if self.mode & Segment.READ_MODE:
            addr -= self.start
            # return struct.unpack('1b', self.data[addr - self.start])
            return self.data[addr]
        else:
            raise SystemError("Can't read from segment")

    # '\xFF\xFF' -> int_dec(\xFF\xFF)
    def read_word(self, addr):
        # return struct.unpack('<1H', str(self.data[addr - self.start:addr - self.start + 2]))
        if self.mode & Segment.READ_MODE:
            addr -= self.start
            return (self.data[addr + 1] << 8) | self.data[addr]
        else:
            raise SystemError("Can't read from segment")

    # int -> '\xFF'
    def write_byte(self, addr, value):
        if self.mode & Segment.WRITE_MODE:
            addr -= self.start
            self.data[addr] = value
        else:
            raise SystemError("Can't write to segment")

    def write_word(self, addr, value):
        if self.mode & Segment.WRITE_MODE:
            addr -= self.start
            print('write')
            print((value >> 8) & 0x00FF)
            print(value & 0x00FF)
            print(addr)
            self.data[addr + 1] = (value >> 8) & 0x00FF
            self.data[addr] = value & 0x00FF
        else:
            raise SystemError("Can't write to segment")


class Memory(IMemory):
    def __init__(self, data, layout):
        self.layout = layout
        for segment in self.layout:
            segment.update(data)

    def select_segment(self, addr):
        """
        :rtype: Segment
        """
        segment = list(filter(lambda segment: segment.start <= addr < segment.end, self.layout))
        if len(segment) == 1:
            return segment[0]
        raise KeyError("ambiguous segment for specified address")

    def read_byte(self, addr):
        return self.select_segment(addr).read_byte(addr)

    def read_word(self, addr):
        return self.select_segment(addr).read_word(addr)

    def write_byte(self, addr, value):
        self.select_segment(addr).write_byte(addr, value)

    def write_word(self, addr, value):
        self.select_segment(addr).write_word(addr, value)

    def dump(self):
        result = bytearray(b'\x00' * 0x10000)
        for segment in self.layout:
            result[segment.start:segment.end] = segment.data
        return result


def read_memory(path):
    with open(path, 'r') as f:
        data = f.read()
        data = ''.join(data.splitlines()[1:-1]).replace(' ', '')
        data = binascii.unhexlify(data)
    return data


# print(core.R)
code = read_memory('memoryTest3.bin')
memory = Memory(code, [
    Segment('sfr', 0x0000, 0x0200, Segment.READ_MODE | Segment.WRITE_MODE),
    Segment('ram', 0x0200, 0x0A00, Segment.READ_MODE | Segment.WRITE_MODE),
    Segment('undefined', 0x0A00, 0x1000, Segment.READ_MODE | Segment.WRITE_MODE),
    Segment('info', 0x1000, 0x1100, Segment.READ_MODE | Segment.WRITE_MODE),
    Segment('flash', 0x1100, 0x10000, Segment.READ_MODE | Segment.WRITE_MODE),
])
# functions instead
core = Core(code, memory)
# memory.write_word(0x1200, 0xAA55)
# print memory.read_word(0x1200) == 0xAA55


hexdump.hexdump(memory.dump()[0x110C:0x110F])
core.run(memory.read_word(0xfffe))

# sfr = Memory(core.code[0:16*32], "sfr")
# ram = Memory(core.code[16*32:16*128], "ram")
# print(ram)
# info = Memory(core.code[0:16*32], "info")
# flash = Memory(core.code[0:16*32], "flash")
