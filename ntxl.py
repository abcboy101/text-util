# Parses NTXL files and outputs a txt file.
# Usage: python ntxl.py <filename>

import sys

def read_val(data, index, length=4):
    # print(data[index:index+length])
    return int.from_bytes(data[index:index+length], byteorder='little', signed=False)

def read_string_table(data, start, end):
    string_table = []
    for i in range(start, end, 12):
        uid_index = read_val(data, i, 4)
        str_index = read_val(data, i + 4, 4)
        string_table.append(get_string(data, uid_index, str_index))
    return string_table
    
def get_string(data, uid_index, str_index):
    # read string identifier
    uid_id = read_val(data, uid_index, 2)
    uid_length = read_val(data, uid_index + 2, 2)
    uid_value = data[uid_index + 4:uid_index + 4 + uid_length].decode('ascii')
    
    # read string
    str_type = read_val(data, str_index, 2) # 2 is a normal string
    str_length = read_val(data, str_index + 2, 2)
    # strings are null-terminated utf-16le
    str_value = data[str_index + 4:str_index + 4 + str_length]
    try:
        str_value = str_value.decode('utf-16-le')
    except:
        print("Failed to encode:")
        print(hex(uid_id), uid_value, hex(str_index), str_type, str_value)
        str_value = str_value.hex() #fallback to hex
    str_value = str_value[0:str_value.find('\x00')]
    str_value = str_value.replace('\\', '\\\\').replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')
    
    # return ("{0:#06x}".format(uid_id), uid_value, "{0:#06x}".format(str_type), str_value)
    return ("{0:#06x}".format(uid_id), str(str_type), uid_value, str_value)

with open(sys.argv[1], 'rb') as file:
    data = file.read()
    
    # Check file header
    if (data[0:6] != b'NTXL\x05\x01'):
        print('Not a NTXL file.')
        sys.exit()
    
    lang = data[6:8].decode('ascii')
    print('lang', lang)
    
    const = read_val(data, 0x08, 4)
    print('const', const)
    
    file_start, file_end = read_val(data, 0x0C, 4), read_val(data, 0x10, 4)
    print('file_start, file_end', [hex(file_start), hex(file_end)])
    
    uval, start, end = (read_val(data, i, 4) for i in range(0x14, 0x20, 4))
    print('uval, start, end', [hex(i) for i in [uval, start, end]])
    
    string_table = read_string_table(data, start, end)
    # print(string_table)
    output = ''
    for a in string_table:
        output += '\t'.join(a) + '\n'
    with open((sys.argv[1])[:-8] + lang + '.txt', 'w', encoding='utf-8') as out:
        out.write(output)