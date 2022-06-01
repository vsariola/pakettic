-- title:  Outline 256b
-- author: ps & mantratronic
-- desc:   256b intro for Outline 2021
-- script: lua

w=240
u=68
v=120
h=136
st=time()

function TIC()

dt = time()-st
a=dt*0.001
b=a*3
c=a*5
--dt = 0

ms = math.sin(a)*20
ts = math.sin(b)*30
mc = math.sin(c)*30

for i=0,71 do 
	poke(65438+i,math.random()*8+v)
 poke4(2*65434+i,ms)
end

memcpy(0x4000,0,v*h)

f=59
--cls(0)
for y=0,h-1 do
q=y*v
r=q+f
if y<u then
memcpy(r,   r-1+0x4000, f )
memcpy(q+v, q+w+0x4000, f )
else
memcpy(r, r-v+0x4000, f )
memcpy(q, q+1+0x4000, f )
end
end

--circ(v+ms,
--					u+ts,
--					8,a%8+8)
--circb(v+ms,
--					u+ts,
--					8,0)

circ(v+ms+mc+ts,
 				u+ts+mc/2,
					3+ts/2,b%8)
circb(v+ms+mc+ts,
					u+ts+mc/2,
 				3+ts/2,0)

end
