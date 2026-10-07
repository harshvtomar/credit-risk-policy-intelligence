const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');

// Minimal DOM harness checks the dashboard's actual shipped JavaScript without network access.
// This is a logic test, not a visual browser rendering test.
function check(root) {
  class Element {
    constructor(tag) { this.tag=tag; this.children=[]; this.style={}; this.listeners={}; this.value=''; this.textContent=''; }
    append(...children) { this.children.push(...children); }
    appendChild(child) { this.children.push(child); return child; }
    replaceChildren(...children) { this.children=children; }
    setAttribute(key,val) { this[key]=val; }
    addEventListener(key,cb) { this.listeners[key]=cb; }
    click() { this.clicked=true; }
  }
  const nodes=new Map(), blobs=[];
  const document={getElementById(id) { if(!nodes.has(id))nodes.set(id,new Element(id)); return nodes.get(id); },createElement:tag=>new Element(tag),createElementNS:(_,tag)=>new Element(tag)};
  document.getElementById('segment').value='All';
  const html=fs.readFileSync(path.join(root,'dashboard/index.html'),'utf8');
  const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
  const context=vm.createContext({document,Blob,URL:{createObjectURL:b=>{blobs.push(b);return 'blob:test';},revokeObjectURL:()=>{}},setTimeout:fn=>fn()});
  vm.runInContext(script,context,{timeout:5000});
  const data=JSON.parse(fs.readFileSync(path.join(root,'outputs/dashboard_data.json')));
  assert.equal(nodes.get('cards').children.length,4);
  assert.equal(nodes.get('tbody').children.length,data.rows.length);
  assert.ok(nodes.get('chart').children.find(e=>e.tag==='polyline').points.length>0);
  const all=nodes.get('cards').children.map(c=>c.children[1].textContent);
  const segments=[...new Set(data.rows.map(r=>r.segment))];
  for (const segment of segments) {
    nodes.get('segment').value=segment; nodes.get('segment').listeners.change();
    assert.equal(nodes.get('tbody').children.length,data.rows.filter(r=>r.segment===segment).length);
    assert.ok(nodes.get('tbody').children.every(row=>row.children[1].textContent===segment));
  }
  assert.notDeepEqual(nodes.get('cards').children.map(c=>c.children[1].textContent),all);
  nodes.get('export').listeners.click();
  assert.equal(blobs.length,1);
  nodes.get('segment').value='All';nodes.get('segment').listeners.change();
  assert.equal(nodes.get('tbody').children.length,data.rows.length);
  assert.deepEqual(nodes.get('cards').children.map(c=>c.children[1].textContent),all);
  return blobs[0].text().then(csv=>{
    assert.equal(csv.split('\n').length,data.rows.filter(r=>r.segment===segments.at(-1)).length+1);
    assert.ok(csv.includes('"month","segment"'));
    return {segments:segments.length,rows:data.rows.length,checks:5};
  });
}

if (require.main===module) {
  const root=process.argv[2] || path.resolve(__dirname,'..');
  check(root).then(result=>console.log(JSON.stringify(result))).catch(error=>{console.error(error);process.exitCode=1;});
}
module.exports=check;
