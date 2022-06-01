-- title: Inercia 512b
-- author: ps
-- desc: 512b intro for Inercia Demoparty 2021
-- script: lua

cls()s={                                                 
			{0.2 ,0,1,1,1, 0, 0, 0, 1,1, 1,0,''},
			{1 ,0,1,1,1, 0, 0, 0, 1,1, 1,0,''},
			{4   ,0,1,1,1, 0, 0, 0, 0,1, 1,0,'(c) 1982 Sinclair Research Ltd'},
			{5   ,0,1,1,1, 0, 0, 0, 0,1, 1,1,'LOAD '},
			{5.5 ,0,1,1,1, 0, 0, 0, 0,1, 1,1,'LOAD "'},
			{7 ,0,1,1,1, 0, 0, 0, 0,1, 1,1,'LOAD ""'},
			{11  ,0,0,1,1, 1,-1,-1,12,2, 1,0,''},
			{14  ,0,0,1,1,-1, 1, 1,12,7,10,0,''},
		 {14.2,1,0,0,1,-1,-1, 1,12,7, 4,0,'Program: 512b'},
			{16  ,0,0,1,1, 1,-1,-1,12,2,10,0,'Program: 512b'},
		 {18  ,0,0,1,1,-1, 1, 1,12,7,10,0,'Program: 512b'},
			{200 ,1,1,1,1, 0, 0, 0, 0,1, 1,0,'R Tape loading error, 0:1'},
			{201 ,1,1,1,1, 0, 0, 0, 0,1, 1,0,'R Tape loading error, 0:1'},
		}
i=1
function TIC()
 -- hide mouse
 poke(16379,1)
 
	--for i=1,12 do
  -- timeline
		--if time()/1e3>s[i][1] and time()/1e3<s[i+1][1] then
			
			-- background, only sometimes cleared
			rect(i%13//8*255+20,20,200,96,s[i][9])
			
			-- print string
			L=print(s[i][13], 21, 21+89*s[i][3], 1, true)
			
			-- cursor
			rect(L+21, 20+89*s[i][3],
								7*s[i][12],	7,
								time()*s[i][12]//400%2-1)
			print('L',L+22,
													1021+89*s[i][3]-s[i][12]*1e3,
													time()*s[i][12]//400%2)
			
			-- math for loading sound
			L = math.sin(s[i+1][2]*1920)*99 +
			    math.sin(s[i][2]*960)*(time()%3//2<<5)
			
  	if 82>>i&1>0 then
   	for j=0,71 do
     -- vertical lines on first screen
     -- here to reuse the j loop
     rect(1e3-i*979+j%33*6,20,1,96,2)
     -- click sound
 				poke(65436+j,200-j%2*200-1)
			 end
			end
				
  --end
 -- loading sound 
	--poke(65436+i%9,L)
	memset(65436,L,9)
	--end
		i=i+time()/1e3//s[i][1]|0

end


function BDR(...)
	--for i=1,12 do
		--if time()/1e3>s[i][1] and time()/1e3<s[i+1][1] then
		 for j=0,6 do
			poke(16320+j,(1-j%6//3)*255*(s[i][j+3]-s[i][j+6]*((...-time()/s[i][10])//s[i][11]%2)))
 		--poke(16320+j,(1-j%6//2)*255*(s[i][j+3]-s[i][j+6]))
   end
		--end
	--end
end
