const { Client } = require('ssh2');

const conn = new Client();

console.log('🔄 Checking Prod DB Site Table Schema...');

conn.on('ready', () => {
    const script = `
    export PATH=$PATH:/usr/local/bin:/usr/bin:~/.nvm/versions/node/$(ls ~/.nvm/versions/node | tail -n 1)/bin
    [ -s "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"

    cat << 'EOF' > /opt/gravity-lab/smart-building/backend/list_site_columns.js
const Database = require('better-sqlite3');
const db = new Database('./smartbuild_v3.sqlite');
try {
  const cols = db.prepare("PRAGMA table_info(site)").all();
  console.log('Columns:', cols.map(c => c.name));
} catch (e) {
  console.error(e);
}
db.close();
EOF
    
    cd /opt/gravity-lab/smart-building/backend
    node list_site_columns.js
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
