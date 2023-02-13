--{
n={}
TIC=function()
  c=3e2*math.cos(n/3e2)
  --{
  for o=3e2,72,-1 do
    for m=72,-72,-1 do
      d=40+a[(n+o)%512+(m-c//1)%512*512+1]
      circ((m+c%1)/o*512+120,(d>70 and 70or d)/o*512-120,2,d>70 and 7+d/51+o/70or d+o/51+3-e+(o/2+d/4)%1)
      e=d
    end
  end
  n=1+n
  --}
end
--{!
a={}
for o=1,5 do
  --{
  for m=1,3e5 do
    n[m]=math.random()
  end
  e=512//2^o
  --}
  for m=1,3e5 do
    d=n[m//2^o%e+m/512//2^o%e*e+1]+m%2^o/2^o*(n[(m//2^o%e+1)%e+m/512//2^o%e*e+1]-n[m//2^o%e+m/512//2^o%e*e+1])
    a[m]=(a[m]or 0)+2^o*(d+m/512%2^o/2^o*(m%2^o/2^o*(n[(m//2^o%e+1)%e+(m/512//2^o%e+1)%e*e+1]-n[m//2^o%e+(m/512//2^o%e+1)%e*e+1])-d+n[m//2^o%e+(m/512//2^o%e+1)%e*e+1]))
  end
end
--}
n=1
--}
-- <PALETTE>
-- 000:1a1c2c5d275db13e53ef7d57ffcd75a7f07038b76425717929366f3b5dc941a6f673eff7f4f4f494b0c2566c86333c57
-- </PALETTE>
