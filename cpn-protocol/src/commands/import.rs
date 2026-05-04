//! Команда импорта ключей

pub async fn import(source: String) -> Result<(), Box<dyn std::error::Error>> {
    if source.starts_with("mystvpn://") || source.starts_with("ss://") || source.starts_with("v2ray://") {
        let decoded = base64_decode(&source[source.find("://").unwrap() + 3..])?;
        println!("Parsed configuration:\n{}", String::from_utf8_lossy(&decoded));
    } else {
        let content = tokio::fs::read_to_string(&source).await?;
        println!("Configuration from file:\n{}", content);
    }
    Ok(())
}

fn base64_decode(input: &str) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    use base64::{Engine as _, engine::general_purpose};
    Ok(general_purpose::STANDARD.decode(input)?)
}