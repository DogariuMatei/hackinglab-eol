import json
import pandas as pd
import matplotlib.pyplot as plt

with open("TEST-server_eol_failure_for_konstantin_zgrab_targets.json", "r") as f:
    failure_data = json.load(f)

with open("TEST-server_eol_success_for_konstantin_zgrab_targets.json", "r") as f:
    success_data = json.load(f)

df_failure = pd.DataFrame(failure_data)
df_success = pd.DataFrame(success_data)

plt.figure()
counts = [len(df_success), len(df_failure)]
labels = ['Success', 'Failure']
plt.bar(labels, counts)
plt.title('Success vs Failure Count')
plt.ylabel('Number of Records')
plt.grid(True)

plt.figure()
failure_server_counts = df_failure['server'].value_counts()
failure_server_counts.plot(kind='bar')
plt.title('Failure: Server Name Frequency')
plt.xlabel('Server Name')
plt.ylabel('Frequency')
plt.grid(True)

plt.figure()
success_server_counts = df_success['server'].value_counts()
success_server_counts.plot(kind='bar')
plt.title('Success: Server Name Frequency')
plt.xlabel('Server Name')
plt.ylabel('Frequency')
plt.grid(True)

plt.figure()
eol_counts = df_success['eol_from'].value_counts().sort_index()
eol_counts.plot(kind='bar')
plt.title('Success: EOL Date Distribution')
plt.xlabel('EOL Date')
plt.ylabel('Frequency')
plt.grid(True)

plt.figure()
version_counts = df_success['version'].value_counts()
version_counts.plot(kind='bar')
plt.title('Success: Server Version Distribution')
plt.xlabel('Version')
plt.ylabel('Frequency')
plt.grid(True)

plt.tight_layout()
plt.show()
