use anyhow::Result;
use tokio::time::{sleep, Duration};

use crate::web;

pub async fn run_desktop(host: &str, port: u16) -> Result<()> {
    let browser_host = if host == "0.0.0.0" || host == "::" {
        "127.0.0.1"
    } else {
        host
    };
    let url = format!("http://{}:{}", browser_host, port);
    println!("Starting desktop GUI mode at {}", url);

    let open_url = url.clone();
    tokio::spawn(async move {
        sleep(Duration::from_millis(700)).await;
        if let Err(err) = webbrowser::open(&open_url) {
            eprintln!("Could not open browser automatically: {}", err);
            eprintln!("Open this URL manually: {}", open_url);
        }
    });

    web::run_web(host, port).await
}
