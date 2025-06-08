import os
import json
import csv
import matplotlib.pyplot as plt
import numpy as np

def read_data(folder_path):
    port_data = {}

    # Define the path to the extra_data subfolder
    extra_data_folder = os.path.join(folder_path, "extra_data")

    for filename in os.listdir(folder_path):
        if filename.endswith(".json") and not filename.startswith("combined_"):
            port = os.path.splitext(filename)[0]
            eol_file = os.path.join(folder_path, filename)
            zmap_file = os.path.join(extra_data_folder, f"combined_zmap_{port}.csv")
            clean_versions_file = os.path.join(extra_data_folder, f"combined_clean_versions_{port}.json")

            try:
                # Read total responses from zmap_output
                with open(zmap_file, "r", newline="", encoding="utf-8") as f:
                    total_responses = sum(1 for _ in f) - 1  # Subtract header row

                # Read responses with versions from clean_versions
                with open(clean_versions_file, "r", encoding="utf-8") as f:
                    clean_versions = json.load(f)
                    responses_with_versions = len(clean_versions)

                # Read meaningful versions and EOL devices from server_eol_success
                with open(eol_file, "r", encoding="utf-8") as f:
                    meaningful_versions_data = json.load(f)
                    meaningful_versions = len(meaningful_versions_data)
                    eol_devices = sum(1 for entry in meaningful_versions_data if entry.get("is_eol") is True)

                # Store data for this port
                port_data[port] = {
                    "total_responses": total_responses,
                    "responses_with_versions": responses_with_versions,
                    "meaningful_versions": meaningful_versions,
                    "eol_devices": eol_devices,
                }

            except Exception as e:
                print(f"Error processing files for port {port}: {e}")

    return port_data

def plot_cumulative_bar_chart(port_data):
    ports = list(port_data.keys())
    total_responses = [port_data[port]["total_responses"] for port in ports]
    responses_with_versions = [port_data[port]["responses_with_versions"] for port in ports]
    meaningful_versions = [port_data[port]["meaningful_versions"] for port in ports]
    eol_devices = [port_data[port]["eol_devices"] for port in ports]

    # Calculate the bottom positions for stacking
    responses_with_versions_bottom = np.array(total_responses) - np.array(responses_with_versions)
    meaningful_versions_bottom = responses_with_versions_bottom + np.array(responses_with_versions) - np.array(meaningful_versions)
    eol_devices_bottom = meaningful_versions_bottom + np.array(meaningful_versions) - np.array(eol_devices)

    # Plot the cumulative bar chart
    plt.figure(figsize=(12, 6))
    bars = plt.bar(ports, total_responses, label="Total Responses (zmap)", color="#b3cde3", edgecolor="black")
    plt.bar(ports, responses_with_versions, bottom=responses_with_versions_bottom, label="Responses with Versions (zgrab)", color="#8c96c6", edgecolor="black")
    plt.bar(ports, meaningful_versions, bottom=meaningful_versions_bottom, label="Meaningful Versions", color="#8856a7", edgecolor="black")
    plt.bar(ports, eol_devices, bottom=eol_devices_bottom, label="EOL Devices", color="#810f7c", edgecolor="black")

    # Add total numbers on top of each bar
    for bar, total in zip(bars, total_responses):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,  # Position above the bar
                 f"{total}", ha="center", va="bottom", fontsize=11, fontweight="bold")

    # Add labels and legend
    plt.xlabel("Ports")
    plt.ylabel("Number of Responses")
    plt.title("Cumulative Bar Chart of Responses by Port")
    plt.legend(fontsize=12, title_fontsize=14)
    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.show()

def plot_percentage_stacked_bar_chart(port_data):
    ports = list(port_data.keys())
    total_responses = np.array([port_data[port]["total_responses"] for port in ports])
    responses_with_versions = np.array([port_data[port]["responses_with_versions"] for port in ports])
    meaningful_versions = np.array([port_data[port]["meaningful_versions"] for port in ports])
    eol_devices = np.array([port_data[port]["eol_devices"] for port in ports])

    # Calculate percentages
    total_responses_safe = np.where(total_responses == 0, 1, total_responses)
    responses_with_versions_percent = (responses_with_versions / total_responses_safe) * 100
    meaningful_versions_percent = (meaningful_versions / total_responses_safe) * 100
    eol_devices_percent = (eol_devices / total_responses_safe) * 100
    others_percent = 100 - responses_with_versions_percent

    # Calculate bottom positions for stacking
    responses_with_versions_bottom = others_percent
    meaningful_versions_bottom = others_percent + (responses_with_versions_percent - meaningful_versions_percent)
    eol_devices_bottom = meaningful_versions_bottom + (meaningful_versions_percent - eol_devices_percent)

    plt.figure(figsize=(12, 6))

    # Plot the 100% stacked bar chart
    plt.bar(ports, others_percent, label="Responses without Versions", color="#b3cde3", edgecolor="black")
    plt.bar(ports, responses_with_versions_percent - meaningful_versions_percent, bottom=responses_with_versions_bottom, label="Responses with Versions (zgrab)", color="#8c96c6", edgecolor="black")
    plt.bar(ports, meaningful_versions_percent - eol_devices_percent, bottom=meaningful_versions_bottom, label="Meaningful Versions", color="#8856a7", edgecolor="black")
    plt.bar(ports, eol_devices_percent, bottom=eol_devices_bottom, label="EOL Devices", color="#810f7c", edgecolor="black")

    # Add percentage labels inside each bar segment
    for i, port in enumerate(ports):
        if eol_devices_percent[i] > 0:
            plt.text(i, eol_devices_bottom[i] + eol_devices_percent[i] / 2,
                     f"{eol_devices_percent[i]:.1f}%", ha="center", va="center", fontsize=9, color='white')
        if (meaningful_versions_percent[i] - eol_devices_percent[i]) > 0:
            plt.text(i, meaningful_versions_bottom[i] + (meaningful_versions_percent[i] - eol_devices_percent[i]) / 2,
                     f"{(meaningful_versions_percent[i] - eol_devices_percent[i]):.1f}%", ha="center", va="center", fontsize=9, color='white')
        if (responses_with_versions_percent[i] - meaningful_versions_percent[i]) > 0:
            plt.text(i, responses_with_versions_bottom[i] + (responses_with_versions_percent[i] - meaningful_versions_percent[i]) / 2,
                     f"{(responses_with_versions_percent[i] - meaningful_versions_percent[i]):.1f}%", ha="center", va="center", fontsize=9, color='white')
        if others_percent[i] > 0:
            plt.text(i, others_percent[i] / 2,
                     f"{others_percent[i]:.1f}%", ha="center", va="center", fontsize=9, color='black')

    # Add labels and legend
    plt.xlabel("Ports")
    plt.ylabel("Percentage (%)")
    plt.title("100% Stacked Bar Chart of Responses by Port")
    plt.legend(fontsize=10, title_fontsize=12, loc="center left", bbox_to_anchor=(1, 0.5))  # Move legend to the side
    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(np.arange(0, 101, 10), fontsize=12)
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\combined_data"

    # Read data from the folder
    port_data = read_data(folder_path)
    #
    # # Plot the cumulative bar chart
    # plot_cumulative_bar_chart(port_data)

    # Plot the percentage bar chart
    plot_percentage_stacked_bar_chart(port_data)