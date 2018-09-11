#!/usr/bin/python2.7
import math


def get_return_ser(data_file, first_price, data_points):

    # Derives returns series, stores in a list, and sorts from biggest gain to biggest loss
    # Returns the returns series
    # Also returns the time series for chart display

    ret_ser = []
    time_ser = []
    unsorted_rets = []

    today = first_price
    time_ser.append(today)

    if data_points == 0:
        # Work out returns and store in list
        for line in data_file:
            yesterday = float(line.split(',')[6])
            last_date = line.split(',')[0]
            ret_ser.append((today-yesterday)/yesterday)
            unsorted_rets.append((today-yesterday)/yesterday)
            time_ser.append(yesterday)
            today = yesterday
    else:
        for i in range(0, data_points - 1):
            line = data_file.readline()
            yesterday = float(line.split(',')[6])
            last_date = line.split(',')[0]
            ret_ser.append((today-yesterday)/yesterday)
            unsorted_rets.append((today-yesterday)/yesterday)
            time_ser.append(yesterday)
            today = yesterday

    # Sort list, biggest gain first
    ret_ser.sort(reverse=True)

    # Reverse the lists needed for display
    time_ser = reversed(time_ser)
    unsorted_rets = reversed(unsorted_rets)

    return ret_ser, unsorted_rets, time_ser, last_date


def data_process(name, data_points):

    # Open the requested data file, get returns series, calculate parameters needed for
    # Monte Carlo analysis
    # Return returns series, mean, standard deviation and most recent closing price

    data_file = open("./data/" + name + ".csv", "r")

    # Skip header line
    data_file.readline()

    # Store most recent price as needed for Monte Carlo simulation
    line = data_file.readline()
    today_price = float(line.split(',')[6])

    # Get the returns series then close the file

    ret_ser, time, ret, last_date = get_return_ser(data_file, today_price, data_points)
    data_file.close()

    # Calculate mean and standard deviation of returns series, required for
    # covariance and Monte Carlo

    avg = calc_mean(ret_ser)
    sd = standard_dev(ret_ser)

    return ret_ser, avg, sd, today_price, last_date


def historical(ret_ser):

    # Calculate values for historical method
    # Return values at 95% and 95% position in series

    i95 = (int(round((95.0/100.0) * len(ret_ser)))) - 1
    i99 = (int(round((99.0/100.0) * len(ret_ser)))) - 1

    return ret_ser[i95], ret_ser[i99]


def covariance(mean, sd):

    # Calculate values for covariance method
    # Return 95% confidence value and 99% confidence value

    var95 = (mean+(1.65*sd))*-1.0
    var99 = (mean+(2.33*sd))*-1.0

    return var95, var99


def standard_dev(ret_ser):

    # Calculate standard deviation of returns sequence
    # Returns standard deviation

    total = 0.0
    avg = calc_mean(ret_ser)

    for num in ret_ser:
        total += (num-avg)**2

    return math.sqrt(total / (len(ret_ser) - 1))


def calc_mean(ret_ser):

    # Calculate mean of returns sequence
    # Returns mean

    return sum(ret_ser) / len(ret_ser)
