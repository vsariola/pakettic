-- title: Murkwood.tic
-- author: Ilmenit + sizecoders
-- desc: 256 bytes intro port from Atari XE
-- script: lua

function TIC()
  t=t+1
  cls(15)
  math.randomseed (0) -- 56
  
  for layer=14,1,-1 do
    y=120-layer*5
    for x=0,layer/4 do
      -- trees
        r=math.random(270)
        rect((r+t/layer/4)%270-30,0,30-layer*2,136,layer)
    end
    r=14
    rect((r+t/layer/4)%270-30,0,30-layer*2,136,layer)
    for x=0,270 do      
      r=math.random(270)
      -- ground
      line((x+t/layer/4)%270,y,(x+t/layer/4)%270,136,layer)
      y=y+2*math.random()-1
      -- rain
      pix((x+t/layer/4)%270,(r+t/layer)%270,layer+1)
      -- small dither
      pix((x+t/layer/4)%270,r/2,pix((x+t/layer/4)%270,r/2)-1)
      -- palette
      poke(16320+x%48,x%48*5)
    end
  end

  -- play tune
  for x=0,3 do
    sfx(
    0, -- sfx
    41+({0,3,7,8,10,12,15,3})[
     (
         (4-x)*(t//(x*64+64)+1)+(4-x)//4*4
     )%8+1
    ], -- note
    8, -- duration
    x, -- x
    (x*64+64-t)/8
    )
  end
 end
 t=0