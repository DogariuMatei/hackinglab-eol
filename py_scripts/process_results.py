import json
import os


def process_json_file():
    # Hardcoded file names
    input_file = "http_8080_results.json"
    output_file = "clean_versions_with_ip_domains_8080.json"

    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        return

    # Process the data line by line (JSONL format)
    result = []
    processed = 0
    error_count = 0

    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        for line_number, line in enumerate(f, 1):
            try:
                # Skip empty lines
                line = line.strip()
                if not line:
                    continue

                # Parse the JSON object from this line
                entry = json.loads(line)
                processed += 1

                # Access the server headers path
                headers = entry.get('data', {}).get('http', {}).get('result', {}).get('response', {}).get('headers', {})
                server = headers.get('server')

                # Exact match to the jq logic:
                # select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
                if server is not None and len(server) > 0 and server[0] is not None:
                    # Get IP address
                    ip = entry.get('ip')

                    # Add to result with exact format {server: server[0]} but also include ip
                    result.append({
                        'ip': ip,
                        'server': server[0]
                    })
            except json.JSONDecodeError as e:
                error_count += 1
                if error_count < 5:  # Only show the first few errors
                    print(f"Error parsing JSON at line {line_number}: {e}")
            except Exception as e:
                error_count += 1
                if error_count < 5:
                    print(f"Error processing line {line_number}: {e}")

    # Write the result to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Successfully processed {len(result)} entries with server headers out of {processed} total entries")
    print(f"Encountered {error_count} errors during processing")
    print(f"Output saved to {output_file}")


if __name__ == "__main__":
    process_json_file()