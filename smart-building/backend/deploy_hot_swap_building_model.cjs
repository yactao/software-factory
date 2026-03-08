const { Client } = require('ssh2');

const fs = require('fs');

const frontendFile = '../frontend/src/components/dashboard/BuildingModel.tsx';
const frontendContent = fs.readFileSync(frontendFile, 'utf8');

const conn = new Client();

console.log('🔄 Connexion au serveur de production...');

conn.on('ready', () => {
    console.log('✅ Connecté via SSH');
    conn.sftp((err, sftp) => {
        if (err) throw err;

        console.log('📤 Upload du fichier modifié (BuildingModel.tsx)...');

        const fStream = sftp.createWriteStream('/opt/gravity-lab/smart-building/frontend/src/components/dashboard/BuildingModel.tsx');
        fStream.write(frontendContent);
        fStream.end();

        fStream.on('close', () => {
            console.log('✅ BuildingModel.tsx uploadé.');

            console.log('🔨 Lancement de la compilation et du redémarrage sans interruption (PM2)...');

            const script = `
            export PATH=$PATH:/usr/local/bin:/usr/bin:~/.nvm/versions/node/$(ls ~/.nvm/versions/node | tail -n 1)/bin
            [ -s "$HOME/.nvm/nvm.sh" ] && source "$HOME/.nvm/nvm.sh"

            echo "[FRONTEND] Nettoyage lock..."
            cd /opt/gravity-lab/smart-building/frontend
            rm -rf .next

            echo "[FRONTEND] Recompilation..."
            npm run build
            echo "[FRONTEND] Redémarrage..."
            pm2 restart gtb-frontend
            
            echo "🎉 Déploiement Hot-Swap terminé !"
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
        });
    });
}).connect({
    host: '76.13.59.115',
    port: 22,
    username: 'root',
    password: "5FPuD8)DpuHH8'Ic.(r#"
});
