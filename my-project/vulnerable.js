// SONAR S2077: SQL Injection
// SONAR S5122: Permissive CORS
// SONAR S2068: Hardcoded Credentials
// SONAR S2245: Weak Random
// SONAR S108:  Empty Catch Block

const express = require('express');
const app = express();

// ❌ S2077 - SQL Injection
app.get('/user', (req, res) => {
  const username = req.query.username;
  const query = "SELECT * FROM users WHERE username = '" + username + "'";
  db.execute(query);
});

app.get('/order', (req, res) => {
  const orderId = req.query.id;
  const query = "SELECT * FROM orders WHERE id = " + orderId;
  db.execute(query);
});

// ❌ S2068 - Hardcoded Credentials
const config = {
  db_password: "admin123",
  api_key: "sk-abc123secret",
  jwt_secret: "mysupersecretjwtkey",
};

// ❌ S2245 - Weak Random (not cryptographically secure)
function generateOTP() {
  return Math.floor(Math.random() * 999999);
}

function generateSessionToken() {
  return Math.random().toString(36).substring(2);
}

// ❌ S5122 - Permissive CORS
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  next();
});

// ❌ S108 - Empty Catch Block
async function fetchData(url) {
  try {
    const res = await fetch(url);
    return await res.json();
  } catch (e) {
    // exception swallowed silently
  }
}

app.listen(3000);
