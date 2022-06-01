-- author: ps
-- title: the chasm
-- desc: executable graphics for lovebyte 2022

-- https://twitter.com/AkiyoshiKitaoka/status/1409841093324144646/photo/1

for i=0,15 do
	poke(0x03FC0+i*3+0,i*(155/15))
	poke(0x03FC0+i*3+1,0)
	poke(0x03FC0+i*3+2,i*(255/15))
end

function TIC()
cls(15)
t=time()
s=math.sin(t/1000)*9
c=math.cos(t/1000)*9

for x=-10,39 do
 for y=-10,32 do
		circ((y%2)*4+x*8,
						 y*5,
							2,
							0)
 end
end

len = 16*3
sx = 120-len
gratio = 0.5

for x=0,len do
for y=0,136 do
	p = pix(x+sx,y)
	pt = p-(x)*gratio
	if (pt < 0) then pt = 0 end
	pix(x+sx,y,pt)
	
	p=pix(x+sx+len,y)
	pt = p-(len-x)*gratio
	if (pt < 0) then pt = 0 end
	pix(x+sx+len,y,pt)
end
end




end
