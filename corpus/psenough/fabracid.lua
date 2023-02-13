-- title: Fabracid
-- author: ps + luchak
-- desc: 1kb intro for Lovebyte 2023
-- license: MIT License
-- script: lua

frame=0
-- filter ladder stage outputs
a=0
b=0
c=0
d=0
-- filter feedback highpass output
z=0
cutoff=0
pitch=1
kick=0
hat=0
snare=0

se={"hard","bass","drop","acid","more","trip","fabr"}

--tunnel,lemons,text,balls,smiley
r={
{0,1,1,0,1},
{0,1,1,0,1},
{0,1,1,1,1},
{0,0,1,0,0},
{1,1,0,1,0},
{1,1,1,0,0,0}, --reused for sound
{1,0,0,1,0},
{0,0,1,0,0}
}

st=0

function TIC()
 --{
 -- hide mouse cursor
	poke(16379,1) 
	-- scene tracker
	st=(frame//25600+hat//1%2+snare//1%2*2)%8
 -- border color
 poke(0x3ff8,d)
 --}
 
	if r[st+1][1]>0 then
		-- tunnel effect, originally by pestis
		--for s=0,32640 do
		for s=time()%6,32640,6 do
			t=s%240-120
			o=s/240-70
			n=math.atan2(o,t)
			rs=(2+math.sin(3*n+time()/200))/(t*t+o*o)^.5*10
			poke4(s,math.sin(n*6+math.sin(rs*20+snare))^2/rs)
		end
	else
 	cls(d)
 end

 for x=1,11 do
		-- floating lemons
		if r[st+1][2]<1 then
			for y=2,11 do
				circ(x*20,y*10,
				10+math.sin((x-6)*math.sin(time()/1e3)+(y-6)*math.cos(time()/1e3))*10,
				(x-time()/100)%d*4)
			end
		end
	
	 -- floating text
		if r[st+1][3]>0 then
		 print(se[time()//200%7+1],
				5,
				40+st%3*20*math.sin(time()/500+x*d/50+st%3*x/2),
		  x/2*d,0,10)
		end
	end
	
 -- audio
 --{
 poke(0xff9d,0xd0)
 poke(0xff9c,60*pitch)
 poke(0xffaf,(15*(kick/500+.6)//1)<<4)
 poke(0xffae,kick)
 poke(0xffc1,((hat/28//1)<<4)+0xf)
 poke(0xffc0,0x80)
 poke(0xffd3,((snare/28//1)<<4))
 poke(0xffd2,0x80)
 -- filter decay, LFO for subtle variation
 cutoff=cutoff*(.88-.04*math.sin(frame/7e3))
 --}
 
 -- percussion envelopes
 -- kick pitch and amplitude env are the same var
 --{
 kick=kick*.8
 hat=hat*.6
 snare=snare*.8
 --}
 for i=0,31 do
  if frame%200==0 then
   step=frame//200
   bar=step//16
   phase=bar//8
   section=(phase//2)%4
   phase=phase%2
   next_pitch=(({.9,.9,1,1,1,1,1,1.05,1.8,2,2,2,2,2.1,3,3.6,4,4.2})[math.random(18)])*(r[6][math.random(4+2*(step&1))])
   --[[
   next_pitch=({
    1,2,0,1,1,0,.9,0,
    2,0,1,0,4,0,2.1,0,
    1,1.05,0,2,1,0,.9,0,
    2,0,1,0,4.2,0,3,0
   })[step%((step%256<112 and step%256>96) and 8 or 32)+1]
   --]]
   if next_pitch>0 then
    cutoff=.011*(7+2*section)-.05*math.sin(frame*6.2832/48640)
    pitch=next_pitch
   end
   if step%4==0 and step//16%8<7 then
    kick=200
   end
   if section>1 and step%2==1 and step//128%2==1 then
    hat=80
   end
   if ((step%4==2) ~= (math.random(40-2*section)==1)) and step//128%2==1 then
    hat=255
   end
   if (step%8==4 or math.random(80-4*section)==1) and section>0 and phase>0 then
    snare=200
   end
  end
  v=frame%32/16-1
  -- ridiculous 32x oversampling
  for j=0,31 do
   -- constant below is the filter resonance
   a=a+cutoff/pitch*(v-(2.3+.1*section)*(d-z-v)-a)
   b=b+cutoff/pitch*(a-b)
   c=c+cutoff/pitch*(b-c)
   d=d+cutoff/pitch*(c-d)
   z=z+((d-z)/64)
  end
  
  --{
	 -- set bass waveform
	 poke4(0xff9e*2+i, math.max(0,math.min(d*6+8,15)))
	 -- set kick waveform (could be done elssewhere)
	 poke4(0xffb0*2+i, 8+8*math.sin(6.2832*i/32))
	 frame=frame+1
  --}
  
		-- twirl balls
		if r[st+1][4]>0 then
		circ(120+math.sin(time()/500+i*10)*80,
			(i*6-time()/10)%150-10,
			math.sin(time()/500+i)*5*(st%2)+5+kick,
			5+math.sin(i)+frame*(st%2))
		end
	
	 -- circles from center
		--[[
		if r[st+1][5]>0 then
			circb(120,
			 68+math.sin(time()//200%9)*10*r[st+1][3],
			 i/math.sin(time()/3e4)*4,math.sin(i+time()/200))
 	end
  --]]
 end

	-- smiley
	if r[st+1][5]>0 then
		--{
		x=math.sin(time()/1e3+kick/200*st%3)*80+120
		y=math.cos(time()/3e3*pitch)*30+70
		--}
		circ(x,y,30,4)
		circ(x,y,20,0)
		circ(x,y-5+2*math.sin(pitch),20,4)
		--{
		elli(x-8,y-10,3,6,0)
		elli(x+8,y-10,3,6,0)
		--}
 end

end


function BDR(l)
	--{
	poke(0x3ffa,math.sin(time()/800+l/32)*math.sin(time()/400+l/64)*snare)
	poke(0x3ff9,math.sin(time()/1e3+l/32)*math.sin(time()/1e3)*snare)
 --}
 
 for i=3,st%2*13 do
		-- random color brightness ramp
		poke(0x3fc0+time()//1e3%6*i,255)
		-- gradient palette touches
		poke(0x3fc0+i*4,l+st%4*math.sin(l*120+time()/150)*10+10)
	end
	
	-- pixelated bar on first colors
	poke(0x3fc0+time()/2000%9,
	 st%2*math.sin(l*5+time()/3e4)*time()/500+st%3*time()/10
	)
end
