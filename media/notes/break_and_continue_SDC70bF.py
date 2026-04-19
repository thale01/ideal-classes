a = [12,23,34,4,55,66,77,8,9]
'''
for i in a :
    if i ==55:
        print("number is found")
        break 
for i in a :
    if i ==23:
        continue
    print("its go")
 '''
''' 
take_number = int(input("write any number : ")) 
for i in take_number:
    if i ==55:
        print(i,"find next number")
        continue 
    elif i==77:
        print(i,"number is found")
        break
    else:
        print("number is wrong")
'''
'''
take_number = (input("write any number : ")) 
for i in take_number:
    if i =="55":
        print("right number")
    else:
        print("wrong number")
     
    elif i != "55":
        print("try again")
    
    elif i != "55":
        print("attempt over")
        break'''   
    

l = [45,77,56,34,23,34]
l2 = [45,90,34]
i = 0 
while i <len(l):
    if l[i] in l2:
        i+=1
        continue
    l2.append(l[i])
    i+=1
print(f"final --- {l2}")


ListOfProduct = ["rice","roti","chicken","mutton","panner"]
priceOfProduct =[100,20,150,200,160]

product = []
price =[]
