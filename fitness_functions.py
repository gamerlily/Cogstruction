"""
Cogstruction: Optimizing cog arrays in Legends of Idleon
    Copyright (C) 2021 Michael P. Lane

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
"""
"""
    File created by Lily Stejko 5/7/2022
"""

"""
- A convex combination (i.e. weighted average) of the build, flaggy,
  and exp rates. 
- ''obj_fnx'' is an abbreviation of ''objective function''.
"""

import numpy as np

def inversion_matrix(input_build_weight, input_flaggy_weight, input_exp_weight,
                     debug=False):
    inv_build_weight = 7000.0 / input_build_weight   # Seem arbitary
    inv_flaggy_weight = 2000.0 / input_flaggy_weight  # Seem arbitary
    inv_exp_weight = 3.0 / input_exp_weight  # Seem arbitary
    A = np.array([
        [1., 1., 1.],
        [inv_build_weight, -inv_flaggy_weight, 0.],
        [0., inv_flaggy_weight, -inv_exp_weight]
    ])
    b = np.array([1., 0., 0.])
    new_build_weight, new_flaggy_weight, new_exp_weight = np.linalg.solve(A, b)
    return new_build_weight, new_flaggy_weight, new_exp_weight

def standard_obj_fxn(cog_array, build_weight, flaggy_weight, exp_weight,
                     debug=False):
    return cog_array.get_build_rate() * build_weight +\
        cog_array.get_flaggy_rate() * flaggy_weight +\
        cog_array.get_total_exp_mult() * exp_weight

def average_affix_conversion_obj_fxn(cog_array, build_weight, flaggy_weight,
                             exp_weight, debug=False):
    if debug:
        print("Build rate:", cog_array.get_build_rate())
    build_contrebution = build_weight *\
        ((3 * cog_array.get_build_rate()) /
         (5.5 * cog_array.get_num_occupied()))
    if debug:
        print("Flaggy rate:", cog_array.get_build_rate())
    flaggy_contrebution = flaggy_weight *\
        ((3 * cog_array.get_flaggy_rate()) /
         (5.5 * cog_array.get_num_occupied()))
    if debug:
        print("XP multiplier:", cog_array.get_total_exp_mult())
    exp_contrebution = exp_weight *\
        ((3 * cog_array.get_total_exp_mult()) /
         (5.5 * cog_array.cog_array.get_num_occupied()))

    return build_contrebution + flaggy_contrebution + exp_contrebution