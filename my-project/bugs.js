// SONAR S2259: Null / Undefined Dereference
// SONAR S1440: == instead of ===
// SONAR S4328: Promise not awaited
// SONAR S2228: Sensitive data in console.log
// SONAR S1763: Dead / Unreachable Code

// ❌ S2259 - Null dereference
function getUserCity(users, id) {
  const user = users.find(u => u.id === id); // may return undefined
  return user.address.city;                  // TypeError risk
}

function getFirstItem(arr) {
  return arr[0].name; // no check if arr is empty
}

// ❌ S1440 - == instead of ===
function check(value) {
  if (value == null) {   // loose equality
    return true;
  }
  if (value == 0) {      // "0", false, "" all pass
    return false;
  }
  if (value == "true") { // string vs boolean confusion
    return true;
  }
}

// ❌ S4328 - Promise not awaited
async function saveUser(user) {
  db.save(user);          // promise not awaited
  console.log("saved");   // may run before save completes
}

async function deleteRecord(id) {
  db.delete(id);          // fire and forget — no error handling
}

// ❌ S2228 - Sensitive data logged
function processPayment(card) {
  console.log("Processing card: " + card.number);
  console.log("CVV: " + card.cvv);
  charge(card);
}

// ❌ S1763 - Unreachable / dead code
function calculate(x) {
  return x * 2;
  const unused = x + 1; // unreachable
}

function getLabel(status) {
  if (status === 'active') {
    return 'Active';
    console.log('returned active'); // unreachable
  }
  return 'Inactive';
}
