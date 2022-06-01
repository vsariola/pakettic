-- title:  travelling without moving
-- author: ps
-- desc:   256b intro for JML 2021
-- script: lua

u=15

function TIC()
	cls(1)
	poke(0x03FF8,1)
	for x=0,10 do
		rect(8+x*24,8,8,120,6)
		for y=0,u do
			thx = 8+x*24
			thy = 8+y*8
	
			-- horizontal line
			line(thx,thy,thx+8,thy,((y-1)%2)*u)
			
			-- left line
			if (y < u) then
				line(thx,thy+1,thx,thy+8,((x+y+1)%2)*u)
				line(thx+8,thy+1,thx+8,thy+8,((x+y)%2)*u)
			end
			
		end
	end
end

function SCN(l)
t=time()/120
s=math.sin(t*2+l/2)*44+168
for c=0,2 do
poke(0x03FC0+c,s)
poke(0x03FED+c,120-s)
end
poke(0x03FC3,225-l/2+math.sin(t/2-l/4)*u)
poke(0x03FC4,225-l)
poke(0x03FC5,0)
poke(0x03FD3,math.sin(t+l/u)*44+168)
end