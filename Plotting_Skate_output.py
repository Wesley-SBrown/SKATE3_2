import matplotlib.pyplot as plt
import json
import cv2 as cv


# Image in background, enable this
# fig, ax = plt.subplots()
# image = cv.imread('/Users/lamsk/Downloads/010170_0639_0023_04.png')
# plt.imshow(image)

f1 = open('ROI')
roi = json.load(f1)
roi_pts = []
for coords in roi['geometry']['coordinates']:
    roi_pts.append(coords)
labeled = False
for line in roi_pts:
    x_values, y_values = zip(*line)
    if not labeled:
        plt.plot(x_values,y_values,color = 'purple', label='ROI')
        labeled = True
    else:
        plt.plot(x_values,y_values,color = 'purple')


f2 = open('MEANLINES')
data0 = json.load(f2)
data0_pts = []
for feature in data0['features']:
    coords = feature['geometry']['coordinates']
    data0_pts.append(coords)

labeled1 = False
labeled2 = False
for line in data0_pts:
    x_vals, y_vals = zip(*line)
    if not labeled1:
        plt.plot(x_vals,y_vals,color = 'cyan', label='SKATE Output')
        labeled1 = True
    else:
        plt.plot(x_vals,y_vals,color = 'cyan')

    if line not in data0_pts:
        if not labeled2:
            plt.plot(x_vals,y_vals,color = 'green', label='Deleted Slopes')
            labeled2 = True
        else:
            plt.plot(x_vals,y_vals,color = 'green')

f3 = open('SEGMENTS')
base = json.load(f3)
base_pts = []
for feature in base['features']:
    coords = feature['geometry']['coordinates']
    base_pts.append(coords)

labeled = False
for line in base_pts:
    x_values, y_values = zip(*line)
    if not labeled:
        plt.plot(x_values,y_values,color = 'red', label='Segments')
        labeled = True
    else:
        plt.plot(x_values,y_values,color = 'red')


f4 = open('REPLOT.MEANLINES')
data = json.load(f4)
data_pts = []
for feature in data['features']:
    coords = feature['geometry']['coordinates']
    data_pts.append(coords)
data_pts.sort()
labeled = False
for line in data_pts:
    x_vals, y_vals = zip(*line)
    if not labeled:
        plt.plot(x_vals,y_vals,color = 'blue', label='Extrapolated Lines')
        labeled = True
    else:
        plt.plot(x_vals,y_vals,color = 'blue')




plt.xticks([])  # Removes x-axis tick labels
plt.yticks([])
plt.title('Compare output data')
plt.legend(loc='upper left', bbox_to_anchor=(1, 0.5))
plt.tight_layout()  

plt.show()
