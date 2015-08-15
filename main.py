__author__ = 'OlaPsema'


import binascii
import hexdump
import struct


CR = ({0: 0}, {0: 0}, {0: 0, 1: 0, 2: 4, 3: 8}, {0: 0, 1: 1, 2: 2, 3: 0xFFFF})


class Core(object):
    def __init__(self, code, memory, diction):
        self.R = [0] * 16
        for i in range(4, len(self.R)):
            self.R[i] = 0xcdcd
            # print(self.R[15])
        self.code = code
        self.memory = memory
        self.dict = diction

    # payload
    def mov(self, word):
        src = (word & 0x0f00) >> 8
        adst = (word & 0x0080) >> 7
        bw = (word & 0x0040) >> 6
        asrc = (word & 0x0030) >> 4
        dst = word & 0x000f
        result = 0
        print('mov')
        print(word)
        if asrc == 3:
            if src == 0:  # !!WARNING mov @R0+, RI!!
                self.R[0] += 2
                sword = self.memory.read_word(self.R[0])
                print(sword)
                result = sword
            elif src not in (2, 3):
                result = self.memory.read_word(self.R[src])
                self.R[src] += 2
            else:
                result = CR[src][asrc]

        if asrc == 2:
            if src in {2, 3}:
                result = CR[src][asrc]
            elif src == 0:
                result = self.memory.read_word(self.R[0] + 2)
            else:
                print("!!!!!")
                print(self.R[4])
                result = self.memory.read_word(self.R[src])
                print(result)
        if asrc == 1:
            if src == 3:
                result = CR[src][asrc]
            elif src == 2:
                self.R[0] += 2
                sword = self.memory.read_word(self.R[0])
                result = self.memory.read_word(sword)
            else:
                self.R[0] += 2
                sword = self.memory.read_word(self.R[0])
                print("sword")
                print(sword)
                print((self.R[src] + sword) & 0x0ffff)
                result = self.memory.read_word((self.R[src] + sword) & 0x0ffff)
        if asrc == 0:
            if src == 3:
                result = 0
            elif src == 0:
                result = self.R[0] + 2
                # возможно и не плюс 2, нужно смотреть дальше
            else:
                result = self.R[src]

        if adst == 1:
            # self.R[0] += 2
            dword = self.memory.read_word(self.R[0] + 2)
            if dst == 2:  # mov #N, &addr -> 3 byte length
                dst = dword
            if dst not in (2, 3):  # mov #N, addr or mov #N, M(RI)
                dst = (self.R[dst] + dword) & 0x0ffff
            self.memory.write_word(dst, result)
            self.R[0] += 4

            print(dword)
            hexdump.hexdump(memory.dump())
            return 0

        if adst == 0:  # mov #N, RI
            self.R[dst] = result

            hexdump.hexdump(memory.dump())
            print(self.R[4])
            print(self.R[8])
            # print(self.R[5])
            # read next word
        # self.R[dst] = result #
        return 0

    def add(self, word):
        pass

    def addc(self, word):
        pass

    def subc(self, word):
        pass

    def sub(self, word):
        pass

    def cmp(self, word):
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

    def jmp(self, word):
        print(self.R[0])
        offset = (word & 0x03ff)
        self.R[0] += (2 + offset * 2) & 0x3ff
        print(self.R[0])
        pass

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
        print(word)
        self.R[4] = 0x110a
        self.memory.write_word(self.R[0], 0x3fff)
        self.memory.write_word(self.R[0] + 2, 0xfff2)
        self.memory.write_word(self.R[0] + 4, 0x007)
        command = self.memory.read_word(self.R[0])
        opcode = self.getopcode(command)
        print(command)
        self.dict[opcode](self, command)


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
        # print(data)

        data = binascii.unhexlify(data)

        # print(data)
    return data

# print(core.R)
code = read_memory('memory.bin')
memory = Memory(code, [
    Segment('sfr', 0x0000, 0x0200, Segment.READ_MODE | Segment.WRITE_MODE),
    Segment('ram', 0x0200, 0x0A00, Segment.READ_MODE | Segment.WRITE_MODE),
    Segment('info', 0x1000, 0x1100, Segment.READ_MODE | Segment.WRITE_MODE),
    Segment('flash', 0x1100, 0x10000, Segment.READ_MODE | Segment.WRITE_MODE),
])
# functions instead
core = Core(code, memory, {
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
})
# memory.write_word(0x1200, 0xAA55)
# print memory.read_word(0x1200) == 0xAA55


hexdump.hexdump(memory.dump()[0x110C:0x110F])
core.run(memory.read_word(0xfffe))

# sfr = Memory(core.code[0:16*32], "sfr")
# ram = Memory(core.code[16*32:16*128], "ram")
# print(ram)
# info = Memory(core.code[0:16*32], "info")
#flash = Memory(core.code[0:16*32], "flash")