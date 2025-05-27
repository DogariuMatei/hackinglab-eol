#!/bin/bash

# === CONFIGURATION ===
SUFFIX="AS1101"
PORTS=("80" "443" "8080" "6379" "5432" "3306" "27017") # List of ports 3 http, Redis, postgre, mariadb mysql, mongo
RATE="1024"

# === PATH SETUP ===
BASE_DIR="data_filip/${SUFFIX}"
mkdir -p "$BASE_DIR"

for PORT in "${PORTS[@]}"; do
  PORT_DIR="${BASE_DIR}/${PORT}"
  mkdir -p "$PORT_DIR"

  ZMAP_OUTPUT="${PORT_DIR}/zmap_output${SUFFIX}.csv"
  IP_LIST="data_filip/${SUFFIX}/IP${SUFFIX}.txt"
  ZGRAB_OUTPUT="${PORT_DIR}/zgrab_results${SUFFIX}.json"
  CLEAN_VERSIONS="${PORT_DIR}/clean_versions${SUFFIX}.json"
  CLEAN_COUNT="${PORT_DIR}/clean_count${SUFFIX}.json"

  # === ZMAP ===
  sudo zmap -p "$PORT" -o "$ZMAP_OUTPUT" -r "$RATE" -w "$IP_LIST"

  # === ZGRAB2 ===
  cat "$ZMAP_OUTPUT" | ../zgrab2/zgrab2  http \
    --user-agent "Mozilla/5.0" \
    --endpoint "/" \
    --output-file "$ZGRAB_OUTPUT"

  # === FILTER & CLEAN JSON ===
  cat "$ZGRAB_OUTPUT" | jq -c \
    'select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
     | {server: .data.http.result.response.headers.server[0], ip: .ip}' \
    | jq -s '.' > "$CLEAN_VERSIONS"

  # === GROUP AND COUNT ===
  cat "$CLEAN_VERSIONS" | jq \
    'group_by(.server)
     | map({server: .[0].server, count: length})
     | sort_by(-.count)
     | .[]
     | "\(.server): \(.count)"' > "$CLEAN_COUNT"

  # === EOL CHECK ===
  python3 py_scripts/best_eol_check.py "$CLEAN_VERSIONS" "$PORT_DIR"
done