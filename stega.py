# file: stega.py
# updated by Duncan Fisher
# 10/18/16 


from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import struct


# mode encoding
d = {'unicode':0, 'L':1, 'RGB':3, 'RGBA':4}

# bit mask for extracting bits from bytes
bit_mask = b'\x80\x40\x20\x10\x08\x04\x02\x01'





def inject_png(carrier, hidden, output):
    '''
    recieves 3 PNG file objects
    stores data from hidden in carrier and saves result to output
    '''
    carrier_img = Image.open(carrier) 
    hidden_img = Image.open(hidden) 
    hidden_bytes = add_header(hidden_img.mode, hidden_img.tobytes(), *hidden_img.size)
    carrier_bytes = inject_bytes(carrier_img.tobytes(), hidden_bytes)
    print(len(carrier_bytes), hidden_img.size)
    output_img = Image.frombytes(carrier_img.mode, carrier_img.size, carrier_bytes)
    output_img.save(output)


def inject_text(carrier, text, output):
    '''
    stores unicode text inside carrier and saves result to output
    '''
    carrier_img = Image.open(carrier)
    text_bytes = text.encode()
    text_bytes = add_header('unicode', text_bytes, len(text_bytes))
    carrier_bytes = inject_bytes(carrier_img.tobytes(), text_bytes)
    output_img = Image.frombytes(carrier_img.mode, carrier_img.size, carrier_bytes)
    output_img.save(output)


def inject_bytes(bs1, bs2):
    '''
    accepts two bytes objects bs1 and bs2 and injects the bytes of 
    bs2 one bit at a time into the least significant bit of each
    byte of bs1. Checks to ensure bs1 is large enough to hold the
    bits of bs2
    '''
    if len(bs1) < 8*len(bs2):
        return
    ba = bytearray(bs1)
    for i, byte in enumerate(bs2):
        for j in range(8):
            ba[8*i+j] = (ba[8*i+j] & 254) | ((bit_mask[j] & byte) >> (7-j))
    return bytes(ba)


def add_header(mode, data, x, y=1):
	'''
	mode -> string describing the type of data ('text', 'rgb', 'g', 'rgba')
	x, y -> dimensions of the image or number of bytes
	data -> a bytes object representing the object
	returns a byte array with header information describing the data 
	'''
	header = struct.pack('III', d[mode], x, y)
	return header + data


def unpack_bytes(data):
    '''
    parses a bytes object
    returns a tuple with the header and the data segment
    '''
    header = struct.unpack('III', extract_n_bytes(data, 12))
    data_segment = extract_n_bytes(data[96:], data_length(header) )
    return header , data_segment


def data_length(header):
    '''
    given a header return the number of bytes in the data segment
    '''
    if header[0] == 0 :
        return header[1]
    else :
        return header[1] * header[2]


def extract_n_bytes(data, n):
    '''
    returns a bytes object that is n bytes long and consists
    of the least significant bits of data
    '''
    if len(data) < 8*n :
        return
    ba = bytearray(n)
    for i in range(8*n):
        ba[i//8] = ba[i//8] | ((data[i] & 1) << (7 - (i%8)))
    return bytes(ba) 


def extract_text(carrier):
    '''
    given an image with a hidden unicode string
    returns the string
    '''
    img = Image.open(carrier)
    header, text_bytes = unpack_bytes(img.tobytes())
    text = text_bytes.decode()
    return text





# test functions via command line    

if __name__ == "__main__" :

    print('1 -> inject text', '2 -> inject image', '3 -> extract text', '4 -> extract image', sep='\n')
    choice = int(input('choice: '))

    if choice == 1 :
        carrier_path = input('image path: ')
        text = input('input a string: ')
        inject_text(carrier_path, text, 'output.png')
        img = Image.open('output.png')
    elif choice == 2 :
        carrier_path = input('carrier image path: ') 
        hidden_path = input('hidden image path: ')
        inject_png(carrier_path, hidden_path, 'output.png')
        img = Image.open('output.png')
    elif choice == 3 :
        path = input('image path: ')
        text = extract_text(path)
        print(text)
        img = Image.open('output.png')
        
    elif choice == 4 :
        path = input('image path: ')
        img = Image.open(path)
        header, img_bytes = unpack_bytes(img.tobytes())
        for key , val in d.items():
            if header[0] == val :
                mode = key
        img = Image.frombytes(mode, header[1:], img_bytes)
    else :
        exit(1)

    # display modified or extracted image
    im_array = np.array(img)
    plt.imshow(im_array)
    plt.show()
