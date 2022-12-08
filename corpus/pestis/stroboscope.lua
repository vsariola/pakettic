--{
d = {

  -- start 1, length 16: key patterns (essentially: chord progressions)
  1, 1, 1, 1,
  1, 1, 0, 1,
  1, 3, 5, 2,
  1, 3, 0, 1,

  -- start 17, length 80: note patterns
  1, 0, 5, 3, 4, 0, 7, 0, 1, 0, 3, 4, 5, 5, 4, 3,
  1, 7, 7, 1, 7, 7, 1, 7, 1, 7, 7, 1, 7, 7, 1, 7,
  1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0,
  1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0,
  1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, -- 1, 1,

  -- start 95, length 9: which chord progression to play
  1, 1, 0, 0, 3, 3, 3, 2, 0,

  -- start 104, length 2: what is the note length for each channel
  -2, 1, -- 0, 0, from following

  -- start 106, length 36: orderlist for the 4 channels
  0, 0, 0, 5, 5, 1, 1, 1, 5,
  3, 3, 2, 2, 2, 2, 2, 2, 0,
  0, 1, 3, 3, 1, 1, 1, 1, 3,
  3, 3, 4, 5, 5, 5, 5, 5, 4,

  -- start 142, length 3: primitives (circles and horiz/vert rectangles)
  function(n, u, u, a) rect(0, n - u, 240, u * 2, a) end,
  circ,
  function(n, u, u, a) rect(n - u, 0, u * 2, 240, a) end,
}

t = 0

function TIC()
  --{
  -- all channels get updated unnecessarily many times to reuse the same loop for setting palette
  for a = 47, 0, -1 do
    k = a % 4 -- which channel to update
    p = t // 896 -- orderlist pos
    poke(65896, 32) -- set chn 2 wave
    x = t << d[k + 104] -- envelope pos
    -- n is note (semitones), 0=no note
    n = d[
        16 * d[9 * k + p + 106] + 1 -- patstart
            + x // 14 % 16]
    -- save envelopes for syncs
    -- d[0] = chn 0, d[-1] = chn 1...
    -- % ensures if n=0|pat=0 then env=0
    d[-k] = n * d[9 * k + p + 106] // -52 * x % 14
    u = d[4 * d[p + 95] + 1 + t // 224 % 4]

    n = ((n - 1 - u // 2 * 2) * 7 // 6 + u + 1) * 12 // 7
    --{
    sfx(
      k, -- channel k uses wave k
      8 -- global pitch
      + 12 * k -- octave
      + n -- note
      - k // 3 * x % 14 * 7-- pitch drop for the kick
      ,
      2,
      k,
      d[-k]-- stored envelope
    )
    -- set palette
    poke(16320 + a, 255 / (1 + 2 ^ (5 - s(a % 3 + p) - d[-3] / 5 - a / 5)) ^ 2)
    --}
  end
  cls(3)
  --}
  -- draw the center of the glowing thing (ball, rectangle) black
  d[p % 3 + 142](
    s(p % 8 * (s(t / 70) + t / 179)) * 52 + 120,
    s(p % 8 * (s(t / 79) + t / 170)) * 52 + 68, 50, 0)

  for a = 13, 1, -1 do
    u = 1 + a * a * (d[-3] + 14) / 6000 -- zoom factor, how far we are from the light
    for k = .5, 10 do -- draw 20 lights
      y = (1 + p) % 3 // 2 * (1 - k / 5)
      x = (1 - y * y) ^ .5 * s(p // 3 * k * 4 + t / 18)

      d[p % 3 + 142](
        s(p % 8 * (s(t / 70) + t / 179)) * 52 + x * u * 52 + 120,
        s(p % 8 * (s(t / 79) + t / 170)) * 52 + y * u * 52 + 68,
        a * math.min(-- this madness smoothly hides the "light" when it's behind the ball/cylinder
          math.min(
            1 - u * (x ^ 2 + y * y) ^ .5,
            (1 - y * y) ^ .5 * s(p // 3 * k * 4 + t / 18 + 8)
          ) * -9, 1
        ) * d[-2] / 5 - 1,
        -a)
    end
    -- just make the effect a bit more busy to add a rectangle sweeping the screen synced to bassline
    d[144 - (n & 2)]((.5 - n % 2) * (d[0] - 6) * u * 52 + 120, 0, u * 10, -a)
  end
  t = t + 1, t < 8063 or exit()
end

s = math.sin
--}

-- <TILES>
-- 001:eccccccccc888888caaaaaaaca888888cacccccccacc0ccccacc0ccccacc0ccc
-- 002:ccccceee8888cceeaaaa0cee888a0ceeccca0ccc0cca0c0c0cca0c0c0cca0c0c
-- 003:eccccccccc888888caaaaaaaca888888cacccccccacccccccacc0ccccacc0ccc
-- 004:ccccceee8888cceeaaaa0cee888a0ceeccca0cccccca0c0c0cca0c0c0cca0c0c
-- 017:cacccccccaaaaaaacaaacaaacaaaaccccaaaaaaac8888888cc000cccecccccec
-- 018:ccca00ccaaaa0ccecaaa0ceeaaaa0ceeaaaa0cee8888ccee000cceeecccceeee
-- 019:cacccccccaaaaaaacaaacaaacaaaaccccaaaaaaac8888888cc000cccecccccec
-- 020:ccca00ccaaaa0ccecaaa0ceeaaaa0ceeaaaa0cee8888ccee000cceeecccceeee
-- </TILES>

-- <WAVES>
-- 000:00000000ffffffff00000000ffffffff
-- 001:0123456789abcdeffedcba9876543210
-- 002:0123456789abcdef0123456789abcdef
-- </WAVES>

-- <SFX>
-- 000:000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000304000000000
-- </SFX>

-- <TRACKS>
-- 000:100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
-- </TRACKS>

-- <PALETTE>
-- 000:1a1c2c5d275db13e53ef7d57ffcd75a7f07038b76425717929366f3b5dc941a6f673eff7f4f4f494b0c2566c86333c57
-- </PALETTE>
