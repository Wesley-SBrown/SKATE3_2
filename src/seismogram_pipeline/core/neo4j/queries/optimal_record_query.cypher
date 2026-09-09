MATCH (s:Station {stationCode: $station_code})<-[:CONTAINS_DATA_FOR]-(b:Box)
WHERE b.fromDate <= $date 
  AND b.throughDate >= $date
  AND b.stationData CONTAINS $target_record_name
WITH b, apoc.convert.fromJsonMap(b.stationData)[$station_code] AS records
WHERE records IS NOT NULL
UNWIND records AS record
WITH b, record
WHERE record.recordName = $target_record_name
RETURN b.id AS boxId, b.boxNum AS boxNum, record
LIMIT 1