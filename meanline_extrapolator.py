import json
import numpy
import matplotlib.pyplot as plt
import pandas as pd
LOWER_LIMIT = 0.8 #constraint on slope filtering
UPPER_LIMIT = 1.5

f = open('/Users/lamsk/Downloads/outputs/wavy_example/meanlines.json')
data = json.load(f)

y_coord = []
x_coord = []

for feature in data['features']:
    coord = feature['geometry']['coordinates']
    y_coord.append((coord[0][1], coord[1][1]))


for feature in data['features']:
    coord = feature['geometry']['coordinates']
    x_coord.append(coord[1][0])

x_axis = sum(x_coord)/len(x_coord)

slopelst = []
for i in y_coord:
    slope = (i[1]-i[0])/x_axis
    slopelst.append(slope)

slopelstpd = pd.Series(slopelst)
Q1 = slopelstpd.quantile(0.4)
Q3 = slopelstpd.quantile(0.8)
filter_slopelst = slopelstpd[(slopelstpd >= Q1) & (slopelstpd <= Q3)]
print('filtered slopes',filter_slopelst)
mean_slope = sum(filter_slopelst)/len(filter_slopelst)
# print(slopelst)
print('mean slope', mean_slope)

new_feature = []
new_y_coords = [] 
for feature in data['features']:
    slope = (feature['geometry']['coordinates'][1][1] - feature['geometry']['coordinates'][0][1])/x_axis
    if mean_slope * LOWER_LIMIT <= slope <= mean_slope * UPPER_LIMIT:
        new_feature.append(feature)
        new_y_coords.append(feature['geometry']['coordinates'][1][1])
print(new_feature)

for i in range(1, len(new_feature)):
    l = 0
    r = i
    left = new_feature[l]
    right = new_feature[r]
    while l<r:
        if(new_feature[r]['geometry']['coordinates'][1][1]) >= (new_feature[l]['geometry']['coordinates'][1][1]):
            l += 1
        else:
            new_feature[r]['geometry']['coordinates'], new_feature[l]['geometry']['coordinates'] = new_feature[l]['geometry']['coordinates'],new_feature[r]['geometry']['coordinates']
            r = i
            l += 1
new_y_coords.sort()


intervals = []
for i in range(1, len(new_y_coords)):
    interval = new_y_coords[i] - new_y_coords[i-1]
    intervals.append(interval)
print('intervals', intervals)


intervalspd = pd.Series(intervals)
Q1 = intervalspd.quantile(0.25)
Q3 = intervalspd.quantile(0.75)
intervals_filtered = intervalspd[(intervalspd >= Q1) & (intervalspd <= Q3)]
intervals_filtered = intervals_filtered.tolist()

listlen = len(intervals_filtered)
print(listlen)
med_int = 0
if listlen % 2 == 0:
    med_int += (intervals_filtered[int(listlen/2)] + intervals_filtered[int(listlen/2 + 1)])/2
else:
    med_int += intervals_filtered[int((listlen + 1)/2)]
print(med_int)


# might delete the id of the original code directly -> adding complexity
# directly append lines based on coordniates
def line_add(line, num):
    for n in range(1, num ):
        coord = [
            [line['geometry']['coordinates'][0][0], line['geometry']['coordinates'][0][1] + n*(med_int)], [line['geometry']['coordinates'][1][0], line['geometry']['coordinates'][1][1] + n*(med_int)]
        ]
        added_feature = {'type': 'Feature', 'id':i+n, 'geometry': {'type': 'LineString', 'coordinates': coord}, 'properties': {}}
        new_feature.append(added_feature)

for i in range(0,len(intervals)):
    if intervals[i] >= med_int * 1.1 or intervals[i] <= med_int*0.9 : 
    #What should be a good threshold ?
        num_add = round(intervals[i]/med_int)
        line_add(new_feature[i], num_add)


output_path = '/Users/lamsk/Downloads/wave_meanlines_new.json'

with open(output_path,  'w') as f:
    json.dump({
  "type": "FeatureCollection",
  "features":new_feature}, f, indent= 2)

f2 = open(output_path)
data = json.load(f2)
data_pts = []
for feature in data['features']:
    coords = feature['geometry']['coordinates']
    data_pts.append(coords)

for line in data_pts:
    x_vals, y_vals = zip(*line)
    plt.plot(x_vals,y_vals,color = 'cyan')

plt.title('Meanlines plots')
plt.show()