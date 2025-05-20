
sudo zmap -p 80 -o "zmap_output.csv" -r 128 -w zgrab_targets.csv

# i canot get this damn zgrab to be callable from anywhere on my machine => you all have to suffer bc of my incompetence

cat /home/doga/Desktop/HackingLab/hackinglab-eol/zgrab_targets.csv | ./zgrab2 http --user-agent "Mozilla/5.0" --endpoint "/" --output-file /home/doga/Desktop/HackingLab/hackinglab-eol/zgrab_results.json


cat results.json | jq -c 'select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
| {server: .data.http.result.response.headers.server[0], ip: .ip}' | jq -s '.' > clean_versions.json

cat clean_versions.json | jq 'group_by(.server) | map({server: .[0].server, count: length}) | sort_by(-.count) | .[] | "\(.server): \(.count)"' > clean_count.json
