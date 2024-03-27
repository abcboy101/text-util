# Parses GMSG/GSMG files and outputs a txt file.
# Usage: python gmsg.py <filename>

import sys

def read_val(data, index, length=4):
    # print(data[index:index+length])
    return int.from_bytes(data[index:index+length], byteorder='little', signed=False)

with open(sys.argv[1], 'rb') as file:
    data = file.read()
    
    # Check file header
    if (data[:4] != b'GMSG'):
        print('Not a GMSG file.')
        sys.exit()
        
    total_size, start_id, end_id, c, d, e, start_pointer = [read_val(data, i) for i in range(0x04, 0x20, 4)]
    print((total_size, start_id, end_id, c, d, e, start_pointer), [hex(i) for i in (total_size, start_id, end_id, c, d, e, start_pointer)])
    
    count = end_id - start_id + 1
    print(count)
    
    pointers = [read_val(data, i) + start_pointer for i in range(0x20, 0x20 + 4 * count, 4)] + [total_size]
    #for i in range(1, len(pointers) - 1):
    #    pointers[i] += start_pointer
    print([hex(i) for i in pointers])
    
    output = ''
    for i in range(count):
        id = start_id + i
        string = data[pointers[i]:pointers[i+1]].decode('utf-16-le')
        string = string[0:string.find('\x00')]
        string = string.replace('\\', '\\\\').replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')
        for i in range(0x00, 0x20):
            string = string.replace(chr(i), '\\x' + hex(i)[2:].zfill(2))
        output += '\t'.join([str(id), string]) + '\n'
        
    with open((sys.argv[1])[:-7] + '.txt', 'w', encoding='utf-8') as out:
        out.write(output)