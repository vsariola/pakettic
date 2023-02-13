TIC=function()
  for p=0,32160 do
    q=0
    for m=0,24 do
      q=q+peek4(p+m//5*240+m%5-482)
    end
    poke4(p,q/24-math.random()/2)
  end
  circ(math.random(176)+32,math.random(76)+32,math.random(24),-1)
end
-- <PALETTE>
-- 000:1a1c2c5d275db13e53ef7d57ffcd75a7f07038b76425717929366f3b5dc941a6f673eff7f4f4f494b0c2566c86333c57
-- </PALETTE>
