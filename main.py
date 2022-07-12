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
import time
from datetime import datetime

from learning_algo import Iteration_Controller, learning_algo
from fitness_functions import standard_obj_fxn, inversion_matrix,\
    average_affix_conversion_obj_fxn, weight_normalization
from file_readers import read_cog_datas, read_empties_datas, read_flaggies_datas
from cog_factory import cog_factory
from cog_array_stuff import Empties_Set


VERSION = 'Cogstruction 1.1.2 L'

def parseArgs():
    parser = argparse.ArgumentParser(description="A learning algorithm made "
                                     + "for optemizing the distrebution of "
                                     + "gears in the construction skill in "
                                     + "idleon. All arguments are optional.")
    parser.add_argument("-s", "--seed", type=int, default=datetime.now(),
                        help="the random seed to use for this run")
    parser.add_argument("-f", "--function",
                        choices=["aac", "average_affix_conversion",
                                 "im", "invertion_matrix"],
                        default="average_affix_conversion",
                        help="the fitness function that will be used to" +
                        " determine a cog array's fitness value.")
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
    parser.add_argument("--gen_min", type=int, default=100,
                        help="size of the cog_array population")
    parser.add_argument("--gen_max", type=int, default=400,
                        help="size of the cog_array population")
    parser.add_argument("--runs", type=int, default=1,
                        help="number of times to try running the simulation")
    parser.add_argument("--verbose", action='store_true',
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
    min_weight = min(build_weight, flaggy_weight, exp_weight)
    str_to_print = \
        str(prefix) + " build_weight:".ljust(18) +\
        (str(round(build_weight * mul, 2)) + str(sufix)).ljust(8) +\
        " ratio: " + ("%.2f" % (build_weight / min_weight)).rjust(7) + "\n" +\
        str(prefix) + " flaggy_weight:".ljust(18) +\
        (str(round(flaggy_weight * mul, 2)) + str(sufix)).ljust(8) +\
        " ratio: " + ("%.2f" % (flaggy_weight / min_weight)).rjust(7) + "\n" +\
        str(prefix) + " exp_weight:".ljust(18) +\
        (str(round(exp_weight * mul, 2)) + str(sufix)).ljust(8) +\
        " ratio: " + ("%.2f" % (exp_weight / min_weight)).rjust(7)
    return str_to_print
    


def main():
    #####################
    # Initialize Variables
    args = parseArgs()
    debug = args.debug
    verbose = args.verbose
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
    min_generations = args.gen_min
    max_generations = args.gen_max
    #####################


    #####################
    # Initialize Cog file names
    # File for cogs
    cog_datas_filename = "cog_datas.csv"
    # TODO: consider optional alternative file format
    # File for empty spaces
    empties_datas_filename = "empties_datas.csv"
    # TODO: consider optional alternative file format
    # Seprate file for flag locations
    flaggies_datas_filename = "flaggies_datas.csv"
    # TODO: consider seprate output location
    output_filename = "output.txt"
    # CSV output file
    previous_output_filename = "output.csv"
    #####################

    
    fitness_fn = None
    if args.function == "average_affix_conversion" or args.function == "aac":
        build_weight, flaggy_weight, exp_weight =\
            weight_normalization(
                build_weight, flaggy_weight, exp_weight, debug)
        if debug:
            print(weight_string(build_weight, flaggy_weight,
                  exp_weight, "Adj", "%", 100))
        fitness_fn = average_affix_conversion_obj_fxn
    elif args.function == "invertion_matrix" or args.function == "im":
        build_weight, flaggy_weight, exp_weight =\
            inversion_matrix(build_weight, flaggy_weight, exp_weight)
        if debug:
            print(weight_string(build_weight, flaggy_weight,
                  exp_weight, "Adj", "%", 100))
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
        controller,
        lambda cog: fitness_fn(
            cog, build_weight, 0, 0, debug),
        lambda cog: fitness_fn(
            cog, 0, flaggy_weight, 0, debug),
        lambda cog: fitness_fn(
            cog, 0, 0, exp_weight, debug)
    )

    toc = time.perf_counter()
    if verbose or debug:
        print(f"Best cog array found in {toc - tic:0.4f} seconds")

    print("Reading previous cog array data %s" % previous_output_filename)
    previous_cog_array = []
#    try:
    with open(previous_output_filename, 'r') as fh:
        while (line := fh.readline().rstrip()):
            previous_cog_array = previous_cog_array + [line]
#    except BaseException as err:
#        print("No previous array file found at " + previous_output_filename)

    # build the dictionary for the previous cog array
    previous_cog_array.pop(0)
    previous_cog_data_array = {}
    for cog_line in previous_cog_array:
        cog_data = cog_line.split(",")
        cog_data.pop(0)
        x = cog_data.pop(0)
        y = cog_data.pop(0)
        cog_data = tuple(cog_data)
        if x != "Spare":
            if cog_data in previous_cog_data_array.keys():
                previous_cog_data_array[cog_data].append([(x, y), False])
            else:
                previous_cog_data_array[cog_data] = [[(x, y), False]]
            print(cog_data, previous_cog_data_array[cog_data])

    new_cog_array = best[0].csv_record().split("\n")
    tittle = new_cog_array.pop(0)
    tittle = tittle.split(",")
    tittle.insert(3, "origin x")
    tittle.insert(4, "origin y")
    tittle = ",".join(tittle)
    new_cog_data_array = [tittle]
    for cog_line in new_cog_array:
        cog_data = cog_data = cog_line.split(",")
        c_id = cog_data.pop(0)
        x = cog_data.pop(0)
        y = cog_data.pop(0)
        cog_data_tuple = tuple(cog_data)
        source_x = "shelf"
        source_y = "shelf"
        if cog_data_tuple in previous_cog_data_array.keys():
            i = 0
            while i < len(previous_cog_data_array[cog_data_tuple]):
                if previous_cog_data_array[cog_data_tuple][i][1] == False:
                    source_x = previous_cog_data_array[cog_data_tuple][i][0][0]
                    source_y = previous_cog_data_array[cog_data_tuple][i][0][1]
                    previous_cog_data_array[cog_data_tuple][i][1] = True
                    break
                i = i + 1
        cog_data.insert(0, source_y)
        cog_data.insert(0, source_x)
        cog_data.insert(0, y)
        cog_data.insert(0, x)
        cog_data.insert(0, c_id)
        new_cog_data_array.append(",".join(cog_data))

    if debug:
        print(previous_cog_data_array)
        print("------")
        print(new_cog_data_array)
        print("\n".join(new_cog_data_array))
    
    print("Writing best cog array save data to %s" % "move_sequence.csv")
    with open("move_sequence.csv", "w") as fh:
        fh.write("\n".join(new_cog_data_array))
    

    print("Writing best cog array to %s" % output_filename)
    with open(output_filename, 'w') as fh:
        fh.writelines([VERSION, "\r\n"])
        fh.write(str(best[0]))

    print("Writing best cog array save data to %s" % previous_output_filename)
    with open(previous_output_filename, "w") as fh:
        fh.write(best[0].csv_record())

    if debug:
        print(str(best[0]))

if __name__ == "__main__":
    main()