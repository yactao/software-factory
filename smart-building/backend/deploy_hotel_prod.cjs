const { Client } = require('ssh2');
const fs = require('fs');

const bFile = '../frontend/src/components/dashboard/BuildingModel.tsx';
const bContent = fs.readFileSync(bFile, 'utf8');

const conn = new Client();

console.log('🔄 Connexion au serveur de production pour mise à jour HOTEL...');

conn.on('ready', () => {
    console.log('✅ Connecté via SSH');
    conn.sftp((err, sftp) => {
        if (err) throw err;

        console.log('📤 Upload du fichier BuildingModel.tsx...');

        const stream = sftp.createWriteStream('/opt/gravity-lab/smart-building/frontend/src/components/dashboard/BuildingModel.tsx');
        stream.write(bContent);
        stream.end();

        stream.on('close', () => {
            console.log('✅ BuildingModel.tsx uploadé.');

            const script = `
            export PATH=$PATH:/usr/local/bin:/usr/bin:~/.nvm/versions/node/$(ls ~/.nvm/versions/node | tail -n 1)/bin
            [ -s "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"

            cat << 'EOF' > /tmp/check_hotel_prod.js
const Database = require('better-sqlite3');
const db = new Database('/opt/gravity-lab/smart-building/backend/smartbuild_v3.sqlite');
try {
  let org = db.prepare("SELECT * FROM organizations WHERE id LIKE '22222222%'").get();
  if (org) {
    db.prepare("UPDATE organizations SET name = 'Casa de Papel HOTEL', type = 'Hospitality' WHERE id = ?").run(org.id);
    console.log('Prod Org updated:', org.name, '-> Casa de Papel HOTEL');
    
    let site = db.prepare("SELECT * FROM site WHERE organizationId = ? AND name LIKE '%HOTEL%'").get(org.id);
    if (!site) {
      db.prepare("INSERT INTO site (id, name, type, address, city, country, postalCode, organizationId, status, createdAt, updatedAt) VALUES (lower(hex(randomblob(16))), 'Casa de Papel HOTEL', 'Hospitality', '1 rue de la Paix', 'Paris', 'France', '75000', ?, 'active', datetime('now'), datetime('now'))").run(org.id);
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
            node /tmp/check_hotel_prod.js

            echo "[FRONTEND] Recompilation..."
            cd /opt/gravity-lab/smart-building/frontend
            rm -rf .next
            npm run build
            pm2 restart gtb-frontend
            
            echo "🎉 Mises à jour BDD et Hot-Swap terminées !"
            `;

            conn.exec(script, (err, stream2) => {
                if (err) throw err;
                stream2.on('close', (code, signal) => {
                    conn.end();
                }).on('data', (data) => {
                    process.stdout.write(data);
                }).stderr.on('data', (data) => {
                    process.stderr.write(data);
                });
            });
        });
    });
}).connect({
    host: '76.13.59.115',
    port: 22,
    username: 'root',
    password: "5FPuD8)DpuHH8'Ic.(r#"
});
