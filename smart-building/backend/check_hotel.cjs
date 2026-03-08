const Database = require('better-sqlite3');
const db = new Database('./smartbuild_v3.sqlite');
try {
  let org = db.prepare("SELECT * FROM organizations WHERE id LIKE '22222222%'").get();
  if (org) {
    db.prepare("UPDATE organizations SET name = 'Casa de Papel HOTEL', type = 'Hospitality' WHERE id = ?").run(org.id);
    console.log('Org updated:', org.name, '-> Casa de Papel HOTEL');

    let site = db.prepare("SELECT * FROM site WHERE organizationId = ? AND name LIKE '%HOTEL%'").get(org.id);
    if (!site) {
      db.prepare("INSERT INTO site (id, name, type, address, city, country, postalCode, organizationId) VALUES (lower(hex(randomblob(16))), 'Casa de Papel HOTEL', 'Hospitality', '1 rue de la Paix', 'Paris', 'France', '75000', ?)").run(org.id);
      console.log('Site added.');
    } else {
      console.log('Site already exists:', site.name);
    }
  } else {
    console.log('Org 22222222 not found in local DB.');
  }
} catch (e) {
  console.error(e);
}
db.close();
