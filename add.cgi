import cgi
import cgitb
cgitb.enable()

input_data=cgi.FieldStorage()
num1=0
num2=0

print ('Content-Type:text/html')
print()
print('<h1>Resultado da Soma</h1>')
try:
    num1=int(input_data["num1"].value)
    num2=int(input_data["num2"].value)
except:
    print('<p>não deu certo<p>')

sum = num1 + num2
print('<p>{0} + {1} = {2}</p>'.format(num1, num2, sum))
