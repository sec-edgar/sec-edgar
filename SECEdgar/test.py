import time
from sec import Filing_10Q, Filing_10K, Filing_8K

def test():
	t1 = time.time()
	# file containig company name and corresponding cik codes
	companyCodeList = list()    # company code list 
	cikList = list()	    # cik code list
	dateList = list()           # pror date list
	try:
		crs = open("file.txt", "r")
	except:
		print "No input file Found"
	
	# get the comapny  quotes and cik number from the file.
	for columns in ( raw.strip().split() for raw in crs ):  
	     	companyCodeList.append(columns[0])
		cikList.append(columns[1])
		dateList.append(columns[2])

	del cikList[0]; del companyCodeList[0]; del dateList[0]
	for i in range(len(cikList)):
		Filing_10Q(str(companyCodeList[i]), str(cikList[i]), str(dateList[i]))
		Filing_10K(str(companyCodeList[i]), str(cikList[i]), str(dateList[i]))
		Filing_8K(str(companyCodeList[i]), str(cikList[i]), str(dateList[i]))
	
	t2 = time.time()
	print "Total Time taken: ",
	print (t2-t1)
	crs.close()
	
if __name__ == '__main__':
	test()	