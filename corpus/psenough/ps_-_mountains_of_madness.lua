-- title:   mountains of madness
-- author:  ps
-- desc:    256b executable gfx for lovebyte 2023
-- license: MIT License (change this to your license of choice)
-- version: 0.1
-- script:  lua

function TIC()

  math.randomseed(0)
  vbank(1)
  cls(1)
  circ(136,120,20,0)
  
  for i=20,-10,-2 do
  	--{
   w=70+i*2+math.random(3)
   h=60-math.sin(i*5+math.random(8))*30
   --lx=20+i*12
   --}
   
   --[[
   tx1=lx+w*.33
   tx2=lx+w*.5
   tx3=lx+w*.67
   --]]
   
   --px =tx2
   --ex =lx+w
   
   
   --ly =136
   --py =ly-h
	  --ey =ly
   tri(20+i*12,136,
	      20+i*12+w/2,136-h,
	      20+i*12+w,136,
	      12)
   
   --[[for d=.67,.27,-.20 do
	   
	   ty1=136-h*d
				c=16-d*5//1
				--]]
				
			for d=1,3 do

	   --ty1=136-h*((3-d)*.2+.27)
				--c=16-d
				
	   --{
	   tri(20+i*12,136,
	   				20+i*12+w/3,136-h*.87+h*d/5,
	       20+i*12+w,136,
	       16-d)
	  	
	   tri(20+i*12,136,
	   				20+i*12+w/2,136-h*.87+h*d/5,
	       20+i*12+w,136,
	       16-d)
	
	   tri(20+i*12,136,
	   				20+i*12+w/3*2,136-h*.87+h*d/5,
	       20+i*12+w,136,
	       16-d)
				--}
	  end
  
   elli(i*84%240,w-50,h*.4+w,w/5,13+i%3//2)
   elli(i*12%240,w-51,h+w,w/5,14+i%3)
   
  end
  vbank(0)
  cls(4)
  --circ(130,120,20,0)
  vbank(1)
end

function BDR(l)
	--for i=3,3 do
		vbank(1)
		poke(0x3fc3,136+l*2)
		vbank(0)
		poke(0x3fcd,80+l/9)
	--end
end


