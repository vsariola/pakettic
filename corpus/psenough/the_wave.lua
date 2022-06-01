-- title:  the wave
-- author: ps
-- desc: executable graphics for lovebyte 2022
-- script: lua

t=0
x=240
y=136
sq=16/2
dx=15*2
dy=8*2

function TIC()

for i=0,dx do
for j=0,dy-1 do
rect(i*sq,j*sq,sq+1,sq+1,(i+j)%2+5)
end
end

plot={0,1,0,0,1,0,1,1}

for i=1,dx-1 do
for j=1,dy-1 do
--tt=1--math.sin((i-j)%8+t*0.75)+1
--circ(i*sq,j*sq-2,tt,plot[(i-j)%8+1]*10+2)
--circ(i*sq-2,j*sq,tt,plot[(i-j)%8+1]*10+2)
--circ(i*sq+2,j*sq,tt,plot[(i-j)%8+1]*10+2)
--circ(i*sq,j*sq+2,tt,plot[(i-j)%8+1]*10+2)

--circ(i*sq,j*sq,tt,plot[(i-j+1)%8+1]*10+2)
c=plot[(i-j+1)%8+1]*10+2
pix(i*sq,j*sq,c)
pix(i*sq-1,j*sq,c)
pix(i*sq-1,j*sq-1,c)
pix(i*sq,j*sq-1,c)

end
end


t=t+1
end
