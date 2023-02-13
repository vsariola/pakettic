-- title: pollen
-- author: Gasman / Hooy-Program
-- desc: a graphic demo live coded for aldroid's bytejam, 02.09.2021
-- script: lua

for i=0,48 do
  poke(0xcfc0+i,peek(0x3fc0+i))
end
function SCN(y)
for i=0,48 do
  poke(0x3fc0+i,peek(0xcfc0+i)*math.abs(math.sin(t/32+y/48)))
end
end
function TIC()t=time()//32
m=math
for y=0,136 do for x=0,240 do
pix(x,y,
peek(0x6000+(
  x%120+(t//1+(y*240)//1)%0x4000)
)%16/2)
end end
circ(32,32,32*m.sin(t/8),7)
circ(208,104,32*m.cos(t/8),8)
circ(32,104,32*m.sin(-t/8),7)
circ(208,32,-32*m.cos(t/8),8)
x=120+64*m.sin(t/45)
y=68+64*m.sin(t/57)
for i=0,16 do
a=t/40+i
b=t/45+i
c=t/57+i
tri(x+64*(m.cos(a)+m.sin(a)),y+64*(m.cos(a)-m.sin(a)),
x+64*m.sin(b),y+64*m.cos(b),
x+64*m.sin(c),y+64*m.cos(c),
(t/4)%8+8)
tri(x-64*(m.cos(a)+m.sin(a)),y+64*(m.cos(a)-m.sin(a)),
x-64*m.sin(b),y+64*m.cos(b),
x-64*m.sin(c),y+64*m.cos(c),
(t/6)%8+8
)
end
memcpy(0x6000,0x0000,0x4000)
end
