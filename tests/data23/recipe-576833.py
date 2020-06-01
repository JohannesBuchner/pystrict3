database={'name': '1234', 'name2': '5678', 'name3': '9012'}
name = input('Enter username: ')
ask = input('Enter pin: ')
if ask in database[name]:
    print('Welcome', name)
else:
    print('Invalid code')
