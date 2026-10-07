const fs = require('fs'); const path = require('path');
function list(dir){ return fs.readdirSync(dir,{withFileTypes:true}).flatMap(d=>{const p=path.join(dir,d.name);return d.isDirectory()?list(p):[p];}).filter(p=>!p.includes('node_modules')&&!p.includes('.git')&&!p.includes('.next')); }
fs.mkdirSync('docs/architecture/metrics',{recursive:true});
fs.mkdirSync('patches/preview',{recursive:true});
const files=list('.').slice(0,500); // Limit to first 500 for readability
fs.mkdirSync('docs/architecture',{recursive:true});
fs.writeFileSync('docs/architecture/00_system_map.md',`# System Map\n\nTotal files scanned: ${files.length} (showing first 500)\n\n`+files.sort().map(f=>`- ${f}`).join('\n')+'\n');
