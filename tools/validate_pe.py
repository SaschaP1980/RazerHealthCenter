#!/usr/bin/env python3
import struct,sys
p=sys.argv[1]
b=open(p,'rb').read(); pe=struct.unpack_from('<I',b,0x3c)[0]
assert b[pe:pe+4]==b'PE\0\0','bad PE signature'
coff=pe+4; machine,nsec=struct.unpack_from('<HH',b,coff); optsz=struct.unpack_from('<H',b,coff+16)[0]; opt=coff+20
assert machine==0x8664, f'not amd64: {machine:#x}'
assert struct.unpack_from('<H',b,opt)[0]==0x20b, 'not PE32+'
assert struct.unpack_from('<H',b,opt+68)[0]==2, 'not Windows GUI subsystem'
sectalign=struct.unpack_from('<I',b,opt+32)[0]; sizeimg=struct.unpack_from('<I',b,opt+56)[0]; secbase=opt+optsz
secs=[]
for i in range(nsec):
 o=secbase+i*40; name=b[o:o+8].split(b'\0')[0].decode('ascii','replace'); vs,va,rs,fp=struct.unpack_from('<IIII',b,o+8); secs.append((name,vs,va,rs,fp))
rsrc=[s for s in secs if s[0]=='.rsrc']
assert len(rsrc)==1,'expected exactly one .rsrc'
name,vs,va,rs,fp=rsrc[0]
assert va+max(vs,rs) <= sizeimg, f'.rsrc outside SizeOfImage ({va:#x}+{max(vs,rs):#x}>{sizeimg:#x})'
rrva,rsz=struct.unpack_from('<II',b,opt+112+2*8)
assert rrva==va and 0<rsz<=vs, 'resource directory mismatch'
# Ensure resource section starts at/after all previous sections and does not overlap.
for s in secs:
 if s[0]=='.rsrc': continue
 _,ovs,ova,ors,ofp=s
 assert not (ova < va+max(vs,rs) and va < ova+max(ovs,ors)), f'RVA overlap with {s[0]}'
# Validate resource data entries map inside the resource section.
root=fp; visited=set(); data_entries=[]
def walk(rel):
 assert rel not in visited,'resource directory cycle'; visited.add(rel)
 off=root+rel; assert off+16<=len(b)
 named,ids=struct.unpack_from('<HH',b,off+12)
 for i in range(named+ids):
  _,t=struct.unpack_from('<II',b,off+16+i*8); rel2=t&0x7fffffff
  if t&0x80000000: walk(rel2)
  else:
   de=root+rel2; assert de+16<=len(b); drva,sz,cp,res=struct.unpack_from('<IIII',b,de)
   assert va <= drva and drva+sz <= va+rs, f'resource payload outside .rsrc: {drva:#x}+{sz:#x}'
   data_entries.append((drva,sz))
walk(0)
assert data_entries,'no resource data entries'
print(f'PASS: amd64 GUI, sections={nsec}, .rsrc RVA={va:#x}, SizeOfImage={sizeimg:#x}, resource entries={len(data_entries)}')
