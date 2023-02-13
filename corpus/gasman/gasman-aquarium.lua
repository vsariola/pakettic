m=math
bx={}
by={}
for i=1,32 do
bx[i]=m.random(240)
by[i]=m.random(136)
end
ffx={}
ffy={}
for i=1,4 do
ffx[i]=m.random(320)
ffy[i]=m.random(40)
end
function TIC()
a=(time()/8000)%(2*m.pi)
for i=0,15 do
poke(0x3fc0+i*3,i*4)
poke(0x3fc1+i*3,128+i*8)
poke(0x3fc2+i*3,255)
end
poke(0x3fc0+45,0)
poke(0x3fc1+45,64)
poke(0x3fc2+45,32)

for y=0,136 do for x=0,240 do
y0=y+64*m.cos((x-120)/60)
yc=(y0-time()/100)
x0=x-120
x1=(x0)*m.cos(a)+yc*m.sin(a)
y1=yc*m.cos(a)-(x0)*m.sin(a)
x2=(x0)*m.cos(-a)+yc*m.sin(-a)
y2=yc*m.cos(-a)-(x0)*m.sin(-a)
r=m.sqrt(x0*x0+yc*yc)//8
v=(x1//8~y1//8)~(x2//8~y2//8)~r
v=(v%16)//1
if v>14 then v=14 end
pix(x,y,v)
end end
for i=1,32 do
circb(bx[i]+12*m.sin((time())/200+i),(by[i]-(i/4*time()/100))%136,5+3*m.sin(time()/40/i),14)
end
for f=1,4 do
fx=(time()/100 + ffx[f])%320-64
fy=8*m.sin(time()/500+f)+ffy[f]
tt=4*m.sin(time()/100)
elli(48+fx,48+fy,16,8,15)
tri(28+fx+tt,40+fy,36+fx,48+fy,28+fx+tt,56+fy,15)
end
end
