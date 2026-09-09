MATCH (b:Box)
WHERE b.fromDate > b.throughDate
RETURN b.boxNum AS boxNum, b.fromDate AS fromDate, b.throughDate AS throughDate;