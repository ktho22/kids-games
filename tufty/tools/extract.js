// Pulls the finished game data (after all the patches and derived stats have
// run) out of the web game, plus its sprites. Usage: node extract.js <outdir>
const fs=require('fs'),vm=require('vm'),path=require('path');
const html=fs.readFileSync(path.join(__dirname,'../../pocket-mini-adventure/index.html'),'utf8');
const src=html.match(/<script>([\s\S]*?)<\/script>/)[1].replace(/^(const|let) /gm,'var ');
const el=()=>({innerHTML:'',style:{},classList:{add(){},remove(){}},value:''});
const ctx={location:{hostname:'x'},console,setTimeout,clearTimeout,setInterval:()=>0,localStorage:{getItem:()=>null,setItem(){},removeItem(){}},document:{getElementById:el,querySelectorAll:()=>[],createElement:el,body:{appendChild(){}},addEventListener(){}},navigator:{},matchMedia:()=>({matches:true}),fetch:async()=>{throw 1}};
ctx.window=ctx;vm.createContext(ctx);vm.runInContext(src,ctx);
const g=n=>vm.runInContext(n,ctx);
const out={
  SPECIES:g('SPECIES'), MOVES:g('MOVES'), TYPES:g('TYPES'), AREAS:g('AREAS'), CAVES:g('CAVES'),
  LEGEND:g('LEGEND'), LEGENDS:g('LEGENDS'), MEGA:g('MEGA'), PLAZA:g('PLAZA'), EVOLVED:[...g('EVOLVED')],
  MEWTWO_LV:g('MEWTWO_LV'), LEGEND_RATE:g('LEGEND_RATE'), BOX_MAX:g('BOX_MAX'), GAUGE_MAX:g('GAUGE_MAX'),
};
fs.mkdirSync(process.argv[2]+'/raw',{recursive:true});
fs.writeFileSync(process.argv[2]+'/data.json', JSON.stringify(out));
for(const [k,v] of Object.entries(g('SPRITES'))) fs.writeFileSync(process.argv[2]+'/raw/'+k+'.png', Buffer.from(v.split(',')[1],'base64'));
console.log('ok', Object.keys(out.SPECIES).length);
