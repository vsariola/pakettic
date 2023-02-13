m=math
s=m.sin

l={}
for r=0,32 do
 l[r]={}
 for g=0,32 do
  l[r][g]={}
  for b=0,32 do
   t=6e6
   i=0
   for c=0,16 do
    cr=r*8-peek(c*3+16320)
    cg=g*8-peek(c*3+16321)
    cb=b*8-peek(c*3+16322)
    e=cr^2+cg^2+cb^2
    if e<t then
     t=e
     i=c
    end
   end
   l[r][g][b]=i
  end
 end
end

cls(1)
for y=5,7 do
 for x=1,3 do
   print("phazalea\n\n gasman\n@nordlicht",x,y,0)
 end
end
print("phazalea\n\n gasman\n@nordlicht",2,6,2)
n={}
for y=0,34 do
 n[y]={}
 for x=0,64 do
  n[y][x]=pix(x,y)
 end
end

function TIC()
 t0=time()
 t1=0
 if t0>15000 then
  t1=t0-15000
  t0=15000
 end
for y=0,136 do
dr=0
dg=0
db=0
for x=0,240 do
a=3*(s(x)+s(y))+(n[y//4][x//4]-1)*128*(1-t0/15000)^.5
cx=x-120
cy=y-68
q=m.atan2(cx,cy)
d=m.sqrt(cx*cx+cy*cy)
p=s(q*6+(t0+t1)/170)
r=m.max(0,m.min(255,(
 128+127*m.cos(
  d/(30+8*(
   p+s(q*5+(t0+t1)/500)+s((t0+t1)/400)
  )))+a
)-dr))
g=m.max(0,m.min(255,(
 128+127*m.cos(
  d/(30+8*(
   p+s(q*5+t0/500+t1/520)+s(t0/400+t1/401)
  )))+a
)-dg))
b=m.max(0,m.min(255,(
 128+127*m.cos(
  d/(30+8*(
   p+s(q*5+t0/500+t1/540)+s(t0/400+t1/402)
  )))+a
)-db))
c=l[r//8][g//8][b//8]
dr=peek(c*3+16320)-r
dg=peek(c*3+16321)-g
db=peek(c*3+16322)-b
pix(x,y,c)
end end end
