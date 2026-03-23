data_list=[]
n=int(input("enter the max no"))
for i in range(0,n):
    z=int(input("enter the no"))
    data_list.append(z)
new_list = []
while data_list:
    minimum = data_list[0] 
    for x in data_list: 
        if x < minimum:
            minimum = x
    new_list.append(minimum)
    data_list.remove(minimum)
print(new_list)