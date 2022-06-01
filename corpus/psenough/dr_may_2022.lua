-- title:  demoscene report may 2022
-- author: ps
-- desc:   intro for demoscene report may 2022
-- script: lua

poke(16323,255)
poke(16324,117)
--poke(0x3FC5,0x65)
poke(16320,186)
poke(16321,240)
poke(16322,4)
cls(12)
function TIC()
t=time()/32
Q=16384 + math.cos(t*.15)*3

memcpy(480,Q,15840)

--poke(16376,2)
for x=0,40 do

--		rect(x*6,0,3,x,t~x%16)
	for y=0,20 do
	 rect(x*6,0,4,3,
		math.cos(math.abs(x-20)-y*t*.03)%2
	 )
		--tri(x*6-t%6,y*6,x*6-t%5,y*6+2,x*6+2-t%6,y*6,
		--		 math.cos(math.abs(x-20)-math.abs(y-20)*t*0.1)%2+10
		--)
	 line(0,y*4,240,y*4,0)
	end
	
end

memcpy(Q,0,16320)
memcpy(480,Q,15840)

--for y=0,1 do
print("Demoscene",240-t*2%410,20,1,2,3)
print("Report",266-t*2%410,45,1,2,3)
print("May",t*2%410-100,70,1,2,3)
print("2022",t*2%410-108,95,1,2,3)
--end

end
