use reqwest::blocking::Client;
use serde_json::json;

let client = Client::new();
let res = client.post("https://api.openai.com/v1/chat/completions")
    .bearer_auth("YOUR_OPENAI_API_KEY")
    .json(&json!({
        "model": "gpt-4o-mini",
        "messages": [{"role":"user", "content": input}]
    }))
    .send().unwrap()
    .json::<serde_json::Value>().unwrap();

let ai_response = res["choices"][0]["message"]["content"].as_str().unwrap();
println!("AI says: {}", ai_response);
