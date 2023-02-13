-- greetings earthlings!
-- gasman here
-- have a nice jam everyone!
m=math
s=m.sin
c=m.cos
k=0

function SCN(y)
 for i=0,2 do
  poke(16320+i,y/2*i)
 end
end

lastbp=0
p=0
function TIC()t=time()
 -- I like the long trail more
 k=(k+1)%32
 for y=0,135 do
  for x=0,239 do
   if (x~y)&31==k then
    pix(x,y,0)
   end
  end
 end

 b=t/1000
 r=50
 bp=(t/534)%(m.pi)
 if bp>=m.pi/2 and lastbp<m.pi/2 then
  p=(p+1)%3
 end
 lastbp=bp

 for i=3,47 do
  poke(16320+i,120+120*c(i*6+(i+p)%3))
 end

 by=80-80*m.abs(c(bp))
 if bp>m.pi/2 then
  d=(m.pi-bp)/(m.pi/2)
  sy=1+d*s(t/40)/4
 else
  sy=1
 end
 bx=(t/12)%480
 if bx>240 then
  bx=480-bx
 end

 for i=0,400 do
  a=i/5
  y0=s(a)
  x0=c(a)*s(t/500+i/2.3)
  z0=c(a)*c(t/500+i/2.3)
  y1=y0*c(b)+z0*s(b)
  z1=z0*c(b)-y0*s(b)
  y=by+sy*r*y1
  x=bx+r*x0

  for j=0,0.3,0.05 do
   y=by+sy*r*(j+1)*y1
   x=bx+r*(j+1)*x0
   circ(x,y,4-j*10,i)
  end
 end
end
