const fs = require('node:fs/promises');
const path = require('node:path');
const {spawn} = require('node:child_process');
const os = require('node:os');
const root = path.join(process.env.APPDATA || os.homedir(), 'fox-code-meow');
let queue = Promise.resolve();
function publish(status) {
  queue = queue.then(async () => {
    await fs.mkdir(root,{recursive:true});
    const target=path.join(root,'learning.json');
    await fs.writeFile(target+'.tmp',JSON.stringify({status:String(status).slice(0,500),at:Date.now()}));
    await fs.rename(target+'.tmp',target);
  }).catch(()=>{});
  return queue;
}
async function launch(extensionPath) {
  const executable=path.join(extensionPath,'desktop','fox-pet.exe');
  try { await fs.access(executable); }
  catch { throw Error('桌面宠物程序尚未打包，请安装完整版本。'); }
  const child=spawn(executable,[],{detached:true,stdio:'ignore',windowsHide:true});
  await new Promise((resolve,reject)=>{child.once('spawn',resolve);child.once('error',reject)});
  child.unref();
}
module.exports={publish,launch};
