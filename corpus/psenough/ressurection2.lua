-- title:  ressurections
-- author: ps
-- desc:   256b intro for Lovebyte Battlegrounds 2021
-- script: lua

a = {}
l = {}
for y=0,17 do
	poke(0x03FC0+y*3  ,y*y*y*y/16/16)
	poke(0x03FC0+y*3+1,y*16)
	poke(0x03FC0+y*3+2,y*y*y*y/16/16)
 a[y] = {}
 l[y] = math.random(30)
 for x=0,30 do
 	a[y][x] = math.random(16)
	end
end

t=0

function TIC()
cls(0)
--a[math.random(17)-1][math.random(30)] = 16

for y=0,16 do
 for x=0,30 do
	 	if (t%8 == 0) and (a[y][x] > 1) then		
				a[y][x] = a[y][x] - 1		
			end
			c=(x*y+2*y+x*3)%60+40
			if a[y][x] > 14 then
				 c=math.random(40,102) end
 		print(string.char(c),x*8,y*8,a[y][x])
	end

--if y < 6 then
	m = (t//(y/2+5)+y*3)%18
	if (m == 17) then l[y] = math.random(30) end
	a[m][l[y]] = 15
--end

end

t = t+1
end
