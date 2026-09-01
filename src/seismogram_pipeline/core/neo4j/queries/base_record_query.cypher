MATCH (b:Box)
WHERE b.stationData IS NOT NULL
WITH b, apoc.convert.fromJsonMap(b.stationData) as stationMap
UNWIND keys(stationMap) as stationCode
UNWIND stationMap[stationCode] as record
WITH record
WHERE record.recordName = $target_record_name
RETURN record