use nix::sys::prctl::set_pdeathsig;
use nix::sys::signal::Signal;
use std::{
    collections::HashMap,
    error::Error,
    fs::{self, File},
    io::{BufRead, BufReader, Write},
    os::unix::process::CommandExt,
    path::Path,
    process::{Child, Command, Stdio},
    sync::{Arc, Mutex},
};

use log::info;
use serde_json::Value;

pub trait VersionScanner {
    fn scan_versions(
        &self,
        ips_file: &str,
    ) -> Result<HashMap<String, u32>, Box<dyn Error + Send + Sync>>;
}

pub struct ZGrab2 {
    cache_dir: String,
    command: Vec<String>,
}

impl ZGrab2 {
    pub fn with_command<S: Into<String>>(command: Vec<S>) -> Self {
        ZGrab2 {
            cache_dir: "./cache/version-scanner/zgrab2".to_string(),
            command: command.into_iter().map(Into::into).collect(),
        }
    }
}

impl VersionScanner for ZGrab2 {
    fn scan_versions(
        &self,
        ips_file: &str,
    ) -> Result<HashMap<String, u32>, Box<dyn Error + Send + Sync>> {
        fs::create_dir_all(&self.cache_dir)?;

        let file_stem = Path::new(ips_file)
            .file_stem()
            .ok_or("Invalid input file name")?
            .to_string_lossy();
        let output_path = format!("{}/{}.txt", self.cache_dir, file_stem);
        let summary_path = format!("{}/{}.data", self.cache_dir, file_stem);

        if Path::new(&summary_path).exists() {
            info!("Using cached zgrab2 output");
            return load_summary_from_file(&summary_path);
        }

        let child_process: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));

        let mut args = self.command.clone();
        args.push("--output-file".to_string());
        args.push(output_path.to_string());

        let mut cmd = Command::new("zgrab2");
        cmd.args(args);
        cmd.stdin(Stdio::piped());
        cmd.stdout(Stdio::piped());

        unsafe {
            cmd.pre_exec(|| {
                set_pdeathsig(Signal::SIGTERM).expect("Failed to set pdeathsig");
                Ok(())
            });
        }

        let mut child = cmd.spawn()?;

        {
            let stdin = child.stdin.as_mut().ok_or("Failed to open stdin")?;
            let input_file = File::open(ips_file)?;
            let reader = BufReader::new(input_file);
            for line in reader.lines() {
                writeln!(stdin, "{}", line?)?;
            }
        }

        {
            let mut lock = child_process.lock().unwrap();
            *lock = Some(child);
        }
        if let Some(mut child) = child_process.lock().unwrap().take() {
            let _ = child.wait()?;
        }

        let result = parse_versions_from_file(&output_path)?;
        save_summary_to_file(&summary_path, &result)?;
        Ok(result)
    }
}

fn parse_versions_from_file(
    path: &str,
) -> Result<HashMap<String, u32>, Box<dyn Error + Send + Sync>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut version_map = HashMap::new();

    for line in reader.lines() {
        let line = line?;
        let json: Value = match serde_json::from_str(&line) {
            Ok(val) => val,
            Err(_) => continue,
        };

        let server_opt = json
            .pointer("/data/http/result/response/headers/server")
            .and_then(|v| v.get(0))
            .and_then(Value::as_str);

        if let Some(server) = server_opt {
            *version_map.entry(server.to_string()).or_insert(0) += 1;
        }
    }

    Ok(version_map)
}

fn save_summary_to_file(
    path: &str,
    summary: &HashMap<String, u32>,
) -> Result<(), Box<dyn Error + Send + Sync>> {
    let mut file = File::create(path)?;
    for (server, count) in summary {
        writeln!(file, "{}: {}", server, count)?;
    }
    Ok(())
}

fn load_summary_from_file(
    path: &str,
) -> Result<HashMap<String, u32>, Box<dyn Error + Send + Sync>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut map = HashMap::new();

    for line in reader.lines() {
        let line = line?;
        if let Some((server, count)) = line.split_once(": ") {
            if let Ok(count) = count.trim().parse::<u32>() {
                map.insert(server.to_string(), count);
            }
        }
    }

    Ok(map)
}

pub struct HttpVersionScanner {
    inner_scanner: ZGrab2,
}

impl HttpVersionScanner {
    pub fn new(port: u16, use_https: bool) -> Self {
        let mut command = vec![
            "--senders".to_string(),
            "5".to_string(), // amount of senders (defaults to 1000)
            "http".to_string(),
            "--user-agent".to_string(),
            "Mozilla/5.0".to_string(),
            "--port".to_string(),
            port.to_string(),
        ];

        if use_https {
            command.push("--use-https".to_string());
        }

        HttpVersionScanner {
            inner_scanner: ZGrab2::with_command(command),
        }
    }
}

impl VersionScanner for HttpVersionScanner {
    fn scan_versions(
        &self,
        ips_file: &str,
    ) -> Result<HashMap<String, u32>, Box<dyn Error + Send + Sync>> {
        self.inner_scanner.scan_versions(ips_file)
    }
}
