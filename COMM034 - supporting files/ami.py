 #!/usr/bin/python2.7
import random
import os
from google.cloud import datastore


def get_data():

    # Read in instance number from local file, and if this is first instance,
    # also get number of samples
    # Return instance number and number of samples

    num_samples = 0

    inst_file = open("/home/ubuntu/data.txt")

    inst = int(inst_file.readline())

    if inst == 0:

        num_samples = int(inst_file.readline())

    inst_file.close()

    return inst, num_samples


def gds_write(inst_num, var95, var99):

    # Write results to Google Cloud Datastore, with key name that
    # identifies this instance

    ds_client = datastore.Client()

    kind = 'Results'
    name = 'inst' + str(inst_num)
    param_key = ds_client.key(kind, name)

    param = datastore.Entity(key=param_key)

    param['method'] = 'EC2'
    param['var95'] = str(var95)
    param['var99'] = str(var99)

    ds_client.put(param)

    return


def gds_read():

    # Read input parameters from Google Cloud Datastore
    # Return mean, standard deviation, most recent price and number of samples

    ds_client = datastore.Client()

    kind = 'Input'
    name = 'Params'
    param_key = ds_client.key(kind, name)

    param = ds_client.get(param_key)

    return float(param['average']), float(param['sd']), float(param['recent']), int(param['samples'])


def historical(ret_ser):

    # Calculate values for historical method
    # Return Value at Risk at 95% and 99% confidence

    i95 = (int(round((95.0/100.0) * len(ret_ser)))) - 1
    i99 = (int(round((99.0/100.0) * len(ret_ser)))) - 1

    return ret_ser[i95], ret_ser[i99]


# Main
# Monte Carlo method

# Set up environment variable needed to access Google Cloud Datastore

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/ubuntu/comm034x1.json"

# Get input parameters from Google Cloud Datastore, then get instance number
# from local file

mean, sd, rec_price, mc_samples = gds_read()

inst_num, samples = get_data()

if inst_num == 0:

    mc_samples = samples

# Generate simulated price series
sim_price_ser = []
sim_ret_ser = []

for i in range(mc_samples):
    sim_price_ser.append((1.0 + random.gauss(mean, sd)) * rec_price)

# Generate simulated returns series
for i in range(1, mc_samples):
    sim_ret_ser.append((sim_price_ser[i-1] - sim_price_ser[i])/sim_price_ser[i])

# Sort from the largest simulated profit to the largest simulated loss
sim_ret_ser.sort(reverse=True)

# Use same method for historical function to get correct series member
var95, var99 = historical(sim_ret_ser)

# Write results back to Google Cloud Datastore

gds_write(inst_num, var95, var99)

