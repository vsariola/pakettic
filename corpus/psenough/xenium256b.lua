-- title: xenium 256b
-- author: ps
-- desc: 256b intro for xenium 2021

w=240
e=180
v=120
cls(12)
function TIC()
	t=time()//32

	for i=0,71 do 
		poke(65438+i,math.random()*18+v)
	end

	for x=0,w do
	pix(math.sin(x)*x,0,(t>>3~t%12)%4+7)
	end

	Q=0x4000+math.sin(t*.1)*6
	memcpy(Q,0,w*e)
	p=(math.sin(t+e)*2+1)/1
	q=(math.sin(t*.1+e)*1+1)//1
	memcpy(w*q,Q+p*e,v*133)
	spr(0,0,1,0,8,0,0,8,5)
	
	print("xenium",0,5,7,0,p*q)
end

function SCN(s)
 poke(0x3fc0+s,math.random()*255)
end