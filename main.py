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


import random
import numpy as np
import argparse
from datetime import datetime

from learning_algo import Iteration_Controller, learning_algo
from fitness_functions import standard_obj_fxn, inversion_matrix,\
    average_affix_conversion_obj_fxn, weight_normalization
from file_readers import read_cog_datas, read_empties_datas, read_flaggies_datas
from cog_factory import cog_factory
from cog_array_stuff import Empties_Set


# #############################################
# For testing
import time
# #############################################

VERSION = 'Cogstruction L 1.1.1 a'

def parseArgs():
    parser = argparse.ArgumentParser(description="A learning algorithm made "
                                     + "for optemizing the distrebution of "
                                     + "gears in the construction skill in "
                                     + "idleon. All arguments are optional.")
    parser.add_argument("-s", "--seed", type=int, default=datetime.now(),
                        help="the random seed to use for this run")
    parser.add_argument("-f", "--function",
                        choices=["average_affix_conversion",
                                 "invertion_matrix"],
                        default="average_affix_conversion",
                        help="the fitness function that will be used to"
                        + " determine a cog array's fitness value.")
    parser.add_argument("--build_weight", "--bw", type=float,
                        default=1.0,
                        help="the weight of the build speed in the fitness " +
                        "function")
    parser.add_argument("--flaggy_weight", "--fw", type=float,
                        default=1.0,
                        help="the weight of the flaggy speed in the fitness " +
                        "function")
    parser.add_argument("--exp_weight", "--ew", type=float,
                        default=1.0,
                        help="the weight of the exp bonus in the fitness " +
                        "function")
    parser.add_argument("--pop", type=int, default=2000,
                        help="size of the cog_array population")
    parser.add_argument("--runs", type=int, default=1,
                        help="number of times to try running the simulation")
    parser.add_argument("--verbosity", action='store_true',
                        help="increase output verbosity")
    parser.add_argument("-d", "--debug", action='store_true',
                        help="sends program into debug mode, will print a"
                        + " lot of debug messages")
    parser.add_argument("-v", "--version", action='version',
                        version=VERSION)
    args = parser.parse_args()
    return args


def weight_string(build_weight, flaggy_weight, exp_weight, prefix, sufix,\
                  mul = 1):
    str_to_print = \
        str(prefix) + " build_weight:" + str(round(build_weight * mul, 2)) +\
        str(sufix) + "\n" +\
        str(prefix) + " flaggy_weight:" + str(round(flaggy_weight * mul, 2)) +\
        str(sufix) + "\n" +\
        str(prefix) + " exp_weight:" + str(round(exp_weight * mul, 2)) +\
        str(sufix)
    return str_to_print
    


def main():
    #####################
    # Initialize Variables
    args = parseArgs()
    debug = args.debug
    verbose = args.verbosity
    if debug:
        print("Debug mode enabled")
    random.seed(args.seed)  # old value 133742069
    if debug:
        print("Seed: ", args.seed)
    pop_size = args.pop
    num_restarts = 1
    build_weight = args.build_weight
    flaggy_weight = args.flaggy_weight
    exp_weight = args.exp_weight
    # TODO: figure out what these values mean in the context of the code
    prob_cross_breed = 0.5
    prob_one_point_mutation = 0.25
    prob_two_point_mutation = 0.25
    num_mutations = 800
    factor_base = 2
    max_factor = 4
    max_multiplier = 16
    req_running_total = 0.01
    max_running_total_len = 10
    min_generations = 100
    max_generations = 400
    #####################


    #####################
    # Initialize Cog file names
    cog_datas_filename = "cog_datas.csv"  # File for cogs
    # TODO: consider optional alternative file format
    empties_datas_filename = "empties_datas.csv"  # File for empty spaces
    # TODO: consider optional alternative file format
    flaggies_datas_filename = "flaggies_datas.csv"  # Seprate file for flag locations
    output_filename = "output.txt"
    #####################

    
    fitness_fn = None
    if args.function == "average_affix_conversion":
        build_weight, flaggy_weight, exp_weight =\
            weight_normalization(
                build_weight, flaggy_weight, exp_weight, debug)
        if debug:
            print(weight_string(build_weight, flaggy_weight,
                  exp_weight, "Adj", "%", 100))
        fitness_fn = average_affix_conversion_obj_fxn
    elif args.function == "invertion_matrix":
        build_weight, flaggy_weight, exp_weight =\
            inversion_matrix(build_weight, flaggy_weight, exp_weight)
        fitness_fn = standard_obj_fxn
    else:
        if debug:
            raise Exception("Unknown fitness function", args.function)
        else:
            print("Unknown fitness function")
        return -1

    controller = (Iteration_Controller()
        .set_restart_info(num_restarts)
        .set_generation_info(min_generations, max_generations, max_running_total_len, req_running_total)
        .set_mutation_info(num_mutations)
        .set_breeding_scheme_info(prob_cross_breed, prob_one_point_mutation, prob_two_point_mutation)
                  )
    cog_datas = read_cog_datas(cog_datas_filename)
    empties = read_empties_datas(empties_datas_filename)
    empties_set = Empties_Set(empties)
    cogs = cog_factory(cog_datas)

    if debug:
        print("Timer started")
    tic = time.perf_counter()
    best = learning_algo(
        cogs,
        empties_set,
        set(),
        pop_size,
        lambda cog: fitness_fn(
            cog, build_weight, flaggy_weight, exp_weight, debug),
        factor_base,
        max_factor,
        max_multiplier,
        controller
    )

    toc = time.perf_counter()
    if verbose or debug:
        print(f"Best cog array found in {toc - tic:0.4f} seconds")

    print("Reading previous cog array data %s" % output_filename)
    try:
        with open(output_filename, "r") as fh:
            print(fh.readline())
    except BaseException as err:
        print("No previous array file found at " + output_filename)

    print("Writing best cog array to %s" % output_filename)
    with open(output_filename, "w") as fh:
        fh.writelines([VERSION, "\r\n"])
        fh.write(str(best[0]))

if __name__ == "__main__":
    main()