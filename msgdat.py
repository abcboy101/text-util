# Parses a MSG.DAT file and outputs txt files.
# Usage: python msgdat.py <filename>

import sys
import os
from itertools import chain
import re

RAW_OUT = False

def read_val(data, index, length=4):
    return int.from_bytes(data[index:index+length], byteorder='little', signed=False)


def decrypt(data):
    data = list(data)
    key = b"MsgLinker Ver1.00"
    
    for i in range(len(data)):
        data[i] = data[i] ^ key[i % len(key)]
    
    return bytes(data)
    

def process_string(string):
    # string = string[0:string.find(b'\x05\x05\x05')]
    # string = string.replace(b'{', b'\\{').replace(b'}', b'\\}').replace(b'[', b'\\[').replace(b']', b'\\]')
    string = string.decode('shift_jisx0213').replace('¥', '\\')
    
    # print(string)
    
    string = string.replace('\\', '\\\\').replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')
    for j in chain(range(0x00, 0x20)):# , range(0x80, 0xFF)):
        string = string.replace(chr(j), '\\x' + hex(j)[2:].zfill(2))
    string = process_ruby(string)
    string = process_ctrl(string)
    string = process_kana(string)
        
    return string


def process_kana(s):
    while r'\x1bK' in s and r'\x1bH' in s:
        if s.find(r'\x1bH') < s.find(r'\x1bK'):
            s = s[:s.find(r'\x1bH')] + s[s.find(r'\x1bH') + 5:]
        x = s[s.find(r'\x1bK'):s.find(r'\x1bH') + 5]
        s = s.replace(x, to_katakana(x))
    return to_hiragana(s.replace(r'\x1bK', '{K}').replace(r'\x1bH', ''))


KATAKANA = {
	'ｶﾞ': 'ガ',
	'ｷﾞ': 'ギ',
	'ｸﾞ': 'グ',
	'ｹﾞ': 'ゲ',
	'ｺﾞ': 'ゴ',
	'ｻﾞ': 'ザ',
	'ｼﾞ': 'ジ',
	'ｽﾞ': 'ズ',
	'ｾﾞ': 'ゼ',
	'ｿﾞ': 'ゾ',
	'ﾀﾞ': 'ダ',
	'ﾁﾞ': 'ヂ',
	'ﾂﾞ': 'ヅ',
	'ﾃﾞ': 'デ',
	'ﾄﾞ': 'ド',
	'ﾊﾞ': 'バ',
	'ﾋﾞ': 'ビ',
	'ﾌﾞ': 'ブ',
	'ﾍﾞ': 'ベ',
	'ﾎﾞ': 'ボ',
	'ﾊﾟ': 'パ',
	'ﾋﾟ': 'ピ',
	'ﾌﾟ': 'プ',
	'ﾍﾟ': 'ペ',
	'ﾎﾟ': 'ポ',
	'ｳﾞ': 'ヴ',
	'ｱ': 'ア',
	'ｲ': 'イ',
	'ｳ': 'ウ',
	'ｴ': 'エ',
	'ｵ': 'オ',
	'ｶ': 'カ',
	'ｷ': 'キ',
	'ｸ': 'ク',
	'ｹ': 'ケ',
	'ｺ': 'コ',
	'ｻ': 'サ',
	'ｼ': 'シ',
	'ｽ': 'ス',
	'ｾ': 'セ',
	'ｿ': 'ソ',
	'ﾀ': 'タ',
	'ﾁ': 'チ',
	'ﾂ': 'ツ',
	'ﾃ': 'テ',
	'ﾄ': 'ト',
	'ﾅ': 'ナ',
	'ﾆ': 'ニ',
	'ﾇ': 'ヌ',
	'ﾈ': 'ネ',
	'ﾉ': 'ノ',
	'ﾊ': 'ハ',
	'ﾋ': 'ヒ',
	'ﾌ': 'フ',
	'ﾍ': 'ヘ',
	'ﾎ': 'ホ',
	'ﾏ': 'マ',
	'ﾐ': 'ミ',
	'ﾑ': 'ム',
	'ﾒ': 'メ',
	'ﾓ': 'モ',
	'ﾔ': 'ヤ',
	'ﾕ': 'ユ',
	'ﾖ': 'ヨ',
	'ﾗ': 'ラ',
	'ﾘ': 'リ',
	'ﾙ': 'ル',
	'ﾚ': 'レ',
	'ﾛ': 'ロ',
	'ﾜ': 'ワ',
	'ｦ': 'ヲ',
	'ﾝ': 'ン',
	'ｧ': 'ァ',
	'ｨ': 'ィ',
	'ｩ': 'ゥ',
	'ｪ': 'ェ',
	'ｫ': 'ォ',
	'ｬ': 'ャ',
	'ｭ': 'ュ',
	'ｮ': 'ョ',
	'ｯ': 'ッ'
}
def to_katakana(s):
    s = s.replace(r'\x1bK', '').replace(r'\x1bH', '')
    for a, b in KATAKANA.items():
        s = s.replace(a, b)
    return s
    

