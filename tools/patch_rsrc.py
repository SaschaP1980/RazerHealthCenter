#!/usr/bin/env python3
"""Inject recovered v1.7.0 PE resources into the reconstructed Go executable.

Unlike the first recovery patcher, this relocates the resource tree to the next
valid RVA of the reconstructed image and adjusts IMAGE_RESOURCE_DATA_ENTRY
OffsetToData RVAs. Resource payload bytes (icons, manifest, version resources)
remain byte-identical; only location-dependent RVA fields change.
"""
import struct, sys, json, hashlib

def align(x,a): return (x+a-1)//a*a

def pe_info(data):
    pe=struct.unpack_from('<I',data,0x3c)[0]
    if data[pe:pe+4]!=b'PE\0\0': raise ValueError('not PE')
    coff=pe+4
    nsec=struct.unpack_from('<H',data,coff+2)[0]
    optsz=struct.unpack_from('<H',data,coff+16)[0]
    opt=coff+20
    if struct.unpack_from('<H',data,opt)[0]!=0x20b: raise ValueError('not PE32+')
    return dict(pe=pe,coff=coff,nsec=nsec,optsz=optsz,opt=opt,
                sectalign=struct.unpack_from('<I',data,opt+32)[0],
                filealign=struct.unpack_from('<I',data,opt+36)[0],
                secbase=opt+optsz,
                size_image=struct.unpack_from('<I',data,opt+56)[0])

def relocate_resource_tree(raw, old_rva, new_rva):
    b=bytearray(raw)
    delta=new_rva-old_rva
    visited_dirs=set(); visited_data=set()
    def walk_dir(off):
        if off in visited_dirs: return
        visited_dirs.add(off)
        if off < 0 or off+16 > len(b): raise ValueError(f'resource directory offset out of range: {off:#x}')
        named, ids = struct.unpack_from('<HH', b, off+12)
        count=named+ids
        ent=off+16
        if ent+count*8 > len(b): raise ValueError('resource directory entries out of range')
        for i in range(count):
            _, target=struct.unpack_from('<II', b, ent+i*8)
            sub=target & 0x7fffffff
            if target & 0x80000000:
                walk_dir(sub)
            else:
                if sub in visited_data: continue
                visited_data.add(sub)
                if sub < 0 or sub+16 > len(b): raise ValueError(f'resource data entry out of range: {sub:#x}')
                data_rva=struct.unpack_from('<I', b, sub)[0]
                new_data_rva=data_rva+delta
                if not (new_rva <= new_data_rva < new_rva+len(b)):
                    raise ValueError(f'relocated resource data RVA out of range: {data_rva:#x}->{new_data_rva:#x}')
                struct.pack_into('<I', b, sub, new_data_rva)
    walk_dir(0)
    return bytes(b), len(visited_data)

if len(sys.argv)!=5:
    raise SystemExit('usage: patch_rsrc.py input.exe app_rsrc.bin app_rsrc.json output.exe')
inp, rawp, metap, outp=sys.argv[1:]
b=bytearray(open(inp,'rb').read())
raw=open(rawp,'rb').read(); meta=json.load(open(metap)); pi=pe_info(b)
if hashlib.sha256(raw).hexdigest()!=meta['sha256']:
    raise SystemExit('resource hash mismatch')

# Ensure there is room for one more section header and find the end of the
# reconstructed image. Use SizeOfImage as the authoritative next RVA; it is
# section-aligned by the Go linker.
new_hdr=pi['secbase']+pi['nsec']*40
first_raw=1<<62
max_virtual_end=0
for i in range(pi['nsec']):
    o=pi['secbase']+i*40
    vsize,vaddr,rawsize,rawptr=struct.unpack_from('<IIII',b,o+8)
    if rawptr: first_raw=min(first_raw,rawptr)
    max_virtual_end=max(max_virtual_end, vaddr+max(vsize,rawsize))
if new_hdr+40>first_raw:
    raise SystemExit('no room for extra section header')
new_rva=align(max(pi['size_image'],max_virtual_end),pi['sectalign'])
relocated, data_entries = relocate_resource_tree(raw, meta['vaddr'], new_rva)

rawptr=align(len(b),pi['filealign'])
b.extend(b'\0'*(rawptr-len(b)))
b.extend(relocated)
if len(relocated) < meta['rawsize']:
    b.extend(b'\0'*(meta['rawsize']-len(relocated)))

hdr=struct.pack('<8sIIIIIIHHI',b'.rsrc\0\0\0',meta['vsize'],new_rva,meta['rawsize'],rawptr,0,0,0,0,meta['chars'])
b[new_hdr:new_hdr+40]=hdr
struct.pack_into('<H',b,pi['coff']+2,pi['nsec']+1)
struct.pack_into('<II',b,pi['opt']+112+2*8,new_rva,meta['resource_directory_size'])
size_image=align(new_rva+max(meta['vsize'],meta['rawsize']),pi['sectalign'])
struct.pack_into('<I',b,pi['opt']+56,size_image)
struct.pack_into('<I',b,pi['opt']+64,0)  # checksum optional for unsigned PE
open(outp,'wb').write(b)
print(f'resource relocated {meta["vaddr"]:#x}->{new_rva:#x}; data_entries={data_entries}; SizeOfImage={size_image:#x}')
