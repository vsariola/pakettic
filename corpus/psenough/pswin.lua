-- title:  intergalactic geodesic transmutation
-- author: ps
-- desc:   256b intro for Lovebyte 2021
-- script: lua

h=136
w=256
b=0x03FF8
a=16
j=w*w
t=time()

function TIC()

f=math.floor
s=math.sin
r=math.random(-4,4)
q=time()
d=q/64
p=d/8
o=12
poke(b,f(p)%2*2)
o=f(d)%2*o
cls()

if (q-t<j/4) then

cls(o)
poke(b,o)

k=j-100

poke(k,d%w)
poke(k+1,(d/j)%a+w-a)
poke(b+1,r)
--poke(b+2,r)
for y=1,3 do for x=0,32 do
rect(
x*8 + s(d/a+y/2)*o - a,
y*a + s(d/y+x)*4 - s(p)*y*4+o,
w/a,
h/3-y*s(y+p)+s(y+p)*4,
(1+x+y+d)%4+8)
end
end
end
end