HIRAGANA = {
	'ｶﾞ': 'が',
	'ｷﾞ': 'ぎ',
	'ｸﾞ': 'ぐ',
	'ｹﾞ': 'げ',
	'ｺﾞ': 'ご',
	'ｻﾞ': 'ざ',
	'ｼﾞ': 'じ',
	'ｽﾞ': 'ず',
	'ｾﾞ': 'ぜ',
	'ｿﾞ': 'ぞ',
	'ﾀﾞ': 'だ',
	'ﾁﾞ': 'ぢ',
	'ﾂﾞ': 'づ',
	'ﾃﾞ': 'で',
	'ﾄﾞ': 'ど',
	'ﾊﾞ': 'ば',
	'ﾋﾞ': 'び',
	'ﾌﾞ': 'ぶ',
	'ﾍﾞ': 'べ',
	'ﾎﾞ': 'ぼ',
	'ﾊﾟ': 'ぱ',
	'ﾋﾟ': 'ぴ',
	'ﾌﾟ': 'ぷ',
	'ﾍﾟ': 'ぺ',
	'ﾎﾟ': 'ぽ',
	'ｳﾞ': 'ゔ',
	'ｱ': 'あ',
	'ｲ': 'い',
	'ｳ': 'う',
	'ｴ': 'え',
	'ｵ': 'お',
	'ｶ': 'か',
	'ｷ': 'き',
	'ｸ': 'く',
	'ｹ': 'け',
	'ｺ': 'こ',
	'ｻ': 'さ',
	'ｼ': 'し',
	'ｽ': 'す',
	'ｾ': 'せ',
	'ｿ': 'そ',
	'ﾀ': 'た',
	'ﾁ': 'ち',
	'ﾂ': 'つ',
	'ﾃ': 'て',
	'ﾄ': 'と',
	'ﾅ': 'な',
	'ﾆ': 'に',
	'ﾇ': 'ぬ',
	'ﾈ': 'ね',
	'ﾉ': 'の',
	'ﾊ': 'は',
	'ﾋ': 'ひ',
	'ﾌ': 'ふ',
	'ﾍ': 'へ',
	'ﾎ': 'ほ',
	'ﾏ': 'ま',
	'ﾐ': 'み',
	'ﾑ': 'む',
	'ﾒ': 'め',
	'ﾓ': 'も',
	'ﾔ': 'や',
	'ﾕ': 'ゆ',
	'ﾖ': 'よ',
	'ﾗ': 'ら',
	'ﾘ': 'り',
	'ﾙ': 'る',
	'ﾚ': 'れ',
	'ﾛ': 'ろ',
	'ﾜ': 'わ',
	'ｦ': 'を',
	'ﾝ': 'ん',
	'ｧ': 'ぁ',
	'ｨ': 'ぃ',
	'ｩ': 'ぅ',
	'ｪ': 'ぇ',
	'ｫ': 'ぉ',
	'ｬ': 'ゃ',
	'ｭ': 'ゅ',
	'ｮ': 'ょ',
	'ｯ': 'っ'
}
def to_hiragana(s):
    s = s.replace(r'\x1bK', '').replace(r'\x1bH', '')
    for a, b in HIRAGANA.items():
        s = s.replace(a, b)
    return s


