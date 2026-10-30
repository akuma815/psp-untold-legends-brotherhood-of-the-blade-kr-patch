"""Documented Allegrex scalar/FPU32 profile over complete external ISA backends.

Manual-derived constraints are policy/verification data, not a subset assembler.
Unknown extensions, reserved fields and truncated words fail before interpretation.
"""
import json
import re
import struct
import subprocess
import sys
from survey import ROOT,digest
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN

TOOL=ROOT/'workspace/tools/allegrex_015'
ASSEMBLER=TOOL/'armips_dev_build/Release/armips.exe'
ASSEMBLER_SHA='3c295bcff7ff8bc5220472e80cf0715aa03ff72b6ed074562fab5b09774e904d'
sys.path.insert(0,str(TOOL/'python'))
import rabbitizer as rz

class Profile:
    def __init__(self):
        self.path=ROOT/'config/allegrex_profile.json'
        self.data=json.loads(self.path.read_text(encoding='utf-8'))
        assert self.data['profile_id']=='allegrex_le32_documented_scalar_fpu_r1'
        assert len(self.data['instructions'])==132
        assert digest(ASSEMBLER.read_bytes())==ASSEMBLER_SHA
        rz.config.pseudos_enablePseudos=False
        rz.config.misc_expandJalr=True
        self.core_decoder=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)

    def classify(self,word):
        matches=[]
        for entry in self.data['instructions'].values():
            if word&entry['fixed_mask']!=entry['fixed_value']:continue
            values={f['name']:(word>>f['shift'])&((1<<f['bits'])-1) for f in entry['operands']}
            name=entry['name']
            if name=='cfc1' and values['fs'] not in [0,31]:continue
            if name=='ctc1' and values['fs']!=31:continue
            if name=='ext' and values['pos']+values['size']+1>32:continue
            if name=='ins' and values['size']<values['pos']:continue
            matches.append((entry,values))
        if len(matches)==2 and word==0:
            matches=[m for m in matches if m[0]['name']=='nop']
        if len(matches)!=1:raise ValueError(f'Out-of-profile or reserved word0x{word:08X}')
        return matches[0]

    def decode(self,data,origin):
        if len(data)%4 or origin%4:raise ValueError('Truncated or unaligned MIPS32 code')
        result=[]
        for pos in range(0,len(data),4):
            word=struct.unpack_from('<I',data,pos)[0];entry,values=self.classify(word)
            pc=origin+pos;ins=rz.Instruction(word,pc,rz.InstrCategory.R4000ALLEGREX)
            if ins.isValid() and ins.getOpcodeName()==entry['name']:
                text=ins.disassemble().split('#')[0].strip();backend='rabbitizer_allegrex'
            else:
                # General independent core backend, checked against the same complete
                # manual profile. Never accept its extra MIPS modes or data fallback.
                other=list(self.core_decoder.disasm(data[pos:pos+4],pc))
                if len(other)!=1 or other[0].size!=4 or other[0].mnemonic!=entry['name']:
                    raise ValueError(('External decoders rejected documented form',entry['name'],hex(word),hex(pc)))
                text=other[0].mnemonic+' '+other[0].op_str;backend='capstone_core_mips32'
            name=entry['name']
            if name in ['mfc0','mtc0']:
                text=f'{name} ${values["rt"]}, ${values["rd"]}'
            elif name in ['cfc1','ctc1']:
                text=f'{name} ${values["rt"]}, ${values["fs"]}'
            elif name=='jalr':text=f'jalr ${values["rs"]}, ${values["rd"]}'
            elif name in ['break','syscall']:text=f'{name} 0x{values["code"]:X}'
            elif name in ['j','jal']:
                target=((pc+4)&0xf0000000)|((word&0x03ffffff)<<2)
                text=f'{name} 0x{target:08X}'
            elif name in ['div','divu']:text=f'{name} ${values["rs"]}, ${values["rt"]}'
            if '.word' in text:raise ValueError('Data fallback cannot be an instruction')
            result.append({'pc':pc,'word':word,'name':name,'fields':values,'assembly':text,'backend':backend})
        return result

    def assemble(self,source,origin,folder,stem,symbols=False):
        if origin%4:raise ValueError('Unaligned origin')
        folder.mkdir(parents=True,exist_ok=True)
        path=folder/(stem+'.asm');binary=folder/(stem+'.bin')
        path.write_text(f'.psp\n.create "{binary.as_posix()}",0x{origin:X}\n'+source+'\n.close\n',encoding='utf-8')
        command=[str(ASSEMBLER),str(path)]
        if symbols:command.extend(['-sym2',str(folder/(stem+'.sym'))])
        proc=subprocess.run(command,cwd=folder,capture_output=True)
        if proc.returncode:raise ValueError((proc.stdout+proc.stderr).decode(errors='replace'))
        data=binary.read_bytes();self.decode(data,origin)
        return data

    def verify_roundtrip(self,data,origin,folder,stem):
        decoded=self.decode(data,origin)
        assembled=self.assemble('\n'.join(i['assembly'] for i in decoded),origin,folder,stem)
        if data!=assembled:raise ValueError('Nonidentical instruction round trip')
        return decoded

def fixture_word(entry,values):
    """Independent manual field oracle, used for tests, never for game emission."""
    word=entry['fixed_value']
    for f in entry['operands']:
        value=values[f['name']]
        if f['kind']=='size_minus_one':value-=1
        elif f['kind']=='size_msb':value+=values['pos']-1
        word|=(value&((1<<f['bits'])-1))<<f['shift']
    return word

def fixture_assembly(entry,values):
    text=entry['syntax'];name=entry['name'];tokens={}
    for f in entry['operands']:
        value=values[f['name']]
        if f['kind'] in ['gpr','cop0','fcr']:token=f'${value}'
        elif f['kind']=='fpr':token=f'f{value}'
        elif f['kind']=='jump26':token=f'0x{value<<2:X}'
        elif f['name']=='offset' and 'base' not in values:token=f'(.+4+({value}<<2))'
        else:token=str(value)
        tokens[f['name']]=token
    text=re.sub('[a-z]+',lambda m:tokens[m[0]],text)
    if name=='jalr':text=f'${values["rs"]},${values["rd"]}'
    return name+(' '+text if text else '')
