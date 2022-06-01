-- title:  inercia water worm
-- author: ps
-- desc:   256b intro for Inercia 2021
-- script: lua

pal={9,9,9,1,10,10,10}
poke(0x03FF8,12)
function TIC()
 cls(12)
	t=time()/200
	for p=0,14,.01 do
	 circ(120+math.sin(p+t/3)*(p*6-8+math.sin(t)*20),
		 				68+math.sin(p+t+1)*(p*3-8+math.sin(t)*10),
			 			math.abs(math.sin(p+t)*p*2.5),
				 		pal[p*17%8//1])
		--poke(0x0FF9C+p*2*(timer%2),math.sin(t+p)*20)
	end
	print'inercia water worm'
	for a=0,46 do
		x=math.random(240)
		y=math.random(136)
		w=math.random(20)
		line(x,y,x+w,y,pix(x,y))
		line(x,y+1,x+w/2,y+1,pix(x,y))
		poke(0x0FF9C+t//1.5%2*a,math.sin(t+a)*99)
	end
	
end
