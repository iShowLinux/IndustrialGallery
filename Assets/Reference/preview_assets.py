"""Source-asset contact sheet only: this is NOT an Unreal render."""
from pathlib import Path
import math
from PIL import Image, ImageDraw

BASE=Path(__file__).resolve().parent

def unit(v):
    length=math.sqrt(sum(n*n for n in v))
    return tuple(n/length for n in v)

def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def dot(a,b): return sum(x*y for x,y in zip(a,b))

v,f=[],[]
for line in (BASE/'Meshes'/'SM_BronzeLoop.obj').read_text().splitlines():
    parts=line.split()
    if parts and parts[0]=='v': v.append(tuple(map(float,parts[1:])))
    if parts and parts[0]=='f': f.append(tuple(int(n.split('/')[0])-1 for n in parts[1:]))
canvas=Image.new('RGB',(1440,920),'#28282a')
draw=ImageDraw.Draw(canvas)
draw.text((28,22),'ORIGINAL SOURCE-ASSET PREVIEW / not an Unreal render',fill='#ded6c4')
forward=unit((.45,.89,-.18)); right=unit(cross(forward,(0,0,1))); up=cross(right,forward)
light=unit((-.4,-.8,1.4))
projected=[(330+dot(p,right)*3,740-dot(p,up)*3,dot(p,forward)) for p in v]
order=sorted(f,key=lambda face:sum(projected[i][2] for i in face)/3,reverse=True)
for face in order:
    a,b,c=(v[i] for i in face)
    normal=cross(tuple(b[k]-a[k] for k in range(3)),tuple(c[k]-a[k] for k in range(3)))
    if sum(n*n for n in normal)<1e-18: continue
    normal=unit(normal)
    value=.24+.76*max(0,dot(normal,light))
    color=tuple(int(n*value) for n in (220,152,77))
    draw.polygon([projected[i][:2] for i in face],fill=color)
draw.text((90,815),'CONTINUITY / three swept bronze ribbons',fill='#ded6c4')
draw.text((90,837),'Source geometry: 116 x 63 x 195 cm',fill='#a6a094')
for i,name in enumerate(['T_Chromatic_01','T_Chromatic_02','T_Chromatic_03','T_ContourField','T_QuietTerrain']):
    thumb=Image.open(BASE/'Textures'/f'{name}.png').convert('RGB')
    thumb.thumbnail((230,330))
    col=i%3; row=i//3
    x=660+col*250; y=90+row*415
    canvas.paste(thumb,(x,y))
    draw.text((x,y+340),name,fill='#d4cbbb')
label=Image.open(BASE/'Textures'/'T_Label_06.png').convert('RGB')
label.thumbnail((500,150)); canvas.paste(label,(700,740))
path=BASE/'SourcePreview.png'; canvas.save(path)
print(path)
