-- author: ps
-- title: the untz untz untz
-- lang: lua
-- desc: 512b intro for lovebyte'22


n={
--1 4 smileys
	function(t,x,y)
		i=5
		n[i](t,60,34)
		n[i](t,180,34)
		n[i](t,60,102)
		n[i](t,180,102)	
	end,
--2 worm
	 function(t,x,y)
		for i=8,14,.01 do
			 circ(x+math.sin(t/3+i)*i*3,
				 				y+math.sin(t/4+i)*i*3,
					 		 math.sin(11+i)*i*1.5,
						 		(t/3+i)%8+8)
		end
	end,
--3 spinner
	 function(t,x,y)
		for i=0,360 do
		for j=0,60 do
		pix(x + math.sin(t/20+i)*(20+j),
						y + math.sin(t/10+11+i)*(20+j),
		 			i*2%8+8)
		end
		end
	end,
--4 wave plasma
	 function(t,x,y)
		for i=-60,60,1.5 do
			for j=-40,40,.5 do
				z = math.sin(j/8)
							+math.sin(t/20+i/8)*2	
				circb(y+i*4+j*8,
										y+i*2-j*2+z*2,
										2+z%3,
										z%7+8)
			end
		end
	end,
--5 smiley
 function(t,x,y) 
		circ(x,y,30,4)
		circ(x,y,20,0)
		circ(x,y-5,20,4)
		elli(x-10,y-10,4,7,0)
		elli(x+10,y-10,4,7,0)
	end,
--6 4 worms
	 function(t,x,y)
	 i=2
		n[i](t,60,34)
		n[i](t,180,34)
		n[i](t,60,102)
		n[i](t,180,102)	
	end,
--7 pseudo laser lines
	 function(t,x,y)
		for i=0,60 do
			line(x,y,
				x+math.sin(t/20+i*6)*i,
				y+math.sin(t/10+11+i)*34,
			 i%8+8)
		end
	end,
--8 untz
	function(t,x,y)
	 for i=0,2 do 
			print('untz',60+2,20+i*35+2,0,0,5)
			print('untz',60,20+i*35,12,0,5)
		end
	end,
--9 4 pseudo laser lines
	function(t,x,y)
		i=7
		n[i](t,60,34)
		n[i](t,180,34)
		n[i](t,60,102)
		n[i](t,180,102)
	end,
--10	rectangles
	function(t,x,y)
		rect(30+math.sin(t/20)*10,0,20,136,12+math.sin(t/4)*4)
		rect(180-math.sin(t/20)*10,0,20,136,12+math.sin(t/4)*4)
	 rect(0,20+math.sin(t/20)*10,240,20,12+math.sin(t/10+11)*4)
	 rect(0,96-math.sin(t/20)*10,240,20,12+math.sin(t/10+11)*4)
	end,
--11 plasma circles
	function(t,x,y)
		for i=0,360 do
		  for j=0,60 do
		 	circ(j%2*4+i*8,
								 j*4,
									2+math.sin(t/10+(i-15)/(j-16))*2,
									11+math.sin(t/10+(i-15)/(j-16))*2)
				end
		end
	end,
--12 rave
 function(t,x,y)
 	rect(18,40,215,53,12)
  rect(18,40,108,53,0)
  print('un',22,44,12,0,9)
		print('tz',130,44,0,0,9)
 end
}

t=0
function TIC()
-- increase time
t=t+1

-- hide mouse
poke(16379,1)

-- hack assign to make n[i] compress better
i=t//16%12+1

-- flash border
poke(16376,t//16%2*12)

-- offset screen
poke(16377+t//500%3,-t%16)

-- untz untz
sfx(0,-t%16, t&(15+t//500%3*20))

-- sequence
n[i](t,120,68)
--cls()
--n[11](t,120,68)
end
