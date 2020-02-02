# Parses hangul encoded as kanji in EUC-JP to UTF-8.
# Requires Table.tbl file.
# Usage: python jis_hangul.py f <input file> <output file>
#        python jis_hangul.py

import sys

in_file  = sys.argv[2]
out_file = sys.argv[3]

def encode_text(text, map):
	for i, j in map:
		text = text.replace(j, i)
	return text

def decode_text(text, map):
	for i, j in map:
		text = text.replace(i, j)
	return text

mapping =  [['蔽', 'ㄱ'], ['閉', 'ㄲ'], ['米', 'ㄴ'], ['壁', 'ㄷ'], ['癖', 'ㄸ'], ['碧', 'ㄹ'], ['篇', 'ㅁ'], ['編', 'ㅂ'],
			['辺', 'ㅃ'], ['遍', 'ㅅ'], ['便', 'ㅆ'], ['勉', 'ㅇ'], ['娩', 'ㅈ'], ['弁', 'ㅉ'], ['鞭', 'ㅊ'], ['保', 'ㅋ'],
			['舗', 'ㅌ'], ['鋪', 'ㅍ'], ['圃', 'ㅎ'], ['捕', 'ㅏ'], ['歩', 'ㅐ'], ['甫', 'ㅑ'], ['補', 'ㅒ'], ['輔', 'ㅓ'],
			['穂', 'ㅔ'], ['募', 'ㅕ'], ['墓', 'ㅖ'], ['慕', 'ㅗ'], ['簿', ' ㅛ'], ['菩', 'ㅜ'], ['呆', 'ㅠ'], ['報', 'ㅡ'],
			['宝', 'ㅣ'], ['捧', '…'], ['放', '♂'], ['方', '♀'], ['朋', '-'], ['法', '갹'], [' 泡', '꼍'], ['烹', '늄'],
			['砲', '떽'], ['縫', '맒'], ['胞', '봄'], ['芳', '섹'], ['萌', '씸'], ['蓬', '음'], ['蜂', '쩍'], ['褒', '캭'],
			['訪', '틱'], ['豊', '횟']] + \
			[[bytearray([(int(i, 16) + 479) // 94 + 161, (int(i, 16) + 479) % 94 + 161])
				.decode('euc-jp'), j] # .encode('shift-jis'), j]
				for i, j in [line.split('=')
				for line in open('Table.tbl', encoding='utf-8').read().split('\n')]]

if sys.argv[1] == "f":
	t = open(in_file, 'r', encoding='shift-jis', errors='ignore').read()
	t = decode_text(t, mapping)
	open(out_file, 'w', encoding='utf-8').write(t)
	print("Done!")
else:
	t = input("Input: ") # open(in_file, 'r', encoding='shift-jis', errors='ignore').read()
	t = encode_text(t, mapping)
	print(t) # open(out_file, 'w', encoding='utf-8').write(t)
	t = decode_text(t, mapping)
	print(t) # open(out_file, 'w', encoding='utf-8').write(t)
	print("Done!")