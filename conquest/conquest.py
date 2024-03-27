# Parses out text from .dat files and outputs txt files.
# Usage: python conquest.py <filename>

import sys

def pokemon_dat():
    with open('Pokemon.dat', 'rb') as file:
        data = file.read()
        
        output = ''
        for i in range(0x0, 0x2580, 0x30):
            s = data[i:i+11]
            s = s[:s.find(b'\x00')]
            s = s.decode('shift_jisx0213')
            output += str(i // 0x30) + '\t' + s + '\n'
        
        with open('Pokemon.txt', 'w', encoding='utf-8') as out:
            out.write(output)

def skill_dat():
    with open('Skill.dat', 'rb') as file:
        data = file.read()
        
        output = ''
        for i in range(0x0, len(data), 20):
            s = data[i:i+20]
            s = s[:s.find(b'\x00')]
            # print(s.decode('shift_jisx0213'))
            s = s.decode('shift_jisx0213')
            output += str(i // 20) + '\t' + s + '\n'
        
        with open('Skill.txt', 'w', encoding='utf-8') as out:
            out.write(output)
            
def BaseBushou_dat():
    with open('BaseBushou.dat', 'rb') as file:
        data = file.read()
        
        d = {}
        special = {
            'ю': 'ō',
            'п': 'ū',
        }
        for i in range(0x13B0, len(data), 12):
            s = data[i:i+12]
            s = s[:s.find(b'\x00')]
            # print(s.decode('shift_jisx0213'))
            s = s.decode('shift_jisx0213')
            for a, b in special.items():
                s = s.replace(a, b)
            d[(i - 0x13B0) // 12] = s
            
        output = ''
        for i in range(252):
            index = (data[i * 20 + 3] * 256 + data[i * 20 + 2] >> 1) & 0xFF
            output += str(i) + '\t' + str(index) + '\t' + d[index] + '\n'
        
        with open('BaseBushou.txt', 'w', encoding='utf-8') as out:
            out.write(output)

def gimmick_dat_en():
    with open('Gimmick.dat', 'rb') as file:
        data = file.read()
        
        output = ''
        for i in range(0x0, len(data), 40):
            s = data[i:i+16]
            s = s[:s.find(b'\x00')]
            # print(s.decode('shift_jisx0213'))
            s = s.decode('shift_jisx0213').replace('ﾊ', 'é')
            output += str(i // 40) + '\t' + s + '\n'
        
        with open('Gimmick.txt', 'w', encoding='utf-8') as out:
            out.write(output)
            
def gimmick_dat_ja():
    with open('Gimmick.dat', 'rb') as file:
        data = file.read()
        
        output = ''
        for i in range(0x0, len(data), 36):
            s = data[i:i+15]
            s = s[:s.find(b'\x00')]
            # print(s.decode('shift_jisx0213'))
            s = s.decode('shift_jisx0213')
            output += str(i // 36) + '\t' + s + '\n'
        
        with open('Gimmick.txt', 'w', encoding='utf-8') as out:
            out.write(output)
            
def waza_dat(filename='Waza', namelen=15, recordlen=36):
    with open(filename + '.dat', 'rb') as file:
        data = file.read()
        
        output = ''
        for i in range(0x0, len(data), recordlen):
            s = data[i:i+namelen]
            s = s[:s.find(b'\x00')]
            # print(s.decode('shift_jisx0213'))
            s = s.decode('shift_jisx0213')
            output += str(i // recordlen) + '\t' + s + '\n'
        
        with open(filename + '.txt', 'w', encoding='utf-8') as out:
            out.write(output)

def TrSkill_dat():
    filename = 'TrSkill'
    recordlen = 81
    with open(filename + '.dat', 'rb') as file:
        data = file.read()
        
        output = ''
        for i in range(0x0, len(data), recordlen):
            s = data[i:i+0x13]
            s = s[:s.find(b'\x00')].decode('shift_jisx0213')
            
            s2 = data[i+0x13:i+80]
            s2 = s2[:s2.find(b'\x00')].decode('shift_jisx0213')
            
            output += str(i // recordlen) + '\t' + s + '\t' + s2 + '\n'
        
        with open(filename + '.txt', 'w', encoding='utf-8') as out:
            out.write(output)

pokemon_dat()
skill_dat()
BaseBushou_dat()
gimmick_dat_en()
waza_dat()
waza_dat('Item', 0x15)
waza_dat('Building', 0x13) # en
# waza_dat('Building', 0x11, 32) # ja
waza_dat('Tokusei', 0x10, 20)
waza_dat('SpAbility', 19, 19)
waza_dat('Trainer', 0x14, 44)
waza_dat('Trainer', 0x14, 44)
waza_dat('Saihai', 0x13, 28) # en
# waza_dat('Saihai', 0xF, 24) # ja
TrSkill_dat()
waza_dat('EventSpeaker', 0x10, 18) # en
# waza_dat('EventSpeaker', 11, 12) # ja
waza_dat('Kuni', 0xB, 24) # en
# waza_dat('Kuni', 9, 20) # ja
waza_dat('Jinkei', 0x10, 28)