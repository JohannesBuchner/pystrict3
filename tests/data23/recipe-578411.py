import pygame
import time
import sys

CODE = {'A': '.-',     'B': '-...',   'C': '-.-.', 
        'D': '-..',    'E': '.',      'F': '..-.',
        'G': '--.',    'H': '....',   'I': '..',
        'J': '.---',   'K': '-.-',    'L': '.-..',
        'M': '--',     'N': '-.',     'O': '---',
        'P': '.--.',   'Q': '--.-',   'R': '.-.',
     	'S': '...',    'T': '-',      'U': '..-',
        'V': '...-',   'W': '.--',    'X': '-..-',
        'Y': '-.--',   'Z': '--..',
        
        '0': '-----',  '1': '.----',  '2': '..---',
        '3': '...--',  '4': '....-',  '5': '.....',
        '6': '-....',  '7': '--...',  '8': '---..',
        '9': '----.' 
        }
        
ONE_UNIT = 0.5
THREE_UNITS = 3 * ONE_UNIT
SEVEN_UNITS = 7 * ONE_UNIT
PATH = 'morse_sound_files/'

def verify(string):
	keys = list(CODE.keys())
	for char in string:
		if char.upper() not in keys and char != ' ':
			sys.exit('Error the charcter ' + char + ' cannot be translated to Morse Code')

def main():
	
	
	print('Welcome to Alphabet to Morse Code Translator v.01\n')
	
	msg = input('Enter Message: ')
	verify(msg)
	print()
	pygame.init()
	
	for char in msg:
		if char == ' ':
			print(' '*7, end=' ')
			time.sleep(SEVEN_UNITS)
		else:
			print(CODE[char.upper()], end=' ')
			pygame.mixer.music.load(PATH + char.upper() + '_morse_code.ogg')
			pygame.mixer.music.play()
			time.sleep(THREE_UNITS)
			
if __name__ == "__main__":
	main()
