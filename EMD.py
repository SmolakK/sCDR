from pyemd import emd
import numpy as np
from scipy.spatial import distance_matrix
import time

"""
PATHS REQUIRE ADJUSTMENT
"""
start = time.time()
file_write = """path_to_write"""
writef = open(file_write,'wb')
for num in range(24):
    path = """dir"""+str(num)+"""joined.csv"""
    prob1 = []
    prob2 = []
    x = []
    y = []
    with open(path,'r') as hour10:
        hour10.next()
        for line in hour10:
            line = line.split(',')
            x.append(float(line[::-1][0]))
            y.append(float(line[::-1][1]))
            prob2.append(float(line[::-1][2].replace('\n','')))
            prob1.append(float(line[13]))
            #limit += 1
    prob1 = np.array(prob1)
    prob2 = np.array(prob2)

    f1 = []
    f2 = []
    for element in zip(x, y):
        f1.append([element[0], element[1]])
        f2.append([element[0], element[1]])

    dm = distance_matrix(f1, f2, p=2)
    print "Starting EMD"
    result = emd(prob1,prob2,dm)
    print result
    result_miles = str(result/1000*0.621371192)
    print "Finished EMD"
    writef.write(str(num)+','+str(result)+','+result_miles+"""\n""")
end = time.time()
print("Time elapsed:" + str(end - start))
writef.close()
