const db = require('better-sqlite3')('../../smartbuild_v3_vps.sqlite', { readonly: true });
const fs = require('fs');
const data = {
    orgs: db.prepare('SELECT id, name FROM organizations').all(),
    sites: db.prepare('SELECT id, name, organizationId FROM site').all(),
    zones: db.prepare('SELECT id, name, siteId, floor FROM zone').all()
};
fs.writeFileSync('../../db_dump.json', JSON.stringify(data, null, 2));
console.log("Dump saved to db_dump.json");
