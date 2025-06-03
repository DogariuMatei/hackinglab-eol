use std::collections::HashMap;

use chrono::NaiveDate;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sled::Db;

use crate::cve_checker::CVE;

#[derive(Debug, Serialize, Deserialize)]
pub struct EOLProductInfo {
    pub product: String,
    pub version: String,
    pub inferred_version: String,
    pub is_eol: bool,
    pub eol_from: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cves: Option<Vec<CVE>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EOLInfo {
    pub version_str: String,
    pub is_version_enough: bool,
    pub has_known_products: bool,
    pub count: u32,
    pub is_eol: bool,
    pub eol_from: Option<String>,
    pub products: Vec<EOLProductInfo>,
}

pub struct EOLChecker {
    db: Db,
}

impl EOLChecker {
    pub fn new() -> Self {
        EOLChecker {
            db: sled::open("./cache/eol-cache").unwrap(),
        }
    }

    pub async fn check_eol(&self, versions: HashMap<String, u32>) -> Vec<EOLInfo> {
        let mut info = vec![];
        for (version_str, count) in versions {
            let extracted = extract_versions(&version_str);

            let mut eol_versions = Vec::new();
            let mut is_eol = false;
            let mut eol_from: Option<String> = None;
            let mut is_version_enough = true;

            for (product, version) in &extracted {
                if let Some((inferred_version, eol_status, eol_date)) =
                    fetch_eol_info(&self.db, product, version).await
                {
                    if eol_status {
                        is_eol = true;

                        if let Some(new_date_str) = &eol_date {
                            let new_date = NaiveDate::parse_from_str(new_date_str, "%Y-%m-%d").ok();
                            let existing_date = eol_from
                                .clone()
                                .and_then(|d| NaiveDate::parse_from_str(&d, "%Y-%m-%d").ok());

                            if existing_date.map_or(true, |d| new_date < Some(d)) {
                                eol_from = Some(new_date_str.clone());
                            }
                        }
                    }
                    eol_versions.push(EOLProductInfo {
                        product: product.clone(),
                        version: version.clone(),
                        inferred_version,
                        is_eol: eol_status,
                        eol_from: eol_date,
                        cves: None,
                    });
                } else {
                    is_version_enough = false;
                }
            }

            if !is_version_enough && is_eol {
                // as we still have enough info
                is_version_enough = true;
            }

            info.push(EOLInfo {
                version_str: version_str.to_string(),
                is_version_enough,
                has_known_products: has_known_products(&version_str),
                count,
                is_eol,
                eol_from,
                products: eol_versions,
            });
        }

        info
    }
}

// TODO: improve to also find "nginx" without "/version"
fn extract_versions(server_string: &str) -> Vec<(String, String)> {
    let re = Regex::new(r"(\w+(?:-\w+)?)/(\d+(?:\.\d+)+(?:-\w+)?)").unwrap();
    let mut results = Vec::new();

    for cap in re.captures_iter(server_string) {
        let name = cap[1].to_string();
        let version = cap[2].to_string();

        let mapped = check_and_replace_known_labels(&name);
        results.push((mapped.to_string(), version));
    }

    results
}

fn has_known_products(server_string: &str) -> bool {
    let str = server_string.to_lowercase();
    return str.contains("apache");
    // str.contains("apache")
    // || str.contains("php")
    // || str.contains("microsoft-iis")
    // || str.contains("microsoft-httpapi")
    // || str.contains("nginx")
    // || str.contains("mod_python")
    // || str.contains("python")
    // || str.contains("mod_ssl")
    // || str.contains("openssl");
}

fn check_and_replace_known_labels(name: &str) -> &str {
    match name.to_lowercase().as_str() {
        "apache" => "apache-http-server",
        // "php" => "php",
        // "microsoft-iis" | "microsoft-httpapi" => "windows-server",
        // "nginx" => "nginx",
        // "mod_python" | "python" => "python",
        // "mod_ssl" | "openssl" => "openssl",
        _ => name,
    }
}

pub async fn fetch_eol_info(
    db: &Db,
    product: &str,
    version: &str,
) -> Option<(String, bool, Option<String>)> {
    let cache_key = format!("eol:{}:{}", product, version);
    if let Ok(Some(cached)) = db.get(&cache_key) {
        if let Ok(cached_str) = std::str::from_utf8(&cached) {
            if cached_str == "NOT_FOUND" {
                return None;
            }
            if let Ok(json) = serde_json::from_str::<Value>(cached_str) {
                let inferred_version = json.get("cycle")?.as_str()?.to_string();
                let is_eol = json.get("isEol")?.as_bool()?;
                let eol_from = json
                    .get("eolFrom")
                    .and_then(|v| v.as_str())
                    .map(String::from);
                return Some((inferred_version, is_eol, eol_from));
            }
        }
    }

    let full_json_key = format!("eol-json:{}", product);
    let json_data = if let Ok(Some(cached)) = db.get(&full_json_key) {
        if cached == b"NOT_FOUND" {
            return None;
        }
        Some(serde_json::from_slice::<Value>(&cached).ok()?)
    } else {
        let url = format!("https://endoflife.date/api/{}.json", product);
        let res = match reqwest::get(&url).await.unwrap().json::<Value>().await.ok() {
            Some(res) => Some(res),
            None => {
                db.insert(&full_json_key, b"NOT_FOUND").ok();
                None
            }
        }?;
        let serialized = serde_json::to_vec(&res).ok()?;
        db.insert(&full_json_key, serialized).ok()?;
        Some(res)
    }?;

    let cycle = match find_matching_cycle(&json_data, version) {
        CycleMatch::Exact(data) => data,
        CycleMatch::InferredEol(data) => data,
        CycleMatch::InferredNotEol => {
            db.insert(cache_key, b"NOT_FOUND").ok()?;
            return None;
        }
        CycleMatch::NotFound => {
            db.insert(cache_key, b"NOT_FOUND").ok()?;
            return None;
        }
    };

    let is_eol = cycle
        .get("eol")
        .and_then(|e| chrono::NaiveDate::parse_from_str(e.as_str()?, "%Y-%m-%d").ok())
        .map(|eol_date| eol_date < chrono::Utc::now().naive_utc().date())
        .unwrap_or(false);

    let inferred_version = cycle.get("cycle")?.as_str()?.to_string();

    let eol_info = json!({
        "cycle": inferred_version,
        "isEol": is_eol,
        "eolFrom": cycle.get("eol"),
    });

    let serialized = serde_json::to_string(&eol_info).ok()?;
    db.insert(cache_key, serialized.as_bytes()).ok()?;

    Some((
        inferred_version,
        is_eol,
        cycle.get("eol").and_then(|v| v.as_str()).map(String::from),
    ))
}

#[derive(Debug)]
pub enum CycleMatch {
    Exact(Value),
    InferredEol(Value),
    InferredNotEol,
    NotFound,
}

pub fn find_matching_cycle(json_data: &Value, version: &str) -> CycleMatch {
    let releases = json_data.as_array().unwrap();

    // 1. Try exact match (e.g. 1.0.5)
    if let Some(exact) = releases
        .iter()
        .find(|entry| entry.get("cycle").unwrap().as_str().unwrap() == version)
    {
        return CycleMatch::Exact(exact.clone());
    }

    // 2. Try shortened versions (1.0.5 → 1.0 → 1)
    let mut parts: Vec<&str> = version.split('.').collect();
    while parts.len() > 1 {
        parts.pop();
        let shortened = parts.join(".");
        if let Some(entry) = releases
            .iter()
            .find(|entry| entry.get("cycle").unwrap().as_str().unwrap() == shortened)
        {
            return CycleMatch::Exact(entry.clone());
        }
    }

    // 3. Try prefix match (e.g. 5.6 → 5.6.1, 5.6.5)
    let sub_matches: Vec<&Value> = releases
        .iter()
        .filter(|entry| {
            entry
                .get("cycle")
                .unwrap()
                .as_str()
                .unwrap()
                .starts_with(version)
        })
        .collect();

    if !sub_matches.is_empty() {
        let now = chrono::Utc::now().naive_utc().date();

        let all_eol = sub_matches.iter().all(|entry| {
            entry
                .get("eol")
                .and_then(|v| v.as_str())
                .and_then(|d| NaiveDate::parse_from_str(d, "%Y-%m-%d").ok())
                .map(|eol_date| eol_date < now)
                .unwrap_or(false)
        });

        if all_eol {
            let latest = sub_matches.into_iter().max_by_key(|entry| {
                entry.get("releaseDate").and_then(|d| {
                    NaiveDate::parse_from_str(d.as_str().unwrap_or(""), "%Y-%m-%d").ok()
                })
            });
            if let Some(entry) = latest {
                return CycleMatch::InferredEol(entry.clone());
            }
        } else {
            return CycleMatch::InferredNotEol;
        }
    }

    // 4. No match found at all
    CycleMatch::NotFound
}
