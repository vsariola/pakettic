-- title:  approved by the leprechaum committe
-- author: ps
-- desc:   256b intro for nevoke 2021
-- script: lua

t=0
c=math.cos

function TIC()
t=time()//32

for x=0,40 do
	for y=0,22 do
		l=c(math.abs(x-20)-math.abs(y-10)*t*0.01)%3+3
		rect(x*6,y*6,6,6,l*4)
		poke4(2*65438+x,c(l)) 
	end
end

rect (0,106,256,20,15)
print("approved by the leprechaum committe",c(t*0.05)*74-20,110,14,0,2,0)
print("approved by the leprechaum committe",c(t*0.05)*74-21,110,5,0,2,0)

if (t%4>2) then
poke(65437,(t/65536)%16+240)
end
end


function SCN(s)
poke(0x3fc1,t)
poke(0x3fc2,t)
end