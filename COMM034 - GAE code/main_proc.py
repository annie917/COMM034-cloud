#!/usr/bin/python2.7

import data_proc
import ndb_functions
from aws_functions import create_ec2_from_img
from lambda_functions import call_lambda_r


def calc_samples(resources, tot_samples):

    # Returns number of samples for first instance to calculate, plus number of samples
    # for all other instances to calculate

    samples_per_inst = int(round(tot_samples/resources))
    samples_first_inst = int(tot_samples) - (samples_per_inst*(int(resources)-1))

    return samples_per_inst, samples_first_inst


def main_processing(name, investment, data_points, mc_samples, mc_resources, ec2_flag):

    # Top level processing function, called when Submit button is clicked
    # Get returns series, most recent price, mean and standard deviation

    ret_ser, avg, sd, rec_price, last_date = data_proc.data_process(name, data_points)

    # Store the entered parameters, ready for later display
    if ec2_flag:
        res_type = "EC2"
    else:
        res_type = "Lambda"

    ndb_functions.gds_write_user_params(name, investment, len(ret_ser)+1, mc_samples, mc_resources, res_type)

    # Get VaR using historical method and store in Datastore
    var_hist = data_proc.historical(ret_ser)
    ndb_functions.gds_write_res("hist", "hist", var_hist[0], var_hist[1])

    # Get VaR using covariance method and store in Datastore
    var_cov = data_proc.covariance(avg, sd)
    ndb_functions.gds_write_res("cov", "cov", var_cov[0], var_cov[1])

    # Calculate number of samples for each resource

    inst_samples, first_samples = calc_samples(float(mc_resources), float(mc_samples))

    if ec2_flag:

        # Write the parameters required by EC2 instances to Datastore,
        # the call function to start instances
        ndb_functions.gds_write_params(avg, sd, rec_price, inst_samples)
        create_ec2_from_img(mc_resources, first_samples)

    else:

        # Call lambda function in parallel
        call_lambda_r(avg, sd, rec_price, first_samples, inst_samples, mc_resources)

    return
