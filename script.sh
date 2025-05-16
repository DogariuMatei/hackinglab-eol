
sudo zmap -p 80 -o "zmap_output.csv" -r 1024 -w TRANSIP-IPs.txt


cat /home/doga/Desktop/HackingLab/Proj/output.csv | ./zgrab2 http --user-agent "Mozilla/5.0" --endpoint "/" --output-file /home/doga/Desktop/HackingLab/Proj/zgrab_results.json

cat results.json | jq '[select(.data.http.status == "success")
| select(.data.http.result.response.headers.server != null)
| select(.data.http.result.response.headers.server[]
| ascii_downcase | contains("oracle"))
| {ip: .ip, oracle_version: .data.http.result.response.headers.server[]}]' | jq -s 'flatten | map(select(. != null))' > clean_versions.json


cat results.json | jq -c 'select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
| {server: .data.http.result.response.headers.server[0], ip: .ip}' | jq -s '.' > clean_versions.json

cat clean_versions.json | jq 'group_by(.server) | map({server: .[0].server, count: length}) | sort_by(-.count) | .[] | "\(.server): \(.count)"' > clean_count.json
