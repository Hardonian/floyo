const fs=require('fs'); const path=require('path');
const edges=[['frontend/app','frontend/lib'],['frontend/app','frontend/components'],['frontend/app','supabase'],['frontend/components','frontend/lib'],['app','lib'],['app','components'],['app','supabase'],['components','lib']];
const m=['graph TD'];
edges.forEach(([a,b])=>{if(fs.existsSync(a)&&fs.existsSync(b)) m.push(`${a}-->${b}`);});
fs.writeFileSync('docs/architecture/01_dependency_graph.mmd',m.join('\n'));
