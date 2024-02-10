import re
registers = {'A': [0,0], 'X': [1,0], 'L': [2,0], 'B': [3,0], 'S': [4,0], 'T': [5,0], 'F': [6,0], 'PC': [8,0], 'SW':[9,0]}
start, name, length = 0, 0, 0

def Opcode_Lookup():
	codes = {}
	file = open(r"D:\Project Systems\sicxe_sheet.csv").readlines()
	for i in range(len(file)):
		temp = file[i][:-1].split(',')
		codes[temp[0].strip()] = [temp[1],temp[2],temp[3]] 
	return codes


def symVal(op,symTab):
		if symTab[op]:
			return symTab[op]
		else:
			return 0

def split(text_file):
	"""accepts address of input text file and returns 3 arrays"""
	global name
	lable = []
	codes = []
	ops = []
	file = open(text_file)
	file = file.readlines()
	for j in range(len(file)):
		line = file[j]
		l = re.split("\s+",line.strip())
		if len(l) == 3:
			lable.append(l[0])
			codes.append(l[1])
			ops.append(l[2])
		elif len(l) == 2:
			lable.append(None)
			codes.append(l[0])
			ops.append(l[1])
		elif len(l) == 1:
			lable.append(None)
			codes.append(l[0])
			ops.append(None)
	name = lable[0]
	return [lable, codes, ops]


def location(text_file):
	global start, length
	cols = split(text_file)
	ops = {}
	n = 0
	if cols[1][0] == "START":
		n = int(cols[2][0])
	start = n
	for i in range(1,len(cols[1])):
		m = n
		size = 0
		if (cols[1][i][0] == '+'):
			frmt = 4
			cols[1][i] = cols[1][i][1:]
		else:
			frmt = int(Lookup[cols[1][i]][0])
		if frmt == 0:
			if cols[1][i] == "BYTE":
				if cols[2][i][0] == "X":
					size = 1
				elif cols[2][i][0] == "c":
					size = len(cols[2][i])-3
			elif cols[1][i] == "RESB":
				size = int(cols[2][i])
			elif cols[1][i] == "RESW":
				size = int(cols[2][i])*3
		else:
			size = frmt
		n += size
		ops[m] = {"label": cols[0][i], "opcode": cols[1][i], "op": cols[2][i], "format": frmt, "next": n, "size": size}
	length = n - start
	return ops


