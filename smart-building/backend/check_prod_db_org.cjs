const { Client } = require('ssh2');

const conn = new Client();

console.log('🔄 Checking Prod DB...');

conn.on('ready', () => {

    const script = `
    export PATH=$PATH:/usr/local/bin:/usr/bin:~/.nvm/versions/node/$(ls ~/.nvm/versions/node | tail -n 1)/bin
    [ -s "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"

    cat << 'EOF' > /opt/gravity-lab/smart-building/backend/list_orgs.js
const Database = require('better-sqlite3');
const db = new Database('./smartbuild_v3.sqlite');
try {
  let org = db.prepare("SELECT * FROM organization WHERE id LIKE '22222222%'").get();
  console.log('ORG in organization:', org);
} catch (e) {
  console.log('Error organization:', e.message);
}
try {
  let org2 = db.prepare("SELECT * FROM organizations WHERE id LIKE '22222222%'").get();
  console.log('ORG in organizations:', org2);
} catch (e) {
  console.log('Error organizations:', e.message);
}
db.close();
EOF
    
    cd /opt/gravity-lab/smart-building/backend
    node list_orgs.js
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
