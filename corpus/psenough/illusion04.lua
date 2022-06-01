-- title:  illusion04
-- author: ps
-- desc:   256b for Flashparty
-- script: lua

function TIC()
t=time()/128
cls(12)
poke(0x03FF8,12)

for x=0,14 do
	for y=0,14 do
		rect(x*9+52,y*9,9,9,((x+y)%2)*12)
		--if (math.abs(x-7)/math.abs(y-7) < math.sin(t*0.1)*3+1) then
		--if math.abs(x-7) > (128-t)%8 then
		defx = math.floor(math.sin(t+y)/(y+1))%2		
		defy = math.floor(math.sin(t+x)/(y+1))%2		
		 rect(x*9+53+5*defx,
								y*9+1+5*defy,2,2,
								((x+y+1)%2)*12 )
--			rect(x*w+(240-s*w)/2+1+5*defy,
--								y*w+1+5*defx,2,2,
--								((x+y+1)%2)*12 )
		--end
	end
end

memcpy(0xFF9C,math.floor(math.sin(t*2)),(t%8)*8)

for i=11,99 do
r=5+math.sin(i)*4
c=i%3+13
x=math.sin(i*9+t*.01*(9-r)+c)*12
y=9*i%120+8

circ(25+x,y,r,0)
circ(26+x,y,r,c)
circ(214-x,y,r,0)
circ(213-x,y,r,c)
end

end
