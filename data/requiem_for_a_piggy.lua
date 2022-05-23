t=2e9 -- start time from large value to distribute clouds
function TIC()
-- visuals:
	for z=1,9 do -- z=1 far, z=9 near
		y=239 -- star height of the mountains
		for c=0,y do -- loop over all columns
			r=math.sin(c) -- ~ random value
			x=r*z*t/40%302-30 -- move near clouds faster
			rect(c,y/2,1,y,0) -- draw mountains
			circ(x,z*21+c-30,17+r*9,-z) -- clouds
			y=y+6*math.sin(r*199) -- randomness to mountains
		end
		print("v",x,z*8) -- draw birds
	end
	print(" Here lies the last fellow\\n+who gave a piggy to psenough.",50,84) -- \\n becomes \n after pactic.py
	t=t-1 -- t running backwards saves - sign somewhere
-- music:
	k=t&3 -- which channel to update
	-- the channels getting updated
	-- slightly out of sync makes more
	-- organic sound
	i=t>>9&3 -- which chord out of 4
	q=i&2 -- q=0 minor chord, q=2 second inversion major
	z={7,2,4,0} -- bass note of chord
	sfx(
		0,
		18+z[i+1]+k*(k-q*k+5+3*q)//2, -- note numbers for note k in chord
		9,
		k, -- only one channel is updated
		t/(k+1)/4 -- linearly decaying envelope
		-- lower channels loop faster
	)
end
-- <WAVES>
-- 000:00000000ffffffff00000000ffffffff
-- 001:0123456789abcdeffedcba9876543210
-- 002:0123456789abcdef0123456789abcdef
-- </WAVES>

-- <PALETTE>
-- 000:1a1c2c5d275db13e53ef7d57ffcd75a7f07038b76425717929366f3b5dc941a6f673eff7f4f4f494b0c2566c86333c57
-- </PALETTE>
