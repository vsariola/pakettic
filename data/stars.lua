--{
t = 0
function TIC()
  --{
  t = t + .004
  for i = 0, 9e3 do
    --{
    y = 0
    z = 0
    --}
    for j = 1, 3 do
      q = s(t * j)
      x = y * s(q + 8) + z * s(q)
      y = z * s(q + 8) - y * s(q)
      z = (s(i * j) * 1e6 - t + s(y)) % 2 - 1
    end
    q = z < 0 or pix(120 + x * 99 / z, 68 + y * 99 / z, -z * 11)
  end
  --}
  for i = 0, 32639 do
    --{
    poke4(i, peek4(i) - .9
    )
    k = i % 48
    --}
    poke(k + 16320, k * (4 + s(k % 3 + t)))
  end
end

s = math.sin
--}
