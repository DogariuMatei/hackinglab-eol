use default_net::get_default_gateway;
use log::info;
use nix::sys::prctl::set_pdeathsig;
use nix::sys::signal::Signal;
use regex::Regex;
use std::{
    error::Error,
    fs,
    io::{BufRead, BufReader},
    os::unix::process::CommandExt,
    path::Path,
    process::{Child, Command, Stdio},
    sync::{Arc, Mutex},
};

pub struct Zmap {
    cache_dir: String,
    gateway_mac: String,
    rate: u16,
}

impl Zmap {
    pub fn new() -> Self {
        Zmap {
            cache_dir: "./cache/zmap".to_string(),
            gateway_mac: get_default_gateway().unwrap().mac_addr.to_string(),
            rate: 128,
        }
    }

    pub fn scan_ip_prefixes(
        &self,
        file: &str,
        port: u16,
    ) -> Result<String, Box<dyn Error + Send + Sync>> {
        info!("Scanning with zmap on port {}", port);

        let child_process: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));

        let output_file = Path::new(file)
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .replace(".txt", &format!("-{}.txt", port));

        let output_file_with_dir = format!("{}/{}", self.cache_dir, output_file);
        if Path::new(&output_file_with_dir).exists() {
            info!("Using cached zmap output");
            return Ok(output_file_with_dir);
        }

        fs::create_dir_all(&self.cache_dir)?;

        let mut cmd = Command::new("zmap");
        cmd.args(&[
            "-p",
            &port.to_string(),
            "-r",
            &self.rate.to_string(),
            "-w",
            file,
            "-G",
            &self.gateway_mac,
            "-o",
            &output_file_with_dir,
        ]);
        cmd.stderr(Stdio::piped());

        unsafe {
            cmd.pre_exec(|| {
                set_pdeathsig(Signal::SIGTERM).expect("Failed to set pdeathsig");
                Ok(())
            });
        }

        let zmap_cmd = cmd.spawn()?;

        {
            let mut lock = child_process.lock().unwrap();
            *lock = Some(zmap_cmd);
        }

        let stderr = child_process
            .lock()
            .unwrap()
            .as_mut()
            .expect("Child process missing")
            .stderr
            .take()
            .expect("Failed to take stderr");

        let reader = BufReader::new(stderr);
        let hitrate_re = Regex::new(r"hitrate:\s*([\d.]+%)")?;
        let send_re = Regex::new(r"send:\s*([\d]+)")?;

        let mut hitrate = String::from("unknown");
        let mut send_reqs = String::from("unknown");

        for line in reader.lines() {
            let line = line?;
            println!("{}", line);

            if let Some(caps) = hitrate_re.captures(&line) {
                hitrate = caps[1].to_string();
                if let Some(caps) = send_re.captures(&line) {
                    send_reqs = caps[1].to_string();
                }
            }
        }

        if let Some(mut child) = child_process.lock().unwrap().take() {
            let _ = child.wait();
        }

        let info_file = output_file.replace(".txt", ".info");
        fs::write(
            &format!("{}/{}", self.cache_dir, info_file),
            &format!("{} out of {}", hitrate, send_reqs),
        )?;

        Ok(output_file_with_dir)
    }
}
