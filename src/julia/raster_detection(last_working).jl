module raster_detection

using Base.Threads
using StatsBase
using Plots # DEBUG

SlidingWindowElement = SubArray{Float64, 1, Matrix{Float64}, Tuple{Int64, Base.Slice{Base.OneTo{Int64}}}, true}

"Helper function for vectorized equality evaluation"
function equals(x::Float64, y::Float64)::Bool
    return x == y
end

"""
Collapses adjacent points in a matrix based on a vector of bools, each bool
denoting whether the next row in the matrix is colinear
"""
function collapse_points(in_array::Matrix{Float64},
                         collapse_vector::Vector{Bool}
                         )::Tuple{Matrix{Float64}, Vector{UInt64}}

    columns = size(in_array)[2]
    start_indeces = Vector{UInt64}()
    end_indeces = Vector{UInt64}()

    # averages and counts consecutive true values and appends results to outputs
    @inbounds for (i, j) in collect(zip(1:length(collapse_vector) - 1, 2:length(collapse_vector)))
        if collapse_vector[i] == collapse_vector[j]
            continue
        elseif collapse_vector[i]
            append!(end_indeces, j)
        elseif collapse_vector[j]
            append!(start_indeces, j)
        end
    end

    indeces::Matrix{UInt64} = hcat(start_indeces, end_indeces)

    # initialize output arrays
    collapsed_array = Array{Float64}(undef, 0, columns)
    points_per_point = Vector{UInt64}()
    collapsed_array_array = Vector{Matrix{Float64}}()

    # loops through averaging points to be collapsed and storing
    # collapsed/uncollapsed subarrays in an array
    prev_end::UInt64 = 1
    for (start_index, end_index) in eachrow(indeces)
        uncollapsed::Matrix{Float64} = in_array[prev_end:start_index-1,:]
        collapsed_average = reshape(sum.(eachrow(in_array[start_index:end_index,:]')) ./ (end_index - start_index + 1),
                                    1, columns)
        append!(collapsed_array_array, (collapsed_array,
                                        uncollapsed,
                                        collapsed_average))
        end_index += 1
        append!(points_per_point, append!(ones(start_index - prev_end),
                                          end_index-start_index))
        prev_end = end_index
    end
    # Adds end section to subarray array, if loop hasnt
    append!(collapsed_array_array, in_array[prev_end:end,:])

    # Collapses arrays by reduction. This is vital, other attempted
    # ways of constructing array led to *awful* performance.
    collapsed_array = reduce(vcat, collapsed_array_array)

    # collapsed_array = vcat(collapsed_array, in_array[prev_end:end,:])
    append!(points_per_point, ones(size(in_array)[1] - prev_end + 1))

    return collapsed_array, points_per_point
end

"""
Collapses covertical (x = column 1) points in a matrix into an average point,
and returns a vector of the number of points collapsed to form each index
"""
function collapse_coverticals(in_array::Matrix{Float64}
                              )::Tuple{Matrix{Float64}, Vector{Int64}}
    x_axis = in_array[:, 1]
    # gets an array of whether each index is equal to the next one
    covertical_array::Vector{Bool} = equals.(x_axis[1:end-1], x_axis[2:end])
    # last point must be false for this as it has no following point
    append!(covertical_array, false)
    # collapse covertical points into average positions
    return collapse_points(in_array, covertical_array)
end

"""
Returns true of x2 greater than x1 and false if less than
"""
function direction(x1::Float64, x2::Float64)::Bool
    return x2 > x1
end


"""
Reduces matrix to list of indeces of turning points where direction of scan
switches from being positive to being negative
"""
function find_turning_points(in_array::Matrix{Float64})::Vector{UInt64}
    # Begins by collapsing the covertical points
    no_coverticals, points_per_point = collapse_coverticals(in_array)
    # Next, theres no need to compare slopes, just direction of movement on x
    # axis as the raster can never be vertical due to collapsed coverticals
    direction_array::Vector{Bool} = direction.(no_coverticals[1:end-1,1],
                                               no_coverticals[2:end,1])
    # next, reduce this array to indeces at which turns occur
    indeces = Vector{UInt64}()
    buffer = direction_array[1]
    @inbounds for (index, dir) in enumerate(direction_array)
        if dir != buffer
            append!(indeces, index)
        end
        buffer = dir
    end
    # then, convert these indeces in the no_coverticals array to indeces
    # in the original array
    original_indeces = Vector{UInt64}([1])
    prev_index = 1
    @inbounds for index in indeces
        append!(original_indeces, sum(points_per_point[prev_index+1:index]))
        prev_index = index
    end
    append!(original_indeces, sum(points_per_point[prev_index+1:end]))
    original_indeces = cumsum(original_indeces)
    return original_indeces
end

function taxicab_disp(swelement::Tuple{Matrix{Float64}, Matrix{Float64}})::Float64
    x1y1, x2y2 = swelement
    return abs(x1y1[1] - x2y2[1]) + abs(x1y1[2] - x2y2[2])
end

"""
Splits array into subarrays representing individual lines, in individual
samples, structured as hierarchical nested dicts. Thresholding is done based
on a normalized value between 0. (min taxicab displacement) and 1. (max
taxicab displacement)
"""
function tpdist_split(in_array::Matrix{Float64}, thresh_devs::Float64=1.) # ::Dict
    turning_points = find_turning_points(in_array) # gets turning points
    # Create a sliding window for comparing every second turning point
    sliding_window_indeces = zip(eachrow(turning_points[1:end-2]),
                                 eachrow(turning_points[3:end]))
    sliding_window = ((in_array[n1, :], in_array[n2, :])
                      for (n1, n2) in sliding_window_indeces)
    # Compute taxicab distance between every second turning point (chosen because
    # taxicab is analogous here and easier to compute than pythagorean distance)
    displacements = taxicab_disp.(sliding_window)
    # Determine threshold based on multiple of standard deviation
    thresh::Float64 = StatsBase.std(displacements) * thresh_devs
    # Find indeces of turning points with displacement above threshold
    split_points::Vector{Int64} = (1:size(displacements)[1])[displacements .> thresh]
    # Finally, returns the turning points corresponding to start/ends of samples
    return turning_points[split_points]
end

# Test of the turningpoints function
function test1(x::Dict)
    test = x[3.24]
    @time out = find_turning_points(test[:, 1:2])
    # @time out = tpdist_split(test, 0.03)
    ###########################################################################
    # @time out = tpdist_split(test)
    # out2 = hcat(out[1:end-1], out[2:end])
    # println(Matrix{Int64}(out2[1:10, :]))
    # println(size(out2))
    # test2 = test[out2[1, 1]:out2[1, 2],:]
    # println(size(test2))
    # filtered = Vector{Matrix{}}
    ###########################################################################
    # savefig(plot(eachindex(out), out), "Distest.svg")
    # exit() # DEBUG
    # println(minimum(out))
    # println(sum(out) / length(out))
    # println(size(out))
    return out
end

# Test of the ample splitting function
function test2(x::Dict)
    test = x[3.24]
    # @time out = find_turning_points(test[:, 1:2])
    @time out = tpdist_split(test)
    ###########################################################################
    # @time out = tpdist_split(test)
    # out2 = hcat(out[1:end-1], out[2:end])
    # println(Matrix{Int64}(out2[1:10, :]))
    # println(size(out2))
    # test2 = test[out2[1, 1]:out2[1, 2],:]
    # println(size(test2))
    # filtered = Vector{Matrix{}}
    ###########################################################################
    # savefig(plot(eachindex(out), out), "Distest.svg")
    # exit() # DEBUG
    # println(minimum(out))
    # println(sum(out) / length(out))
    # println(size(out))
    return out
end

end
