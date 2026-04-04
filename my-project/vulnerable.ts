// SONAR S4325: Overuse of 'any' type
// SONAR S2637: Non-null assertion abuse
// SONAR S6571: Unsafe optional property access

// ❌ S4325 - Avoid using 'any'
function processData(data: any): any {
  return data.value;
}

let result: any = processData({});
const items: any[] = [];

// ❌ S2637 - Non-null assertion operator abuse
interface User {
  name: string;
  address?: {
    city: string;
    zip?: string;
  };
}

function getCity(user: User): string {
  return user.address!.city; // may throw at runtime
}

function getZip(user: User): string {
  return user.address!.zip!; // double non-null assertion
}

// ❌ S6571 - Unsafe optional access
function getCityUnsafe(user: User): string {
  return user.address.city; // 'address' is possibly undefined
}

// ❌ S4325 - any in function parameters
function merge(a: any, b: any) {
  return { ...a, ...b };
}

// ❌ Hardcoded secret in TypeScript
const JWT_SECRET: string = "hardcoded-jwt-secret-key-123";
const DB_PASSWORD: string = "supersecretpassword";
