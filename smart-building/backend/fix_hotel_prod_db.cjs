const { Client } = require('ssh2');

const conn = new Client();

console.log('🔄 Connexion au serveur de production pour mise à jour BDD HOTEL...');

conn.on('ready', () => {
    console.log('✅ Connecté via SSH');

    const script = `
    export PATH=$PATH:/usr/local/bin:/usr/bin:~/.nvm/versions/node/$(ls ~/.nvm/versions/node | tail -n 1)/bin
    [ -s "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"

    cat << 'EOF' > /opt/gravity-lab/smart-building/backend/check_hotel_prod.js
const Database = require('better-sqlite3');
const db = new Database('./smartbuild_v3.sqlite');
try {
  let org = db.prepare("SELECT * FROM organizations WHERE id LIKE '22222222%'").get();
  if (org) {
    db.prepare("UPDATE organizations SET name = 'Casa de Papel HOTEL', type = 'Hospitality' WHERE id = ?").run(org.id);
    console.log('Prod Org updated:', org.name, '-> Casa de Papel HOTEL');
    
    let site = db.prepare("SELECT * FROM site WHERE organizationId = ? AND name LIKE '%HOTEL%'").get(org.id);
    if (!site) {
      db.prepare("INSERT INTO site (id, name, type, address, city, country, postalCode, organizationId) VALUES (lower(hex(randomblob(16))), 'Casa de Papel HOTEL', 'Hospitality', '1 rue de la Paix', 'Paris', 'France', '75000', ?)").run(org.id);
      console.log('Prod Site added.');
    } else {
      console.log('Prod Site already exists:', site.name);
    }
  } else {
    console.log('Prod Org 22222222 not found.');
  }
} catch (e) {
  console.error(e);
}
db.close();
EOF
    
    cd /opt/gravity-lab/smart-building/backend
    node check_hotel_prod.js
    rm check_hotel_prod.js
    
    echo "🎉 Mise à jour BDD terminée !"
    `;

    conn.exec(script, (err, stream) => {
        if (err) throw err;
        stream.on('close', (code, signal) => {
            conn.end();
        }).on('data', (data) => {
            process.stdout.write(data);
        }).stderr.on('data', (data) => {
            process.stderr.write(data);
        });
    });
}).connect({
    host: '76.13.59.115',
    port: 22,
    username: 'root',
    password: "5FPuD8)DpuHH8'Ic.(r#"
});
