use intervaltree::IntervalTree;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs::File;
use std::io::BufReader;
use std::ops::Range;
use std::path::{Path, PathBuf};
use tokio::fs;
use tokio::io::AsyncWriteExt;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CVE {
    pub cve_id: String,
    pub severity: String,
}

#[derive(Debug)]
pub struct CVEIndex {
    data: HashMap<String, IntervalTree<u32, CVE>>,
}

#[derive(Debug, Clone, Eq, PartialEq, Ord, PartialOrd)]
struct Version(Vec<u32>);

impl Version {
    fn parse(s: &str) -> Self {
        Version(s.split('.').map(|x| x.parse().unwrap_or(0)).collect())
    }
}

fn version_to_int(version: &Version) -> u32 {
    let parts = &version.0;

    parts.iter().take(3).fold(0, |acc, x| acc * 1000 + x)
}

#[derive(Debug, Deserialize)]
struct Root {
    fkie_nvd: Vec<(String, CVEEntry)>,
}

#[derive(Debug, Deserialize)]
struct CVEEntry {
    id: String,
    metrics: Option<Metrics>,
    configurations: Option<Vec<Configuration>>,
}

#[derive(Debug, Deserialize)]
struct Metrics {
    #[serde(rename = "cvssMetricV2")]
    cvss_v2: Option<Vec<CVSSMetric>>,
}

#[derive(Debug, Deserialize)]
struct CVSSMetric {
    #[serde(rename = "baseSeverity")]
    base_severity: Option<String>,
}

#[derive(Debug, Deserialize)]
struct Configuration {
    nodes: Vec<ConfigNode>,
}

#[derive(Debug, Deserialize)]
struct ConfigNode {
    #[serde(rename = "cpeMatch")]
    cpe_match: Vec<CPEMatch>,
}

#[derive(Debug, Deserialize)]
struct CPEMatch {
    vulnerable: bool,
    criteria: String,
    #[serde(rename = "versionStartIncluding")]
    version_start_incl: Option<String>,
    #[serde(rename = "versionEndExcluding")]
    version_end_excl: Option<String>,
    #[serde(rename = "versionEndIncluding")]
    version_end_incl: Option<String>,
}

impl CVEIndex {
    pub fn build_from_json_file(path: &Path) -> Self {
        let file = File::open(path).expect("Cannot open JSON file");
        let reader = BufReader::new(file);
        let parsed: Root = serde_json::from_reader(reader).expect("Invalid JSON structure");

        let mut raw_ranges: HashMap<String, Vec<(Range<u32>, CVE)>> = HashMap::new();

        for (_key, entry) in parsed.fkie_nvd {
            let cve_id = entry.id.clone();
            let severity = entry
                .metrics
                .as_ref()
                .and_then(|m| m.cvss_v2.as_ref())
                .and_then(|v| v.first())
                .and_then(|v| v.base_severity.clone())
                .unwrap_or_else(|| "UNKNOWN".to_string());

            if let Some(configs) = entry.configurations {
                for config in configs {
                    for node in config.nodes {
                        for cpe in node.cpe_match {
                            if !cpe.vulnerable {
                                continue;
                            }

                            let Some(product) = extract_product(&cpe.criteria) else {
                                continue;
                            };

                            let product = product.to_lowercase();

                            let start = match cpe.version_start_incl.as_deref() {
                                Some(s) => version_to_int(&Version::parse(s)),
                                None => match extract_version(&cpe.criteria) {
                                    Some(s) => version_to_int(&Version::parse(&s)),
                                    None => 0,
                                },
                            };

                            let end = match (
                                cpe.version_end_excl.as_deref(),
                                cpe.version_end_incl.as_deref(),
                            ) {
                                (Some(excl), _) => version_to_int(&Version::parse(excl)),
                                (_, Some(incl)) => version_to_int(&Version::parse(incl)) + 1,
                                _ => match extract_version(&cpe.criteria) {
                                    Some(s) => version_to_int(&Version::parse(&s)) + 1,
                                    None => 999_999_999,
                                },
                            };

                            if start >= end {
                                continue;
                            }

                            let cve = CVE {
                                cve_id: cve_id.clone(),
                                severity: severity.clone(),
                            };

                            raw_ranges
                                .entry(product)
                                .or_default()
                                .push((start..end, cve));
                        }
                    }
                }
            }
        }

        let data = raw_ranges
            .into_iter()
            .map(|(k, v)| (k, IntervalTree::from_iter(v)))
            .collect();

        CVEIndex { data }
    }

    pub fn find_cves(&self, product: &str, version: &str) -> Vec<CVE> {
        let version_num = version_to_int(&Version::parse(version));
        let Some(tree) = self.data.get(&product.to_lowercase()) else {
            return vec![];
        };

        let mut seen = HashSet::new();
        let mut results = Vec::new();

        for entry in tree.query_point(version_num) {
            let cve = entry.value.clone();
            if seen.insert(&entry.value.cve_id) {
                results.push(cve);
            }
        }

        results
    }
}

fn extract_product(cpe: &str) -> Option<String> {
    // cpe:2.3:a:f5:nginx:
    let parts: Vec<&str> = cpe.split(':').collect();
    if parts.len() > 4 && parts[4].eq("http_server") {
        Some(parts[4].to_string())
    } else {
        None
    }
}

fn extract_version(cpe: &str) -> Option<String> {
    let parts: Vec<&str> = cpe.split(':').collect();
    if parts.len() > 5 && !parts[5].eq("*") {
        Some(parts[5].to_string())
    } else {
        None
    }
}

pub async fn fetch_and_cache_json(vendor: &str, product: &str) -> PathBuf {
    let url = format!("https://cve.circl.lu/api/search/{vendor}/{product}");
    let cache_dir = Path::new("./cache/cve-data");
    let cache_file = cache_dir.join(format!("{vendor}_{product}.json"));

    if cache_file.exists() {
        println!("Using cached file: {}", cache_file.display());
        return cache_file;
    }

    println!("Fetching from: {url}");
    let response = reqwest::get(&url).await.expect("Failed to fetch CVE data");
    let text = response.text().await.expect("Failed to read response");

    fs::create_dir_all(cache_dir)
        .await
        .expect("Failed to create cache directory");

    let mut file = fs::File::create(&cache_file)
        .await
        .expect("Failed to write cache file");
    file.write_all(text.as_bytes())
        .await
        .expect("Failed to write JSON data");

    println!("Cached to: {}", cache_file.display());
    cache_file
}
