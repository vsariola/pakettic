-- title:  liquid cool
-- author: ps
-- desc:   256b intro for cc 2021
-- script: lua

t=0

function TIC()
	t=time()//32
	
	for x=0,40 do
		for y=0,22 do
			l=math.cos(math.abs(x-20)-math.abs(y-10)*t*0.01)%3
			rect(x*6,y*6,6,6,math.abs(4-(l*6))%3)
			poke4(2*65438+x,math.cos(l))
		end
	end
	
	print("liquid cool",6,120,12,0,2,0)
	
	if (t%4>2) then
	poke(65437,(t/65536)%16+240)
	end
end

function SCN(s)
poke(0x3fc0,256-(math.cos(t*0.1)*s*.5+100))
poke(0x3fc3,256-(math.cos(t*0.1)*s*.5+120))
poke(0x3fc4,0)
poke(0x3fc5,0)
poke(0x3fc6,math.cos(t*0.05)*s*.5+180)
end