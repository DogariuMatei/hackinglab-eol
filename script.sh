
sudo zmap -p 993 -o "zmap_output.csv" -r 128 -w txts/TRANSIP-IPs.txt


cat zmap_output.csv | zgrab2 http --user-agent "Mozilla/5.0" --senders=20 --endpoint "/" --output-file zgrab_results.json

cat zmap_output.csv | zgrab2 ftp --port 21  --senders=20 --output-file zgrab_results.json

cat zmap_output.csv | zgrab2 smtp -t 20 --senders=20 --port 465 --output-file zgrab_results.json

cat zmap_output.csv | zgrab2 imap --imaps -t 20 --senders=20 --port 993 --output-file zgrab_results.json


cat zgrab_results.json | jq -c 'select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
| {server: .data.http.result.response.headers.server[0], ip: .ip}' | jq -s '.' > versions_transip_21.json

cat versions_transip_21.json | jq 'group_by(.server) | map({server: .[0].server, count: length}) | sort_by(-.count) | .[] | "\(.server): \(.count)"' > count_transip_21.json
