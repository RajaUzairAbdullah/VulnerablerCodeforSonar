// SONAR S5696: XSS - Unsafe innerHTML
// SONAR S4721: OS Command Injection
// SONAR S5852: ReDoS - Vulnerable Regex

const { exec } = require('child_process');

// ❌ S5696 - XSS via innerHTML
function renderUserInput() {
  const name = new URLSearchParams(window.location.search).get('name');
  document.getElementById('output').innerHTML = name;

  const comment = document.querySelector('#comment').value;
  document.getElementById('preview').innerHTML = comment;
}

// ❌ S4721 - OS Command Injection
function getFileContents(filename) {
  exec('cat ' + filename, (err, stdout) => {
    console.log(stdout);
  });
}

function listDirectory(userPath) {
  exec('ls -la ' + userPath, (err, stdout, stderr) => {
    console.log(stdout);
  });
}

// ❌ S5852 - ReDoS vulnerable regex
function validateEmail(input) {
  const pattern = /^(a+)+$/;
  return pattern.test(input);
}

function validateUsername(input) {
  const pattern = /([a-zA-Z]+)*@/;
  return pattern.test(input);
}
