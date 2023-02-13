m=math
s=m.sin
c=m.cos
Q=0x3fc0
function TIC()t=time()/500
for p=3,47 do
poke(p+Q,p*(4+s(p/3+t/8)))end
cls()for i=t%4,130 do
x=80*s(t*1.1+i/40)+40*s(t*2)y=10*c(t+i/40)line(120-x,i-y,120+x,i+y,m.abs(x/12))
end end
function SCN(y)poke(Q+y%9,40*(1+s(y/8+t*4)))end