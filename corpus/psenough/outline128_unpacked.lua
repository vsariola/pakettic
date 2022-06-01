-- title:  outline 128b
-- author: ps
-- desc:   128b intro for Outline 2021
-- script: lua

t=0
x=240

function TIC()

cls()

for i=0,90 do
circb(
	x/2,
	68,
	80+math.sin(t/x+i)*80,
	i)
end

--if math.sin(t*0.1)>.95 then
--	rect(0,48,x,40,0)
--	rect(100,0,40,136,0)
poke4(x*136+t%301,t%15)
--end


--memcpy(0x4000,0,x*69)

--d=3 --math.floor(s(t*10)*2)

--memcpy(x*d,
--						0x4000,
--						x*64-x*d)


--if a(s(t*40))<.95 then
--cls(0)
--line(0,0,x,0,0)
--rect(x/2-20,0,40,y,0)
--end

memcpy(0xFF9D,0,x)

--for i=0,71 do 
--	poke(65438+i,math.random()*8+v)
-- poke4(2*65434+i,ms)
--end

t=t+1
end
