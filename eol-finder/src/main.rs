use std::{
    collections::HashMap,
    fs::{self, OpenOptions},
    path::Path,
};

use asn_lookup::CachedAsnLookup;
use clap::Parser;
use ftail::Ftail;
use itertools::Itertools;
use log::LevelFilter;
use serde_json::to_writer_pretty;
use version_scanner::{HttpVersionScanner, VersionScanner};

mod asn_lookup;
mod cve_checker;
mod eol_checker;
mod version_scanner;
mod zmap;

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    #[command(flatten)]
    ips: IPsArgs,
}

#[derive(Parser, Debug)]
#[group(required = true, multiple = false)]
struct IPsArgs {
    /// ASN to look up (example: AS12345)
    #[arg(long, value_parser=asn_lookup::validate_asn)]
    asn: Option<String>,

    /// A file containing IP addresses to look up (example: ips.txt)
    #[arg(long, value_hint=clap::ValueHint::FilePath)]
    custom_ips: Option<String>,
}

#[tokio::main]
async fn main() {
    let scanner_map = build_scanner_map();

    let args = Args::parse();

    fs::create_dir_all("logs").unwrap();
    Ftail::new()
        .console(LevelFilter::Info)
        .daily_file(Path::new("logs"), LevelFilter::Debug)
        .init()
        .unwrap();

    // get the IPs to scan
    let ip_prefixes_path = if let Some(asn) = &args.ips.asn {
        let asn_lookup = CachedAsnLookup::default();
        asn_lookup
            .lookup_asn(asn)
            .await
            .expect("Failed to lookup ASN")
    } else {
        args.ips.custom_ips.unwrap()
    };

    let zmap = zmap::Zmap::new();
    let eol_checker = eol_checker::EOLChecker::new();

    let json_path = cve_checker::fetch_and_cache_json("apache", "http_server").await;
    let index = cve_checker::CVEIndex::build_from_json_file(&json_path);

    for (port, scanners) in scanner_map {
        // zmap scan the IPs
        let zmap_output = zmap
            .scan_ip_prefixes(ip_prefixes_path.as_str(), port)
            .expect("Failed to scan IP prefixes");

        // scan versions
        for scanner in scanners {
            let versions = scanner.scan_versions(&zmap_output).unwrap();

            // check EOL
            let mut eol_info = eol_checker.check_eol(versions).await;
            // save EOL report
            let file_stem = Path::new(&zmap_output)
                .file_stem()
                .unwrap()
                .to_string_lossy();
            fs::create_dir_all("./cache/versions").unwrap();
            let report_path = format!("./cache/versions/{}.json", file_stem);
            let file = OpenOptions::new()
                .create(true)
                .write(true)
                .truncate(true)
                .open(report_path)
                .unwrap();
            to_writer_pretty(file, &eol_info).unwrap();

            // check for CVEs
            for eol in eol_info.iter_mut() {
                for product in eol.products.iter_mut() {
                    if product.product == "apache-http-server" {
                        product.cves = Some(index.find_cves("http_server", &product.version));
                        println!(
                            "{} {:?}",
                            eol.version_str,
                            product.cves.clone().unwrap().len()
                        );
                        println!(
                            "{}",
                            product
                                .cves
                                .clone()
                                .unwrap()
                                .iter()
                                .map(|cve| cve.cve_id.to_owned())
                                .sorted()
                                .collect::<Vec<String>>()
                                .join(", ")
                        );
                    }
                }
            }

            fs::create_dir_all("./cache/results").unwrap();
            let results_path = format!("./cache/results/{}-apache.json", file_stem);
            let file = OpenOptions::new()
                .create(true)
                .write(true)
                .truncate(true)
                .open(results_path)
                .unwrap();
            to_writer_pretty(file, &eol_info).unwrap();
        }
    }
}

fn build_scanner_map() -> HashMap<u16, Vec<Box<dyn VersionScanner>>> {
    let mut map: HashMap<u16, Vec<Box<dyn VersionScanner>>> = HashMap::new();

    let http_scanner = HttpVersionScanner::new(80, false);
    map.insert(80, vec![Box::new(http_scanner)]);

    // let https_scanner = HttpVersionScanner::new(443, true);
    // map.insert(443, vec![Box::new(https_scanner)]);

    map
}
