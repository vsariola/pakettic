-- title: Inercia 512b
-- author: ps
-- desc: 512b intro for Inercia Demoparty 2021
-- script: lua

-- only need to clear bg on 1st frame
cls()

-- timeline
s={                                                 
	{0   ,0,1,1,1, 0, 0, 0, 1,1, 1,0,1,''},
	{0.2 ,0,1,1,1, 0, 0, 0, 1,1, 1,0,0,''},
	{1   ,0,1,1,1, 0, 0, 0, 0,1, 1,0,0,'(c) 1982 Sinclair Research Ltd'},
	{4   ,0,1,1,1, 0, 0, 0, 0,1, 1,1,1,'LOAD '},
	{5   ,0,1,1,1, 0, 0, 0, 0,1, 1,1,0,'LOAD "'},
	{5.5 ,0,1,1,1, 0, 0, 0, 0,1, 1,1,1,'LOAD ""'},
	{7   ,0,0,1,1, 1,-1,-1,12,2, 1,0,0,''},
	{11  ,0,0,1,1,-1, 1, 1,12,7,10,0,0,''},
	{14  ,1,0,0,1,-1,-1, 1,12,7, 4,0,0,'Program: 512b'},
	{14.2,0,0,1,1, 1,-1,-1,12,2,10,0,0,'Program: 512b'},
	{16  ,0,0,1,1,-1, 1, 1,12,7,10,0,0,'Program: 512b'},
	{18  ,1,1,1,1, 0, 0, 0, 0,1, 1,0,0,'R Tape loading error, 0:1'},  
	{200 ,0}
}

function TIC()
	-- hide mouse, thx to pestis and no thx to nesbox
 	poke(16379,1)
 
	for i=1,12 do
  		-- enact timeline
		if time()/1e3>s[i][1] and time()/1e3<s[i+1][1] then
			
			-- zx spectrum background, smaller then our viewport, to ensure big fat borders like the spectrum
			-- it's only sometimes cleared, just to get the 2 texts on the final scene of the r tape loading error 
			rect(i%13//8*255+20,20,200,96,s[i][9])
			
			-- print string
			-- using highcase L as variable name instead of random other letter
			-- saves 1 byte thanks to packer entropy heatmap shenanigans, since it's already used as a char a few times elsewhere
			L=print(s[i][14], 21, 21+89*s[i][3], 1, true)
			
			-- cursor background
			-- only shows up when s[i][12] is 1
			rect(L+21, 20+89*s[i][3],
				7*s[i][12],
				7,
				time()*s[i][12]//400%2-1)
			
			-- cursor letter
			-- multiplying by 1000 and subtracting 1000 is to ensure it's printed outside the screen when the timeline says it shouldnt be printed
			-- it's less bytes then having and if statement
			print('L',L+22,1021+89*s[i][3]-s[i][12]*1e3,time()*s[i][12]//400%2)
			
			-- math for the 2 parts of the loading sound
			-- blue and yellow sounds a bit weird couz it's not using math.random and accurate behavior of double wavelength distinction between 1 and 0
			-- proper spectrum sound implementation of that part is left as an exercise for the reader
			L = math.sin(s[i+1][2]*1920)*99 +
			    math.sin(s[i][2]*960)*(time()%3//2<<5)

		-- click on	
  		if s[i][13]==1 then
   		 for j=0,71 do
     			-- vertical red/yellow lines on first screen
     			-- placed here to reuse the j loop
     			rect(1e3-i*979+j%33*6,20,1,96,2)
     			-- click sound itself
 			poke(65436+j,200-j%2*200-1)
		 end
		end
				
  	end
	
	-- loading sound, not using the whole audio registry which makes the waveform sound dirty so i rolled with it
	-- makes the math of L all weird but hei, trial and error worked to find the right tune, more or less
	-- one day i'll learn proper sound programming instead but not today
	poke(65436+i%9,L)
	end
end

function BDR(...)
	for i=1,12 do
		-- enact timeline
		if time()/1e3>s[i][1] and time()/1e3<s[i+1][1] then		
		 	-- first 3 are RGB of color 0, used for the border effect changes
			-- second 3 are RGB of color 1, which needs to be black, used to print sentences
			-- extra 2 are causing the yellow interferance on the default red that is color 2, used only on the boot screen 
			for j=0,7 do
			 poke(16320+j,(1-j%6//3)*255*(s[i][j+3]-s[i][j+6]*((...-time()/s[i][10])//s[i][11]%2)))
 			end
		end
	end
end