def symbolTab(text_file):
	opTab = location(text_file)
	symbols = {}
	for i in opTab:
		if opTab[i]["label"]:
			symbols[opTab[i]["label"]] = i
		if opTab[i]["op"]:
			op = opTab[i]["op"]
			if op[0] in "#@":
				op = op[1:]
			if op[-2:] == ',X':
				op = op[:-2]
			if (op[0] not in '0123456789cCxX'):
				if (',' not in op) and (op not in 'AXLPCSWBSTF'):
					if (op not in symbols):
						symbols[op] = None
	return [symbols, opTab]


    def objectCode(text_file):
	global registers
	memory = {}#[None]*(2**15)
	array = symbolTab(text_file)
	symTab, opTab = array[0], array[1]
	for i in opTab:
		registers['PC'][1] = opTab[i]["next"]
		op = Lookup[opTab[i]["opcode"]]
		if opTab[i]["format"] == -1: #flag for END directive
			return [opTab, memory]
		elif opTab[i]["format"] == 0: #flag for other directives
			if opTab[i]["opcode"] == "WORD":
				objCode = str(hex(int(opTab[i]["op"])))[2:].upper()
				objCode = "0"*(6-len(objCode)) + objCode
				memory[i] = objCode[:2]
				memory[i+1] = objCode[2:4]
				memory[i+2] = objCode[4:]
			elif opTab[i]["opcode"] == "BYTE":
				objCode = ""
				if opTab[i]["op"][0] in "cC":
					for j in range(2,len(opTab[i]["op"])-1):
						memory[i+j-2] = str(hex(ord(opTab[i]["op"][j])))[2:].upper()
				elif opTab[i]["op"][0] in "xX":
					memory[i] =  opTab[i]["op"][2:4]
			elif opTab[i]["opcode"] == "RESB":
				for j in range(i,i+int(opTab[i]["op"])):
					memory[j] = None
			elif opTab[i]["opcode"] == "RESW":
				for j in range(i,i+int(opTab[i]["op"])*3):
					memory[j] = None
			elif opTab[i]["opcode"] == "BASE":
				opTab[i]["obj"] = ""
		elif opTab[i]["format"] == 1:
			memory[i] = op[1]
			opTab[i]["obj"] = objCode
		elif opTab[i]["format"] == 2:
			if opTab[i]["opcode"] == "CLEAR":
				registers[opTab[i]["op"]][1] = 0
			memory[i] = op[1]
			r1 = opTab[i]["op"].split(',')
			for j in r1:
				if j in registers:
					objCode = '0'+str(registers[j][1])
				elif op[2][j][0] in 'mn':
					objCode = str(hex(int(j)))[2:].upper()
			memory[i+1] = objCode
			opTab[i]["obj"] = objCode
		elif opTab[i]["format"] in [3,4]:
			if opTab[i]["opcode"] == 'RSUB': #special case for RSUB
				objCode = '4C0000'
			else: 
				opBin = str(bin(int(op[1],16)))[2:8]
				opBin = '0'*(6-len(opBin)) + opBin
				#Set flag bits
				flags = '000000' #flags
				dispLen = 12
				op = opTab[i]["op"]
				if op[0] == '@': #n bit
					flags = '1' + flags[1:]
					op = op[1:]
				if op[0] == '#': #i bit
					flags = flags[0] + '1' + flags[2:]
					op = op[1:]
				if op[-2:] in [',X', ',x']: #x bit
					flags = flags[:2] + '1' + flags[3:]
					op = op[:-2]
				if op in symTab:
					ta = symVal(op,symTab)
				else:
					ta = int(op,16)
				disp = ta - registers['PC'][1] #assume pc relative
				if disp > 2048 or disp < -2047: #b bit
					flags = flags[:3] + '1' + flags[4:]
				else: 							#p bit
					flags = flags[:4] + '1' + flags[5:]
				if opTab[i]["format"] == 4: #e bit
					flags = flags[:5] + '1'
					dispLen = 20
				intd = disp
				if disp < 0:
					disp += 2**(len(bin(disp))-2) #get 2s complement
				disp = bin(disp)[2:]
				disp = ('0'*(dispLen-len(disp)) + disp)[:dispLen]
				objCode = hex(int(opBin+flags+disp,2))[2:].upper()
			memory[i] = objCode[:2]
			memory[i+1] = objCode[2:4]
			memory[i+2] = objCode[4:6]
			if opTab[i]["format"] == 4:
				memory[i+3] = objCode[6:]
			opTab[i]["obj"] = objCode
	print(opTab)
	return [opTab, memory]


    def createRecord(opTab):
	global start, name, length
	Record = []
	tstart = start
	start = hex(start)[2:]
	length = hex(length)[2:]
	header = 'H.'
	header += name + 'X'*(6-len(name))+'.'
	header += '0'*(6-len(start))+start+'.'
	header += '0'*(6-len(length))+length
	print(header)
	Record.append(header)
	record = 'T.'+'0'*(8-len(hex(tstart)))+hex(tstart)[2:]
	objcodes = ''
	newR = False
	for i in opTab:
		if opTab[i]['format'] >= 1:
			if newR:
				tstart = i
				record = 'T.'+'0'*(8-len(hex(tstart)))+hex(tstart)[2:]
				objcodes = ''
				newR = False
			objcodes += '.'+'0'*(6-len(opTab[i]['obj'])) +opTab[i]['obj']
		else:
			if objcodes == '':
				continue
			newR = True
			tlen = hex(i-tstart)[2:]
			record = record[:8]+'.' + '0'*(6-len(tlen))+tlen + record[8:] + objcodes
			print(record)
			Record.append(record)
			objcodes = ''
	end = 'E.'+'0'*(6-len(start))+start
	Record.append(end)
	return Record

    with open(r"D:\Project Systems\outSICXE.txt",'w') as file:
	for i in Record:
		file.write(i+'\n')
	file.close()

Lookup = Opcode_Lookup()
ob = objectCode(r"D:\Project Systems\inSICXE.txt")
Record = createRecord(ob[0])


