TIC=function()
  cls()
  for h=0,4,2 do
    i=math.sin(h+time()/68)
    d=math.sin(h+time()/68+8)
    b=math.sin(h+time()/163)*9+18
    poke(16320+time()%48,time()%48*5)
    -- j=time()//1%48
    -- poke(16320+j,j%3*j*3)
    for m=0,5 do
      e=191363//8^m
      l=e%2-.5
      s=e//2%2-.5
      r=e//2//2%2-.5
      k=-s*i+d*l
      o=(-r*i+d*k+d)/(k*i+d*r+b)*733
      j=(l*i+d*s+i)/(k*i+d*r+b)*733
      e=110960//8^m
      l=e%2-.5
      s=e//2%2-.5
      r=e//2//2%2-.5
      k=-s*i+d*l
      f=(-r*i+d*k+d)/(k*i+d*r+b)*733
      t=(l*i+d*s+i)/(k*i+d*r+b)*733
      e=63777//8^m
      l=e%2-.5
      s=e//2%2-.5
      r=e//2//2%2-.5
      k=-s*i+d*l
      n=(-r*i+d*k+d)/(k*i+d*r+b)*733
      q=(l*i+d*s+i)/(k*i+d*r+b)*733
      g=(f-o)*(q-j)-(n-o)*(t-j)
      if g>0then
        tri(o+120,j+68,n+120,q+68,f+120,t+68,g^.3-2)
        e=238546//8^m
        l=e%2-.5
        s=e//2%2-.5
        r=e//2//2%2-.5
        k=-s*i+d*l
        n=(-r*i+d*k+d)/(k*i+d*r+b)*733
        q=(l*i+d*s+i)/(k*i+d*r+b)*733
        tri(o+120,j+68,n+120,q+68,f+120,t+68,g^.3-2)
      end
    end
  end
end
