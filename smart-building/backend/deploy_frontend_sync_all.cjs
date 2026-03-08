const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const srcDir = '../frontend/src';
const destDir = '/opt/gravity-lab/smart-building/frontend/src';

const conn = new Client();

function getAllFiles(dirPath, arrayOfFiles) {
    const files = fs.readdirSync(dirPath);
    arrayOfFiles = arrayOfFiles || [];
    files.forEach(function (file) {
        if (fs.statSync(dirPath + "/" + file).isDirectory()) {
            arrayOfFiles = getAllFiles(dirPath + "/" + file, arrayOfFiles);
        } else {
            arrayOfFiles.push(path.join(dirPath, "/", file));
        }
    });
    return arrayOfFiles;
}

const allFiles = getAllFiles(path.resolve(srcDir));

console.log('🔄 Connexion au serveur de production pour sync complète du frontend...');

conn.on('ready', () => {
    console.log('✅ Connecté via SSH');
    conn.sftp((err, sftp) => {
        if (err) throw err;

        console.log('📤 Synchronisation de src vers la prod...');

        const uploadFile = (index) => {
            if (index >= allFiles.length) {
                console.log('✅ Synchronisation terminée.');

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
                
                echo "🎉 Déploiement complet Hot-Swap terminé !"
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
                return;
            }

            const localFilePath = allFiles[index];
            const relativePath = path.relative(path.resolve(srcDir), localFilePath);
            const remoteFilePath = `${destDir}/${relativePath.replace(/\\/g, '/')}`;
            const remoteFileDir = path.dirname(remoteFilePath);

            // Ensure directory exists
            sftp.mkdir(remoteFileDir, { recursive: true }, (err) => {
                // Ignore directory already exists error
                sftp.fastPut(localFilePath, remoteFilePath, (err) => {
                    if (err) {
                        console.error('Erreur sur upload de', relativePath, err.message);
                    } else {
                        console.log('Uploaded:', relativePath);
                    }
                    uploadFile(index + 1);
                });
            });
        };

        uploadFile(0);
    });
}).connect({
    host: '76.13.59.115',
    port: 22,
    username: 'root',
    password: "5FPuD8)DpuHH8'Ic.(r#"
});
