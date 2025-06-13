import json

def extract_rabbitmq_info(json_data):
    results = []

    for entry in json_data:
        if entry is None or not isinstance(entry, dict):
            continue

        ip = entry.get('ip')
        amqp_data = entry.get('data', {}).get('amqp091', {})

        if amqp_data.get('status') == 'success':
            server_props = amqp_data.get('result', {}).get('server_properties', {})
            product = server_props.get('product')
            version = server_props.get('version')

            if product == 'RabbitMQ' and version:
                server_info = f"{product}/{version}"
                results.append({
                    "ip": ip,
                    "server": server_info
                })

    return results


def process_file(file_name, output_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        json_data = []

        for line in file:
            line = line.strip()
            if line:
                try:
                    json_data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    rabbitmq_info = extract_rabbitmq_info(json_data)

    print(f"Output for {file_name}:")
    print(json.dumps(rabbitmq_info, indent=2))

    with open(output_name, 'w', encoding='utf-8') as outfile:
        json.dump(rabbitmq_info, outfile, indent=2)
