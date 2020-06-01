print("all amounts should be in dollars!")

while True:
	P=float(input("enter Principal:"))
	i=float(input("enter Percentage of interest rate:"))
	t=float(input("enter Time(in years):"))
	I=P*t*(i/100)
	print("Interest is", I,"dollars")
