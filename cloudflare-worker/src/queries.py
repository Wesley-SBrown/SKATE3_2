QUERIES = {
    "optimal_record" : """
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
    """,

    "simple_date": """
        MATCH (b:Box)
        WHERE b.fromDate >= $fromDate 
        AND b.throughDate <= $toDate
        RETURN b.boxNum AS boxNum, 
            b.fromDate AS fromDate, 
            b.throughDate AS throughDate, 
            b.scannedBy AS scannedBy
        ORDER BY b.fromDate ASC;
    """,

    "advanced_search": """
        MATCH (s:Station)<-[:CONTAINS_DATA_FOR]-(b:Box)
        WHERE ($station_code IS NULL OR s.stationCode = $station_code)
          AND b.stationData IS NOT NULL
        
        // Dynamically get keys or unfold station maps depending on whether station_code is set
        WITH b, 
             CASE 
                WHEN $station_code IS NOT NULL THEN [$station_code]
                ELSE keys(apoc.convert.fromJsonMap(b.stationData))
             END AS targetStations
        
        UNWIND targetStations AS stCode
        WITH b, stCode, apoc.convert.fromJsonMap(b.stationData)[stCode] AS records
        WHERE records IS NOT NULL
        
        UNWIND records AS record
        WITH stCode, record
        WHERE ($pier IS NULL OR record.pier = $pier)
          AND ($orientation IS NULL OR record.orientation = $orientation)
          AND ($period IS NULL OR record.period = $period)
          AND ($gain IS NULL OR record.gain = $gain)
          AND ($from_date IS NULL OR record.dateTime >= $from_date)
          AND ($to_date IS NULL OR record.dateTime <= $to_date)
          
        RETURN {
            boxNum: b.boxNum,
            boxId: b.id,
            record: {
                recordName: record.recordName,
                stationCode: stCode,
                dateTime: record.dateTime,
                pier: record.pier,
                orientation: record.orientation,
                period: record.period,
                gain: record.gain
            }
        } AS result
        ORDER BY record.dateTime ASC
        LIMIT 100
    """
}