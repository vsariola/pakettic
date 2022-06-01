-- author: ps
-- title: The Silver Bullet
-- desc: 256b for lovebyte 2022

for i=0,15 do
	poke(0x03FC0+i*3,i*10)
	poke(0x03FC1+i*3,i*10)
	poke(0x03FC2+i*3,i*15)
end

function TIC()
t=time()

poke(0x3FFB,1)
--cls()

poke(0x3FF8,t%5+4+math.sin(t/1000)*4)

for x=-10,39 do
 for y=-10,32 do
		circb((math.sin(t/1000)
							-math.sin(t/1000+11))+x*9,
						 y*6+math.sin(t/1000)*2*y,
							3+math.sin(x*math.tan(t/1000)*2)*2,
							3+math.sin(y*x+t/500)*2)
 end
end

print('the',
	20,
	35+math.sin(t/1000+11)*30+t%3,
	4+math.sin(t/1000)*4,2,12)
	
for x=0,240 do
for y=t/4%136,t/3%136+10 do
	poke(65436+x,(t/x)+math.sin(t/1000)*4)
	pix(x,y,(pix(x,y)+y%3+(x+y)%3+math.sin(t/1000)*4))
end
end

end
