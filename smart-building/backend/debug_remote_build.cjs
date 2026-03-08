const { Client } = require('ssh2');

const conn = new Client();
conn.on('ready', () => {
    conn.exec('export PATH=$PATH:/usr/local/bin:/usr/bin:~/.nvm/versions/node/$(ls ~/.nvm/versions/node | tail -n 1)/bin; [ -s "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"; cd /opt/gravity-lab/smart-building/backend && npm run build', (err, stream) => {
        if (err) throw err;
        stream.on('close', (code, signal) => {
            conn.end();
        }).on('data', (data) => {
            console.log('STDOUT: ' + data);
        }).stderr.on('data', (data) => {
            console.log('STDERR: ' + data);
        });
    });
}).connect({
    host: '76.13.59.115',
    port: 22,
    username: 'root',
    password: "5FPuD8)DpuHH8'Ic.(r#"
});
