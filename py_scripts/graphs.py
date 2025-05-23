import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the JSON file
df = pd.read_json('../data_filip/AS57043/80/server_eol_success_AS57043.json')

# Convert `eol_from` to datetime
df['eol_from'] = pd.to_datetime(df['eol_from'], errors='coerce')

# Set global font size
plt.rcParams.update({
    'font.size': 20,        # General font size
    'axes.titlesize': 20,   # Title font size
    'axes.labelsize': 20,   # X and Y label font size
    'xtick.labelsize': 16,  # X tick font size
    'ytick.labelsize': 16,  # Y tick font size
    'legend.fontsize':14   # Legend font size
})


plt.figure(figsize=(8, 5))
df['server'].value_counts().plot(kind='bar', title='Server Type Frequency', ylabel='Count', xlabel='Server')
plt.tight_layout()
plt.show()

plt.figure(figsize=(6, 6))
df['is_eol'].value_counts().plot.pie(autopct='%1.1f%%', labels=['EOL', 'Not EOL'], title='EOL Status Distribution')
plt.ylabel('')
plt.tight_layout()
plt.show()

plt.figure(figsize=(8, 5))
df['eol_from'].dropna().dt.year.value_counts().sort_index().plot(kind='bar', title='EOL Year Distribution', xlabel='Year', ylabel='Count')
plt.tight_layout()
plt.show()


plt.figure(figsize=(10, 6))
sns.countplot(data=df, x='version', hue='server')
plt.title('Version Distribution by Server Type')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


plt.figure(figsize=(8, 5))
df.groupby('server')['ip'].nunique().plot(kind='bar', title='Unique IPs Per Server Type', ylabel='Unique IPs')
plt.tight_layout()
plt.show()
