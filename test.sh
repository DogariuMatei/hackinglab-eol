cat "./data_filip/AS8315/Port80/zgrab_resultsAS8315.json" | jq -c \
    'select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
     | {server: .data.http.result.response.headers.server[0], ip: .ip}' \
    | jq -s '.' > "./data_filip/AS8315/Port80/clean_versions.json"