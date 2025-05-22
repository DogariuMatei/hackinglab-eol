use std::{error::Error, path::Path};

use async_trait::async_trait;
use log::info;
use tokio::{fs, io::AsyncReadExt};

#[async_trait]
pub trait AsnLookup {
    /// Lookup the IP prefixes associated with a given ASN.
    async fn lookup_asn(&self, asn: &str) -> Result<Vec<String>, Box<dyn Error + Send + Sync>>;
}

pub fn validate_asn(asn: &str) -> Result<String, Box<dyn Error + Send + Sync>> {
    if !asn.starts_with("AS") || asn.len() < 3 {
        Err("Invalid ASN format".into())
    } else {
        Ok(asn.to_string())
    }
}

pub struct CachedAsnLookup<API: AsnLookup + Send + Sync> {
    cache_dir: String,
    api: API,
}

impl Default for CachedAsnLookup<HackerTargetAPI> {
    fn default() -> Self {
        CachedAsnLookup {
            cache_dir: "./cache/asn".to_string(),
            api: HackerTargetAPI::new(),
        }
    }
}

impl<T: AsnLookup + Send + Sync> CachedAsnLookup<T> {
    pub async fn lookup_asn(&self, asn: &str) -> Result<String, Box<dyn Error + Send + Sync>> {
        info!("Looking up {} for IP prefixes", asn);

        let cache_path = Path::new(&self.cache_dir).join(format!("{}.txt", asn));
        if cache_path.exists() {
            let prefixes = read_ip_prefixes_from_file(&cache_path).await?;
            info!("Using cached version of the IP prefixes");
            info!("Found {} IP prefixes", prefixes.len());

            return Ok(cache_path.to_string_lossy().into_owned());
        }

        let result = self.api.lookup_asn(asn).await?;

        fs::create_dir_all(&self.cache_dir).await?;
        fs::write(&cache_path, result.join("\n")).await?;

        Ok(cache_path.to_string_lossy().into_owned())
    }
}

pub struct HackerTargetAPI;

impl HackerTargetAPI {
    fn new() -> Self {
        HackerTargetAPI
    }
}

#[async_trait]
impl AsnLookup for HackerTargetAPI {
    async fn lookup_asn(&self, asn: &str) -> Result<Vec<String>, Box<dyn Error + Send + Sync>> {
        let url = format!("https://api.hackertarget.com/aslookup/?q={}", asn);
        info!("Requesting IP prefixes via {}", url);
        let response = reqwest::get(&url).await?.text().await?;

        let ip_prefixes: Vec<String> = response
            .lines()
            .skip(1)
            .map(|line| line.to_string())
            .collect();

        info!("Found {} IP prefixes", ip_prefixes.len());

        Ok(ip_prefixes)
    }
}

pub async fn read_ip_prefixes_from_file(
    path: &Path,
) -> Result<Vec<String>, Box<dyn Error + Send + Sync>> {
    let mut file = fs::File::open(path).await?;
    let mut contents = String::new();
    file.read_to_string(&mut contents).await?;

    let ip_prefixes = contents
        .lines()
        .map(|line| line.to_string())
        .collect::<Vec<_>>();

    info!("Using cached version of the IP prefixes");
    info!("Found {} IP prefixes", ip_prefixes.len());

    Ok(ip_prefixes)
}
