use std::{
    collections::HashMap,
    error::Error,
    fs::{self, File},
    io::{BufRead, BufReader, Write},
    path::Path,
    process::{Command, Stdio},
};

use log::info;

use crate::CHILD_PROCESSES;

pub trait VersionScanner {
    fn scan_versions(
        &self,
        ips_file: &str,
    ) -> Result<HashMap<String, u32>, Box<dyn Error + Send + Sync>>;
}

pub struct ZGrab2 {
    cache_dir: String,
    command: Vec<String>,
    senders: u16,
    port: u16,
}

impl ZGrab2 {
    pub fn with_command<I, S>(command: I, port: u16) -> Self
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        ZGrab2 {
            cache_dir: "./cache/version-scanner/zgrab2".to_string(),
            command: command
                .into_iter()
                .map(|s| s.as_ref().to_string())
                .collect(),
            senders: 20,
            port: port,
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

        if Path::new(&output_path).exists() {
            info!("Using cached zgrab2 output");
            return Ok(HashMap::new());
        }

        let mut args = self.command.clone();
        args.insert(0, "--senders".to_string());
        args.insert(1, self.senders.to_string());
        args.push("--output-file".to_string());
        args.push(output_path.to_string());
        args.push("--port".to_string());
        args.push(self.port.to_string());
        args.push("-t".to_string());
        args.push("5".to_string());

        let mut cmd = Command::new("zgrab2");
        cmd.args(args);
        cmd.stdin(Stdio::piped());
        cmd.stderr(Stdio::piped());

        let mut child = cmd.spawn()?;
        let stderr = child.stderr.take().expect("Failed to take stderr");
        {
            let mut processes = CHILD_PROCESSES.lock().unwrap();
            processes.push(child);
        }

        std::thread::spawn(move || {
            let reader = BufReader::new(stderr);
            for line in reader.lines() {
                let line = line.unwrap();
                info!("[zgrab2] {}", line);
            }
        });

        {
            let mut processes = CHILD_PROCESSES.lock().unwrap();
            let mut stdin = processes
                .last_mut()
                .and_then(|c| c.stdin.take())
                .ok_or("Failed to access child stdin")?;

            let input_file = File::open(ips_file)?;
            let reader = BufReader::new(input_file);
            for line in reader.lines() {
                writeln!(stdin, "{}", line?)?;
            }
        }

        if let Some(mut child) = CHILD_PROCESSES.lock().unwrap().pop() {
            let _ = child.wait()?;
        }

        Ok(HashMap::new())
    }
}

pub struct HttpVersionScanner {
    inner_scanner: ZGrab2,
}

impl HttpVersionScanner {
    pub fn new(port: u16, use_https: bool) -> Self {
        let mut command = vec![
            "http".to_string(),
            "--user-agent".to_string(),
            "Mozilla/5.0".to_string(),
        ];

        if use_https {
            command.push("--use-https".to_string());
        }

        HttpVersionScanner {
            inner_scanner: ZGrab2::with_command(command, port),
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
