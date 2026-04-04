// SONAR S3776: Cognitive Complexity Too High
// SONAR S107:  Too Many Parameters
// SONAR S108:  Empty Catch Block
// SONAR S1481: Unused Variables

// ❌ S3776 - Cognitive complexity exceeds threshold
function process(input) {
  if (input) {
    if (input.length > 0) {
      for (const c of input) {
        if (!isNaN(c)) {
          if (c > 5) {
            if (c !== 9) {
              if (c % 2 === 0) {
                return "complex even";
              } else {
                return "complex odd";
              }
            }
          }
        }
      }
    }
  }
  return "simple";
}

// ❌ S107 - Too many parameters
function createOrder(name, address, city, zip, country, email, phone, notes) {
  console.log("Creating order for: " + name);
}

function registerUser(firstName, lastName, email, phone, address, city, country, password) {
  console.log("Registering: " + email);
}

// ❌ S1481 - Unused variables
function computeTotal(items) {
  const tax = 0.2;
  const discount = 0.1;   // never used
  const currency = "USD"; // never used
  return items.reduce((sum, item) => sum + item.price, 0) * (1 + tax);
}
