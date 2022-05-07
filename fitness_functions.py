def standard_obj_fxn(cog_array, build_weight, flaggy_weight, exp_weight):
    return cog_array.get_build_rate() * build_weight +\
           cog_array.get_flaggy_rate() * flaggy_weight +\
           cog_array.get_total_exp_mult() * exp_weight
