"""Evidence-first bounded parsing of this title's UE5 complete property tags."""
from pathlib import Path
from dataclasses import dataclass
import json
import struct


class FormatError(ValueError): pass

@dataclass
class TypeName:
    name:str
    children:list
    def __str__(self):
        return self.name+('('+','.join(map(str,self.children))+')' if self.children else '')

class Reader:
    def __init__(self,data,start=0,end=None):
        self.data=data; self.pos=start; self.end=len(data) if end is None else end
        if not 0<=start<=self.end<=len(data):
            raise FormatError('Reader boundaries exceed the available data.')
    def read(self,size):
        if size<0 or self.pos+size>self.end: raise FormatError(f'Out of bounds at {self.pos:#x}, size {size}')
        value=self.data[self.pos:self.pos+size]; self.pos+=size; return value
    def number(self,fmt): return struct.unpack(fmt,self.read(struct.calcsize(fmt)))[0]
    def string(self):
        n=self.number('<i')
        if not n: return ''
        if abs(n)>4096: raise FormatError(f'Bad FString at {self.pos-4:#x}: {n}')
        raw=self.read(n if n>0 else -2*n)
        terminal=b'\0' if n>0 else b'\0\0'
        if not raw.endswith(terminal): raise FormatError(f'Nonterminated FString at {self.pos:#x}')
        return raw[:-len(terminal)].decode('utf-8' if n>0 else 'utf-16le')
    def type_name(self,depth=0):
        if depth>8: raise FormatError('Deep property type')
        name=self.string(); count=self.number('<i')
        if not 0<=count<=8: raise FormatError(f'Bad type child count {count} at {self.pos:#x}')
        return TypeName(name,[self.type_name(depth+1) for _ in range(count)])

def tags(reader,depth=0):
    if depth>12: raise FormatError('Deep property records')
    result=[]
    while reader.pos<reader.end:
        begin=reader.pos
        name=reader.string()
        if name=='None': return result
        typ=reader.type_name()
        size_offset=reader.pos; size=reader.number('<i'); flags_offset=reader.pos; flags=reader.number('<B')
        if size<0 or flags&0xc0: raise FormatError(f'Unsupported tag {name} flags {flags:#x}, size {size}')
        index=reader.number('<i') if flags&1 else 0
        if flags&2: reader.read(16)
        if flags&4:
            extensions=reader.number('<B')
            if extensions&~2: raise FormatError(f'Unsupported extension {extensions:#x}')
            if extensions&2: reader.read(2)
        offset=reader.pos
        if offset+size>reader.end:
            raise FormatError(f'{name}: property payload crosses its enclosing record.')
        sub=Reader(reader.data,offset,offset+size)
        value=None
        if typ.name=='IntProperty' and size==4: value=sub.number('<i')
        elif typ.name=='FloatProperty' and size==4: value=sub.number('<f')
        elif typ.name=='DoubleProperty' and size==8: value=sub.number('<d')
        elif typ.name=='Int64Property' and size==8: value=sub.number('<q')
        elif typ.name=='BoolProperty' and size==0: value=bool(flags&16)
        elif typ.name in ('EnumProperty','NameProperty','StrProperty'):
            value=sub.string()
        elif typ.name=='ByteProperty' and size==1: value=sub.number('<B')
        elif typ.name=='StructProperty' and not flags&8:
            try:
                value=tags(sub,depth+1)
                if sub.pos!=sub.end: raise FormatError('Unconsumed struct data')
            except (FormatError,UnicodeError):
                value={'opaque_bytes':size}; sub.pos=sub.end
        elif typ.name=='ArrayProperty':
            count=sub.number('<i')
            if not 0<=count<=100000: raise FormatError('Invalid array count')
            inner=typ.children[0] if typ.children else None
            value={'count':count,'element_type':str(inner)}
            if inner and inner.name=='StructProperty' and count<20000:
                records=[]
                try:
                    for _ in range(count): records.append(tags(sub,depth+1))
                    if sub.pos!=sub.end: raise FormatError('Unconsumed struct array data')
                    value['records']=records
                except (FormatError,UnicodeError):
                    value['opaque_bytes']=size-4; sub.pos=sub.end
            elif inner and inner.name in ('EnumProperty','NameProperty','StrProperty'):
                value['values']=[sub.string() for _ in range(count)]
            elif inner and inner.name in ('IntProperty','BoolProperty','FloatProperty','ByteProperty'):
                fmt={'IntProperty':'<i','BoolProperty':'<B','FloatProperty':'<f','ByteProperty':'<B'}[inner.name]
                value['values']=[sub.number(fmt) for _ in range(count)]
            else: sub.pos=sub.end
        else:
            value={'opaque_bytes':size}; sub.pos=sub.end
        if sub.pos!=sub.end: raise FormatError(f'{name} ({typ}): consumed{sub.pos-offset} of{size}')
        reader.read(size)
        result.append({'name':name,'type':str(typ),'tag_offset':begin,'size_offset':size_offset,'flags_offset':flags_offset,'flags':flags,
                       'array_index':index,'data_offset':offset,'data_size':size,'value':value})
    raise FormatError('Missing None terminator')

def parse(data):
    if len(data)<8:raise FormatError('Truncated plaintext envelope.')
    size=struct.unpack_from('>I',data)[0]
    if not len(data)-19<=size<=len(data)-4 or any(data[4+size:]): raise FormatError('Invalid envelope')
    r=Reader(data,4,4+size)
    if r.read(4)!=b'GVAS': raise FormatError('Missing GVAS')
    header={'save_version':r.number('<i'),'ue4_version':r.number('<i'),'ue5_version':r.number('<i')}
    header['engine']=[r.number('<H') for _ in range(3)]; header['changelist']=r.number('<I'); header['branch']=r.string()
    header['custom_version_format']=r.number('<i'); count=r.number('<i')
    if not 0<=count<=1000: raise FormatError('Invalid custom versions')
    header['custom_versions']=[{'guid':r.read(16).hex(),'version':r.number('<i')} for _ in range(count)]
    header['save_class']=r.string(); header['serialization_control']=r.number('<B')
    if header['serialization_control']!=0: raise FormatError('Unsupported control')
    properties=tags(r)
    trailer=r.read(r.end-r.pos)
    return {'header':header,'payload_size':size,'padding_size':len(data)-4-size,
            'properties':properties,'trailer_hex':trailer.hex()}

