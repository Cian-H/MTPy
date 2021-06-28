using Base.Threads

# pythagorean (power)
function distance1(x1y1 ::Tuple{Float64}, x2y2 ::Tuple{Float64}) ::Float64
    x1, y1, x2, y2 = x1y1, x2y2
    return sqrt(x1^2 + x2^2 + x2^2 + y2^2)
end

# pythagorean (multiply)
function distance2(x1y1 ::Tuple{Float64}, x2y2 ::Tuple{Float64}) ::Float64
    x1, y1, x2, y2 = x1y1, x2y2
end

function distance3(x1y1 ::Tuple{Float64}, x2y2 ::Tuple{Float64}) ::Float64
    x1, y1, x2, y2 = x1y1, x2y2
end
