import random
def lambda_handler(event, context):
    mc_samples = int(event['key1'])
    mean = float(event['key2'])
    sdev = float(event['key3'])
    rec_price = float(event['key4'])

    sim_price_ser = []
    sim_ret_ser = []

    # Generate simulated price series
    for i in range(mc_samples):
        sim_price_ser.append((1.0 + random.gauss(mean, sdev)) * rec_price)

    # Generate simulated returns series
    for i in range(1, mc_samples):
        sim_ret_ser.append((sim_price_ser[i - 1] - sim_price_ser[i]) / sim_price_ser[i])

    # Sort from the largest simulated profit to the largest simulated loss
    sim_ret_ser.sort(reverse=True)

    i95 = (int(round((95.0 / 100.0) * len(sim_ret_ser)))) - 1
    i99 = (int(round((99.0 / 100.0) * len(sim_ret_ser)))) - 1

    return (str(sim_ret_ser[i95]), str(sim_ret_ser[i99]))