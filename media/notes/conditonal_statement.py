listOfNumber = [ 1,23,34,45,56,7,88,12]
user = int(input("enter your number : "))

if user in listOfNumber :
    if user%2 !=0:
        print( listOfNumber,"element is persent in list and it is odd number") 
    else :
        print(listOfNumber,"element is present in list and it is even number")
else :
    print("element does not present ")


age =15 
nationality = "indian"
id = True

if age>=18:
    if nationality == "indian":
        if id == True :
            print(" you can opt for adhaarcard")
        else :
            print("you must have atleast one id to opt for adhaarcard")
    else :
        print("you must have indian to opt for adhaarcard")
else :
    print("you must be 18 or above to apply for adhaarcard")

        
light="green"
 
if light=="red" :
    print("stop")
elif light=="green":
    print("go")
elif light=="yellow":
    print("look")
else:
    print("no light")

