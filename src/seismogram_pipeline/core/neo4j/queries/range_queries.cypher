// All high-elevation stations (e.g., elevation >= 1000m) with channels and box counts
MATCH (s:Station)
WHERE s.elevation >= 1000.0
OPTIONAL MATCH (s)<-[:CONTAINS_DATA_FOR]-(b:Box)
RETURN s.stationCode AS station, 
       s.stationName AS name, 
       s.elevation AS elevation, 
       count(DISTINCT b) AS associatedBoxes
ORDER BY s.elevation DESC;

// Geographic bounding box scan (Southern California latitude/longitude slice)
MATCH (s:Station)
WHERE s.latitude >= 33.0 AND s.latitude <= 36.0
  AND s.longitude >= -119.0 AND s.longitude <= -116.0
RETURN s.stationCode AS station, s.latitude, s.longitude
ORDER BY s.latitude ASC;

MATCH (b:Box)
WHERE b.fromDate >= '1930-01-01' 
  AND b.throughDate <= '1945-12-31'
RETURN b.boxNum AS boxNum, 
       b.fromDate AS fromDate, 
       b.throughDate AS throughDate, 
       b.scannedBy AS scannedBy
ORDER BY b.fromDate ASC;


MATCH (s:Station {stationCode: $station_code})<-[:CONTAINS_DATA_FOR]-(b:Box)
WHERE b.fromDate <= '1941-07-01' 
  AND b.throughDate >= '1941-06-01'
  AND b.stationData IS NOT NULL
WITH b, apoc.convert.fromJsonMap(b.stationData)[$station_code] AS records
WHERE records IS NOT NULL
UNWIND records AS record
WITH record
WHERE record.dateTime >= '1941-06-01T00:00:00' 
  AND record.dateTime <= '1941-06-30T23:59:59'
RETURN record.recordName AS recordName, 
       record.dateTime AS dateTime, 
       record.gain AS gain, 
       record.orientation AS orientation
ORDER BY record.dateTime ASC;

MATCH (b:Box)
WHERE b.stationData IS NOT NULL
  AND b.fromDate >= '1940-01-01'
WITH b, apoc.convert.fromJsonMap(b.stationData) AS stationMap
UNWIND keys(stationMap) AS stCode
UNWIND stationMap[stCode] AS record
WITH b, stCode, record
WHERE record.fileSize >= 800000000 
   OR record.width >= 40000
RETURN b.boxNum AS box, 
       stCode AS station, 
       record.recordName AS recordName, 
       record.fileSize / (1024 * 1024) AS fileSizeMB, 
       record.width AS width, 
       record.height AS height
ORDER BY fileSizeMB DESC
LIMIT 25;