RUBY_CHAR = ['[', ']']
def process_ruby(s):
    i = 0
    while r'\x1br' in s:
        s = s.replace(r'\x1br', RUBY_CHAR[i], 1)
        i = (i + 1) % 2
    return s


CONTROL_CODES = {
    '\\x00': '{NULL}',
    '\\x01"': '{C1}',
    '\\x1bc\x31': '{Color:31}',
    '\\x1bc\x32': '{Color:32}',
    '\\x1bc\x33': '{Color:33}',
    r'\x05\x05\x04': '\n\t{Sub}',
    r'\x01S%3': '{S%3}',
    r'\x05\x05\x05': '{End}',
    r'\x1bkﾊ': 'é',
    r'\x1bkﾁ': 'à'
}
def process_ctrl(s):
    for a, b in CONTROL_CODES.items():
        if a in s:
            s = s.replace(a, b)
    
    while r'\x1bc' in s:
        i = s.find(r'\x1bc')
        if s[i+5] != '\\':
            s = s[:i] + '{Color:' + s[i+5].encode('shift_jisx0213').hex() + '}' + s[i+6:]
        else:
            s = s[:i] + '{Color:' + s[i+7:i+9] + '}' + s[i+6:]
    while r'\x1bw' in s:
        i = s.find(r'\x1bw')
        if s[i+5] != '\\':
            s = s[:i] + '{Wait:' + s[i+5].encode('shift_jisx0213').hex() + '}' + s[i+6:]
        else:
            s = s[:i] + '{Wait:' + s[i+7:i+9] + '}' + s[i+6:]
    while r'\x1bs' in s:
        i = s.find(r'\x1bs')
        if s[i+5] != '\\':
            s = s[:i] + '{NameColor:' + s[i+5].encode('shift_jisx0213').hex() + '}' + s[i+6:]
        else:
            s = s[:i] + '{NameColor:' + s[i+7:i+9] + '}' + s[i+6:]
    while r'\x1bf' in s:
        i = s.find(r'\x1bf')
        if s[i+5] != '\\':
            s = s[:i] + '{CharImage:' + s[i+5].encode('shift_jisx0213').hex() + '}' + s[i+6:]
        else:
            s = s[:i] + '{CharImage:' + s[i+7:i+9] + '}' + s[i+6:]
    while r'\x1b@' in s:
        i = s.find(r'\x1b@')
        if s[i+5] != '\\':
            s = s[:i] + '{Char:' + s[i+5:i+9] + '}' + s[i+9:]
    while r'\x02' in s:
        i = s.find(r'\x02')
        if s[i+4] != '\\':
            s = s[:i] + '{Var:' + s[i+4:i+6].encode('shift_jisx0213').hex() + '}' + s[i+6:]
    
    return s


with open(sys.argv[1], 'rb') as file:
    data = file.read()
    
    i = 0
    while data[i:i + 8] != b"\x00\x00\x00\x00\x00\x00\x00\x00":
        start = read_val(data, i)
        end = read_val(data, i + 4) + start
        # print(hex(start), hex(end))
        
        raw = decrypt(data[start:end])
        if RAW_OUT:
            with open(os.path.dirname(sys.argv[1]) + '\\' + str(i // 8) + '.msg', 'wb') as out:
                out.write(raw)
            # break
            continue
        
        count = read_val(raw, 0)
        pointers = [read_val(raw, 4 + i * 4) for i in range(count)] + [len(raw)]
        # print([hex(i) for i in pointers])
        
        output = ""
        for j in range(len(pointers) - 1):
            string = raw[pointers[j]:pointers[j + 1]]                    
            output += str(j) + '\t' + process_string(string) + '\n'
            
        with open(os.path.dirname(sys.argv[1]) + '\\' + str(i // 8) + '.txt', 'w', encoding='utf-8') as out:
            out.write(output)
        
        i += 8
