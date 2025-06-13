use std::{collections::HashMap, fs, path::Path, process::Child, sync::Mutex};

use asn_lookup::CachedAsnLookup;
use clap::Parser;
use ftail::Ftail;
use lazy_static::lazy_static;
use log::{LevelFilter, info};
use version_scanner::{HttpVersionScanner, VersionScanner, ZGrab2};

mod asn_lookup;
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

lazy_static! {
    pub static ref CHILD_PROCESSES: Mutex<Vec<Child>> = Mutex::new(Vec::new());
}

#[tokio::main]
async fn main() {
    setup_logs();

    for asn in vec!["AS60781", "AS24586", "AS50673", "AS39572"] {
        // get the IPs to scan
        let asn_lookup = CachedAsnLookup::default();
        let ip_prefixes_path = asn_lookup
            .lookup_asn(asn)
            .await
            .expect("Failed to lookup ASN");
        let zmap = zmap::Zmap::new();

        let scanner_map = build_scanner_map();

        for (port, scanners) in scanner_map {
            info!("Working on {}", port);
            // zmap scan the IPs
            let zmap_output = zmap
                .scan_ip_prefixes(ip_prefixes_path.as_str(), port)
                .expect("Failed to scan IP prefixes");

            // scan versions
            for scanner in scanners {
                scanner.scan_versions(&zmap_output).unwrap();
            }
        }
    }
}

fn setup_logs() {
    fs::create_dir_all("logs").unwrap();
    Ftail::new()
        .console(LevelFilter::Info)
        .daily_file(Path::new("logs"), LevelFilter::Info)
        .init()
        .unwrap();
}

fn build_scanner_map() -> HashMap<u16, Vec<Box<dyn VersionScanner>>> {
    let mut map: HashMap<u16, Vec<Box<dyn VersionScanner>>> = HashMap::new();

    map.insert(80, vec![Box::new(HttpVersionScanner::new(80, false))]);
    map.insert(8080, vec![Box::new(HttpVersionScanner::new(8080, false))]);
    map.insert(443, vec![Box::new(HttpVersionScanner::new(443, true))]);

    map.insert(
        3306,
        vec![], // vec![Box::new(ZGrab2::with_command(vec!["mysql"], 3306))],
    ); // change

    map.insert(
        1521,
        vec![Box::new(ZGrab2::with_command(vec!["oracle"], 1521))],
    );

    map.insert(587, vec![Box::new(ZGrab2::with_command(vec!["smtp"], 587))]);
    map.insert(
        465,
        vec![Box::new(ZGrab2::with_command(vec!["smtp", "--smtps"], 465))],
    );

    map.insert(21, vec![Box::new(ZGrab2::with_command(vec!["ftp"], 21))]);

    map.insert(
        27017,
        vec![], // vec![Box::new(ZGrab2::with_command(vec!["mongodb"], 27017))],
    ); // change to custom one

    map.insert(
        1433,
        vec![Box::new(ZGrab2::with_command(vec!["mssql"], 1433))],
    );

    map.insert(
        995,
        vec![Box::new(ZGrab2::with_command(vec!["pop3", "--pop3s"], 995))],
    );

    map.insert(
        993,
        vec![Box::new(ZGrab2::with_command(vec!["imap", "--imaps"], 993))],
    );

    map.insert(
        6379,
        vec![], // vec![Box::new(ZGrab2::with_command(vec!["redis"], 6379))],
    ); // change

    map.insert(
        5671,
        vec![Box::new(ZGrab2::with_command(
            vec!["amqp091", "--use-tls"],
            5671,
        ))],
    );

    map.insert(
        5672,
        vec![Box::new(ZGrab2::with_command(vec!["amqp091"], 5672))],
    );

    // map.insert(25, vec![Box::new(ZGrab2::with_command(vec!["smtp"], 25))]);
    map
}
