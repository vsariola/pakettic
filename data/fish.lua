--{
function TIC()
  --{
  cls(8)
  t = time() / 99
  --}
  print("pestis: under the waves", 9, 9, 12)
  for i = 0, 50 do
    --{
    x = 120 --- 110 --- 130
    y = 170
    w = 3
    --}
    for j = 0, 500 do
      --{
      x = x + s(w) + s(t / 9) / 8
      w = w + s(s(s(i * 9) * 2 + j / 35 + t / 37) * 3 + j / 33 + t / 27) / 30
      l = i + j / 9 - t / 2
      y = y + s(w + 8)
      --}
      --{
      circ(x, y, s(l) * 4, l % -8)
      rect(x, y - 8, 1, s(l) * 15 - 4, l % 4)
      --}
    end
  end
end

s = math.sin

--}
