d=0
TIC=function()
  d=d+1
  for c=0,32402 do
    --{
    m=d+4e4//(1+(c//240-63)^2+(c%240-120)^2)
    o=d-40*math.atan(c%240-120,c//240-63)//1
    poke(c%48+16320,c%48*6*math.sin(c)^2)
    -- poke(f%48+16320,6*(f%48)*math.sin(f+m/240)^2)
    n=peek4(c+48124)
    --}
    poke4(c,(c+6)%240>12 and(3>(-o+m~o+m)%90 and n+6or n))
    -- poke4(f,12<(f+6)%240 and(3>(-d+c~d+c)%(m//240+63) and n+6or n))
  end
  e=math.random(16)
  poke4(62402,e%8)
  for p=0,11 do
    for b=0,11 do
      f=11-p-b+240*(b-p)
      for m=f>0 and 0or 18,f>0 and 18or 0,f>0 and 1or-1 do
        for o=f>0 and 0or 18,f>0 and 18or 0,f>0 and 1or-1 do
          c=o+33000+e+19*b+240*(m+e+19*p)
          poke4(c,peek4(c+f))
        end
      end
    end
  end
end
