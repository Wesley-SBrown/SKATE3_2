
import cv2
import numpy as np
import matplotlib.pyplot as plt

image_input = cv2.imread('SEISMOGRAM', cv2.IMREAD_GRAYSCALE)
brightness_data = np.mean(image_input)
contrast_data = np.std(image_input)
print('brightness:',brightness_data, 'contrast:', contrast_data)

'''
Gamma Correction: Balance out the over/under expose
'''

def gamma_correct(image, gamma=1.2):
    invGamma = 1.0/ gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")

    # apply gamma correction using the lookup table
    return cv2.LUT(image, table)
'''
Binarization
Assuption: the median of intensity histogram lies in background
So, any traces would not be filtered
'''
# These are probably the only important parameters in the
# whole pipeline (steps 0 through 3).
BLOCK_SIZE = 100
DELTA = 25

#blurring 
def preprocess(image):
    image = cv2.medianBlur(image, 3)
    return 255 - image

#generate box coordinates
def get_block_index(image_shape, yx, block_size): 
    y = np.arange(max(0, yx[0]-block_size), min(image_shape[0], yx[0]+block_size))
    x = np.arange(max(0, yx[1]-block_size), min(image_shape[1], yx[1]+block_size))
    return np.meshgrid(y, x)

#binarization(only highlight features as white) from the median value
def adaptive_median_threshold(img_in):
    med = np.median(img_in)
    # Initializes an all-black image (img_out).
    # Then sets pixels close to the median (background) to white (255).
    med = np.median(img_in)
    img_out = np.zeros_like(img_in)
    img_out[img_in - med < DELTA] = 255
    kernel = np.ones((3,3),np.uint8)
    img_out = 255 - cv2.dilate(255 - img_out,kernel,iterations = 2)
    return img_out

#divide data into region(possibly based on resolution ?)
#Then process each region with the former function
def block_image_process(image, block_size):
    out_image = np.zeros_like(image)
    for row in range(0, image.shape[0], block_size):
        for col in range(0, image.shape[1], block_size):
            idx = (row, col)
            block_idx = get_block_index(image.shape, idx, block_size)
            out_image[block_idx] = adaptive_median_threshold(image[block_idx])
    return out_image

#Execution pipeline
def process_image(img):
    image_in = preprocess(img)
    image_out = block_image_process(image_in, BLOCK_SIZE)
    return image_out

#ensure the foreground traces has a gradient, 
#or else ridge detection might fail
#the more the pixel differes from local min, the fainter it is
#(remember that we fill the traces as white, so stronger trace = lower intensity here)

#sigmoid function：smooth out the values between 0 and 1
def sigmoid(x, orig, rad):
    k = np.exp((x - orig) * 5 / rad)
    return k / (k + 1.)

#combine local blocks
def combine_block(img_in, mask):
    # pre-fill the masked region of img_out to black
    # (i.e. background). The mask is retrieved from previous section.
    img_out = np.zeros_like(img_in)
    img_out[mask == 255] = 255
    fimg_in = img_in.astype(np.float32)
 # Then, store the foreground (white) in the `idx` array. 
 # If there are none (i.e. just background), we move on to the next block.
    idx = np.where(mask == 0)
    if idx[0].shape[0] == 0:
        img_out[idx] = img_in[idx]
        return img_out
 # clip the image block to the masked intensity range
    lo = fimg_in[idx].min()
    hi = fimg_in[idx].max()
    v = fimg_in[idx] - lo #shifted pixel values -> as they now start at low
    r = hi - lo  # range
# get estimation of foreground and background by binariz.(with otsu) -> for sigmoid
    img_in_idx = img_in[idx]
    ret3,th3 = cv2.threshold(img_in[idx],0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
# -> normalize and apply sigmoid to have smooth boundaries
# uses the black pixels from Otsu's binary output to estimate the boundary intensity 
    #that’s still considered "background" -> set as center of sigmoid
    bound_value = np.max(img_in_idx[th3[:, 0] == 255])
    bound_value = (bound_value - lo) / (r + 1e-5)
    f = (v / (r + 1e-5))
    f = sigmoid(f, bound_value + 0.05, 0.2)
# re-normalize the result to the range [0..255]
    img_out[idx] = (255. * f).astype(np.uint8)
    return img_out

# do the combination routine on local blocks, so that the scaling
# parameters of Sigmoid function can be adjusted block-to-block
def combine_block_image_process(image, mask, block_size):
    out_image = np.zeros_like(image)
    for row in range(0, image.shape[0], block_size):
        for col in range(0, image.shape[1], block_size):
            idx = (row, col)
            block_idx = get_block_index(image.shape, idx, block_size)
            out_image[block_idx] = combine_block(
                image[block_idx], mask[block_idx])
    return out_image

# The main function of this section. Executes the whole pipeline.
def combine_process(img, mask):
    image_out = combine_block_image_process(img, mask, 20)
    cv2.imwrite('/Users/lamsk/combined_output_1.png', image_out)
    print("Save successful")
    return image_out

mask = process_image(image_input)
combine_process(image_input, mask)  
