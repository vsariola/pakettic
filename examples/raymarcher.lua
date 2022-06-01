--{
function TIC()
  t = (time() / 199--| 200
      ) --| (time()*.005)
  for i = t % 1, M, 1.9 do
    --{
    u = i % 240 / 99 - 1
    v = i / M - .5
    k = s(t / 8)
    --}
    u, w = u + k, 1 - k * u
    --{
    x = s(t / 3)
    y = t
    z = 0
    j = 0
    --}
    repeat Y = y % 4 - 2
      m = 5 - (Y * Y + x * x + z * z / 50) ^ .5
      --{
      x = x + u * m
      y = y + v * m
      z = z + w * m
      j = j + 1
      --}
    until j > m * 9
    poke4(i, z / 5 + 9 + s(y + z / 2))
  end
end

M = 32639
s = math.sin
--}
