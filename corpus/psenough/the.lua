-- title: the 128b
-- author: ps
-- desc: 126b intro for lovebyte battlegrounds 2021

function TIC()
s=time()/1e4
 for i=0,1e5 do
  a=i%136
  d=i%241
		m=a-s*2
		pix(d,a,(((d*d+a*a)//241~(d*d+m*m)//241)%2)*12)
	end
print("THE 128b",70,60,0,0,2)
end