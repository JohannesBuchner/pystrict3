import re
print(" Write  product  name  : ")
nume_produs = input()
print(" Write product  price : ")
cost_produs = eval(input())
if (nume_produs == re.sub('[^a-z]',"",nume_produs)):
    print(('%s %d'%(nume_produs,cost_produs)))
else:
    print("Error ! You  must tape letters")
eval(input())
